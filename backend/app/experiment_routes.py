from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .attachments import serialize_attachment
from .database import get_db
from .deps import get_or_create_mock_user
from .models import Attachment, Experiment, ExperimentStepRun, ExperimentWorkflowRun, Workflow, WorkflowStep
from .schemas import (
    ExperimentCreate,
    ExperimentInstantiateRequest,
    ExperimentRead,
    ExperimentStepRunRead,
    ExperimentStepRunUpdate,
    ExperimentUpdate,
    ExperimentWorkflowRunRead,
)
from .sync import record_local_change


router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def _derive_status(step_statuses: list[str]) -> str:
    if not step_statuses:
        return "planned"
    if any(status_value == "error" for status_value in step_statuses):
        return "error"
    if all(status_value == "complete" for status_value in step_statuses):
        return "complete"
    if any(status_value == "running" for status_value in step_statuses):
        return "running"
    return "planned"


def _serialize_experiment(db: Session, experiment: Experiment) -> ExperimentRead:
    workflow_runs = db.scalars(
        select(ExperimentWorkflowRun)
        .where(ExperimentWorkflowRun.experiment_id == experiment.id)
        .order_by(ExperimentWorkflowRun.order_index, ExperimentWorkflowRun.created_at)
    ).all()
    step_runs = db.scalars(
        select(ExperimentStepRun)
        .join(ExperimentWorkflowRun, ExperimentStepRun.experiment_workflow_run_id == ExperimentWorkflowRun.id)
        .where(ExperimentWorkflowRun.experiment_id == experiment.id)
        .order_by(ExperimentWorkflowRun.order_index, ExperimentStepRun.order_index, ExperimentStepRun.created_at)
    ).all()
    attachments = db.scalars(
        select(Attachment).where(
            Attachment.owner_type == "experiment_step_run",
            Attachment.owner_id.in_([step_run.id for step_run in step_runs]),
        )
    ).all()

    step_runs_by_workflow_run_id: dict[str, list[ExperimentStepRun]] = {}
    for step_run in step_runs:
        step_runs_by_workflow_run_id.setdefault(step_run.experiment_workflow_run_id, []).append(step_run)
    attachments_by_owner_id: dict[str, list[Attachment]] = {}
    for attachment in attachments:
        attachments_by_owner_id.setdefault(attachment.owner_id, []).append(attachment)

    return ExperimentRead(
        id=experiment.id,
        project_id=experiment.project_id,
        title=experiment.title,
        experiment_date=experiment.experiment_date,
        operator_id=experiment.operator_id,
        status=experiment.status,
        notes=experiment.notes,
        workflow_runs=[
            ExperimentWorkflowRunRead(
                id=workflow_run.id,
                experiment_id=workflow_run.experiment_id,
                source_workflow_id=workflow_run.source_workflow_id,
                workflow_title=workflow_run.workflow_title,
                workflow_description=workflow_run.workflow_description,
                workflow_version=workflow_run.workflow_version,
                order_index=workflow_run.order_index,
                status=workflow_run.status,
                step_runs=[
                    ExperimentStepRunRead(
                        id=step_run.id,
                        experiment_workflow_run_id=step_run.experiment_workflow_run_id,
                        source_workflow_step_id=step_run.source_workflow_step_id,
                        order_index=step_run.order_index,
                        label=step_run.label,
                        sublabel=step_run.sublabel,
                        status=step_run.status,
                        duration=step_run.duration,
                        attachments=[serialize_attachment(attachment) for attachment in attachments_by_owner_id.get(step_run.id, [])],
                        procedure_markdown=step_run.procedure_markdown,
                        inputs=step_run.inputs,
                        parameters=step_run.parameters,
                        outputs=step_run.outputs,
                        notes=step_run.notes,
                        created_at=step_run.created_at,
                        updated_at=step_run.updated_at,
                    )
                    for step_run in step_runs_by_workflow_run_id.get(workflow_run.id, [])
                ],
                created_at=workflow_run.created_at,
                updated_at=workflow_run.updated_at,
            )
            for workflow_run in workflow_runs
        ],
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
    )


def _get_experiment(db: Session, experiment_id: str) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


def _get_experiment_workflow_run(db: Session, experiment_id: str, workflow_run_id: str) -> ExperimentWorkflowRun:
    workflow_run = db.get(ExperimentWorkflowRun, workflow_run_id)
    if workflow_run is None or workflow_run.experiment_id != experiment_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment workflow run not found")
    return workflow_run


def _get_experiment_step_run(
    db: Session,
    workflow_run_id: str,
    step_run_id: str,
) -> ExperimentStepRun:
    step_run = db.get(ExperimentStepRun, step_run_id)
    if step_run is None or step_run.experiment_workflow_run_id != workflow_run_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment step run not found")
    return step_run


def _refresh_run_statuses(db: Session, experiment: Experiment) -> None:
    workflow_runs = db.scalars(
        select(ExperimentWorkflowRun).where(ExperimentWorkflowRun.experiment_id == experiment.id)
    ).all()
    workflow_statuses: list[str] = []
    for workflow_run in workflow_runs:
        step_statuses = db.scalars(
            select(ExperimentStepRun.status).where(ExperimentStepRun.experiment_workflow_run_id == workflow_run.id)
        ).all()
        workflow_run.status = _derive_status(step_statuses)
        workflow_statuses.append(workflow_run.status)
    experiment.status = _derive_status(workflow_statuses)


@router.get("", response_model=list[ExperimentRead])
def list_experiments(
    project_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ExperimentRead]:
    query = select(Experiment).order_by(Experiment.experiment_date.desc(), Experiment.created_at.desc())
    if project_id is not None:
        query = query.where(Experiment.project_id == project_id)
    experiments = db.scalars(query).all()
    return [_serialize_experiment(db, experiment) for experiment in experiments]


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)) -> ExperimentRead:
    user = get_or_create_mock_user(db)
    experiment = Experiment(
        id=_new_id("experiment"),
        project_id=payload.project_id,
        title=payload.title,
        experiment_date=payload.experiment_date,
        operator_id=user.id,
        status="planned",
        notes=payload.notes,
    )
    db.add(experiment)
    record_local_change(db, "experiment.create")
    db.commit()
    db.refresh(experiment)
    return _serialize_experiment(db, experiment)


@router.post("/instantiate", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def instantiate_experiment(payload: ExperimentInstantiateRequest, db: Session = Depends(get_db)) -> ExperimentRead:
    user = get_or_create_mock_user(db)
    if not payload.workflow_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one workflow id is required")

    workflows = db.scalars(
        select(Workflow).where(Workflow.id.in_(payload.workflow_ids)).order_by(Workflow.title)
    ).all()
    found_ids = {workflow.id for workflow in workflows}
    if set(payload.workflow_ids) != found_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more workflow ids are invalid")

    workflow_order = {workflow_id: index for index, workflow_id in enumerate(payload.workflow_ids, start=1)}
    workflows = sorted(workflows, key=lambda workflow: workflow_order[workflow.id])

    experiment = Experiment(
        id=_new_id("experiment"),
        project_id=payload.project_id,
        title=payload.title,
        experiment_date=payload.experiment_date,
        operator_id=user.id,
        status="planned",
        notes=payload.notes,
    )
    db.add(experiment)
    db.flush()

    for workflow_index, workflow in enumerate(workflows, start=1):
        workflow_run = ExperimentWorkflowRun(
            id=_new_id("workflow-run"),
            experiment_id=experiment.id,
            source_workflow_id=workflow.id,
            workflow_title=workflow.title,
            workflow_description=workflow.description,
            workflow_version=workflow.version,
            order_index=workflow_index,
            status="planned",
        )
        db.add(workflow_run)
        db.flush()

        steps = db.scalars(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow.id, WorkflowStep.workflow_branch_id.is_(None))
            .order_by(WorkflowStep.order_index, WorkflowStep.created_at)
        ).all()
        for step in steps:
            db.add(
                ExperimentStepRun(
                    id=_new_id("step-run"),
                    experiment_workflow_run_id=workflow_run.id,
                    source_workflow_step_id=step.id,
                    order_index=step.order_index,
                    label=step.label,
                    sublabel=step.sublabel,
                    status=step.status_template,
                    duration=step.duration,
                    procedure_markdown=step.procedure_markdown,
                    inputs=step.inputs,
                    parameters=step.parameters,
                    outputs=step.outputs,
                    notes=step.notes,
                )
            )

    _refresh_run_statuses(db, experiment)
    record_local_change(db, "experiment.instantiate")
    db.commit()
    db.refresh(experiment)
    return _serialize_experiment(db, experiment)


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)) -> ExperimentRead:
    experiment = _get_experiment(db, experiment_id)
    return _serialize_experiment(db, experiment)


@router.patch("/{experiment_id}", response_model=ExperimentRead)
def update_experiment(experiment_id: str, payload: ExperimentUpdate, db: Session = Depends(get_db)) -> ExperimentRead:
    experiment = _get_experiment(db, experiment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(experiment, field, value)
    record_local_change(db, "experiment.update")
    db.commit()
    db.refresh(experiment)
    return _serialize_experiment(db, experiment)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_experiment(experiment_id: str, db: Session = Depends(get_db)) -> Response:
    experiment = _get_experiment(db, experiment_id)
    db.delete(experiment)
    record_local_change(db, "experiment.delete")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}", response_model=ExperimentRead)
def update_experiment_step_run(
    experiment_id: str,
    workflow_run_id: str,
    step_run_id: str,
    payload: ExperimentStepRunUpdate,
    db: Session = Depends(get_db),
) -> ExperimentRead:
    experiment = _get_experiment(db, experiment_id)
    _get_experiment_workflow_run(db, experiment_id, workflow_run_id)
    step_run = _get_experiment_step_run(db, workflow_run_id, step_run_id)
    step_run.label = payload.label
    step_run.sublabel = payload.sublabel
    step_run.status = payload.status
    step_run.duration = payload.duration
    step_run.procedure_markdown = payload.procedure_markdown
    step_run.inputs = [item.model_dump(exclude_none=True) for item in payload.inputs]
    step_run.parameters = [item.model_dump(exclude_none=True) for item in payload.parameters]
    step_run.outputs = [item.model_dump(exclude_none=True) for item in payload.outputs]
    step_run.notes = payload.notes

    _refresh_run_statuses(db, experiment)
    record_local_change(db, "experiment.step_run.update")
    db.commit()
    db.refresh(experiment)
    return _serialize_experiment(db, experiment)
