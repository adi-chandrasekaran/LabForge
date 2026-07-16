from __future__ import annotations

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .attachments import serialize_attachment
from .database import get_db
from .deps import get_or_create_mock_user
from .models import Attachment, Workflow, WorkflowBranch, WorkflowStep
from .schemas import (
    WorkflowBranchCreate,
    WorkflowBranchRead,
    WorkflowBranchStepCreate,
    WorkflowBranchStepRead,
    WorkflowBranchUpdate,
    WorkflowCreate,
    WorkflowRead,
    WorkflowStepCreate,
    WorkflowStepRead,
    WorkflowStepReorderRequest,
    WorkflowStepUpdate,
    WorkflowUpdate,
)
from .sync import record_local_change


router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])
PUBLISHER_ROLES = {"professor", "post_doc", "phd"}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def _serialize_branch(
    branch: WorkflowBranch,
    branch_steps: list[WorkflowStep],
    attachments_by_owner_id: dict[str, list[Attachment]],
) -> WorkflowBranchRead:
    return WorkflowBranchRead(
        id=branch.id,
        workflow_id=branch.workflow_id,
        anchor_step_id=branch.anchor_step_id,
        label=branch.label,
        steps=[
            WorkflowBranchStepRead(
                id=step.id,
                workflow_id=step.workflow_id,
                workflow_branch_id=step.workflow_branch_id,
                parent_step_id=step.parent_step_id,
                branch_track_id=step.branch_track_id,
                order_index=step.order_index,
                attachments=[serialize_attachment(attachment) for attachment in attachments_by_owner_id.get(step.id, [])],
                label=step.label,
                sublabel=step.sublabel,
                status_template=step.status_template,
                duration=step.duration,
                procedure_markdown=step.procedure_markdown,
                inputs=step.inputs,
                parameters=step.parameters,
                outputs=step.outputs,
                notes=step.notes,
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            for step in sorted(branch_steps, key=lambda item: item.order_index)
        ],
        created_at=branch.created_at,
        updated_at=branch.updated_at,
    )


def _serialize_workflow(db: Session, workflow: Workflow) -> WorkflowRead:
    steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow.id)
        .order_by(WorkflowStep.order_index, WorkflowStep.created_at)
    ).all()
    branches = db.scalars(
        select(WorkflowBranch)
        .where(WorkflowBranch.workflow_id == workflow.id)
        .order_by(WorkflowBranch.created_at)
    ).all()
    attachments = db.scalars(
        select(Attachment).where(
            Attachment.owner_type == "workflow_step",
            Attachment.owner_id.in_([step.id for step in steps]),
        )
    ).all()
    attachments_by_owner_id: dict[str, list[Attachment]] = {}
    for attachment in attachments:
        attachments_by_owner_id.setdefault(attachment.owner_id, []).append(attachment)

    branch_steps_by_branch_id: dict[str, list[WorkflowStep]] = {}
    main_steps: list[WorkflowStep] = []
    for step in steps:
        if step.workflow_branch_id:
            branch_steps_by_branch_id.setdefault(step.workflow_branch_id, []).append(step)
        else:
            main_steps.append(step)

    branches_by_anchor: dict[str, list[WorkflowBranchRead]] = {}
    for branch in branches:
        branches_by_anchor.setdefault(branch.anchor_step_id, []).append(
            _serialize_branch(
                branch,
                branch_steps_by_branch_id.get(branch.id, []),
                attachments_by_owner_id,
            )
        )

    return WorkflowRead(
        id=workflow.id,
        title=workflow.title,
        description=workflow.description,
        owner_id=workflow.owner_id,
        visibility=workflow.visibility,
        library_state=workflow.library_state,
        version=workflow.version,
        tags=workflow.tags,
        steps=[
            WorkflowStepRead(
                id=step.id,
                workflow_id=step.workflow_id,
                workflow_branch_id=step.workflow_branch_id,
                parent_step_id=step.parent_step_id,
                branch_track_id=step.branch_track_id,
                order_index=step.order_index,
                attachments=[serialize_attachment(attachment) for attachment in attachments_by_owner_id.get(step.id, [])],
                label=step.label,
                sublabel=step.sublabel,
                status_template=step.status_template,
                duration=step.duration,
                procedure_markdown=step.procedure_markdown,
                inputs=step.inputs,
                parameters=step.parameters,
                outputs=step.outputs,
                notes=step.notes,
                branch_tracks=branches_by_anchor.get(step.id, []),
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            for step in sorted(main_steps, key=lambda item: item.order_index)
        ],
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def _get_workflow(db: Session, workflow_id: str) -> Workflow:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


def _get_step(db: Session, workflow_id: str, step_id: str) -> WorkflowStep:
    step = db.get(WorkflowStep, step_id)
    if step is None or step.workflow_id != workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow step not found")
    return step


def _get_branch(db: Session, workflow_id: str, branch_id: str) -> WorkflowBranch:
    branch = db.get(WorkflowBranch, branch_id)
    if branch is None or branch.workflow_id != workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow branch not found")
    return branch


def _reindex(steps: list[WorkflowStep]) -> None:
    for index, step in enumerate(steps, start=1):
        step.order_index = index


@router.get("", response_model=list[WorkflowRead])
def list_workflows(tag: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> list[WorkflowRead]:
    query = select(Workflow).order_by(Workflow.title)
    workflows = db.scalars(query).all()
    if tag is not None:
        workflows = [workflow for workflow in workflows if tag in workflow.tags]
    return [_serialize_workflow(db, workflow) for workflow in workflows]


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    user = get_or_create_mock_user(db)
    workflow = Workflow(
        id=_new_id("workflow"),
        title=payload.title,
        description=payload.description,
        owner_id=user.id,
        visibility=payload.visibility,
        library_state=payload.library_state,
        version=payload.version,
        tags=payload.tags,
    )
    db.add(workflow)
    record_local_change(db, "workflow.create")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.get("/{workflow_id}", response_model=WorkflowRead)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    return _serialize_workflow(db, workflow)


@router.patch("/{workflow_id}", response_model=WorkflowRead)
def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)
    record_local_change(db, "workflow.update")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)) -> Response:
    workflow = _get_workflow(db, workflow_id)
    db.delete(workflow)
    record_local_change(db, "workflow.delete")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{workflow_id}/publish", response_model=WorkflowRead)
def publish_workflow(workflow_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    user = get_or_create_mock_user(db)
    if user.role not in PUBLISHER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current role cannot publish workflows")

    workflow = _get_workflow(db, workflow_id)
    workflow.library_state = "published"
    workflow.visibility = "library"
    record_local_change(db, "workflow.publish")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.post("/{workflow_id}/steps", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow_step(workflow_id: str, payload: WorkflowStepCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    main_steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow_id, WorkflowStep.workflow_branch_id.is_(None))
        .order_by(WorkflowStep.order_index)
    ).all()

    insert_index = len(main_steps) + 1
    if payload.after_step_id is not None:
        after_step = _get_step(db, workflow_id, payload.after_step_id)
        if after_step.workflow_branch_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use the branch step route for branch inserts")
        insert_index = after_step.order_index + 1

    for step in main_steps:
        if step.order_index >= insert_index:
            step.order_index += 1

    step = WorkflowStep(
        id=_new_id("step"),
        workflow_id=workflow_id,
        order_index=insert_index,
        label=payload.label,
        sublabel=payload.sublabel,
        status_template=payload.status_template,
        duration=payload.duration,
        procedure_markdown=payload.procedure_markdown,
        inputs=[item.model_dump(exclude_none=True) for item in payload.inputs],
        parameters=[item.model_dump(exclude_none=True) for item in payload.parameters],
        outputs=[item.model_dump(exclude_none=True) for item in payload.outputs],
        notes=payload.notes,
    )
    db.add(step)
    record_local_change(db, "workflow.step.create")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.patch("/{workflow_id}/steps/{step_id}", response_model=WorkflowRead)
def update_workflow_step(
    workflow_id: str,
    step_id: str,
    payload: WorkflowStepUpdate,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    step = _get_step(db, workflow_id, step_id)
    step.label = payload.label
    step.sublabel = payload.sublabel
    step.status_template = payload.status_template
    step.duration = payload.duration
    step.procedure_markdown = payload.procedure_markdown
    step.inputs = [item.model_dump(exclude_none=True) for item in payload.inputs]
    step.parameters = [item.model_dump(exclude_none=True) for item in payload.parameters]
    step.outputs = [item.model_dump(exclude_none=True) for item in payload.outputs]
    step.notes = payload.notes
    record_local_change(db, "workflow.step.update")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.delete("/{workflow_id}/steps/{step_id}", response_model=WorkflowRead)
def delete_workflow_step(workflow_id: str, step_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    step = _get_step(db, workflow_id, step_id)

    if step.workflow_branch_id is None:
        branches = db.scalars(select(WorkflowBranch).where(WorkflowBranch.anchor_step_id == step.id)).all()
        for branch in branches:
            db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_branch_id == branch.id))
            db.delete(branch)
        main_steps = db.scalars(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id, WorkflowStep.workflow_branch_id.is_(None))
            .order_by(WorkflowStep.order_index)
        ).all()
        db.delete(step)
        remaining = [item for item in main_steps if item.id != step.id]
        _reindex(remaining)
    else:
        branch_steps = db.scalars(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_branch_id == step.workflow_branch_id)
            .order_by(WorkflowStep.order_index)
        ).all()
        db.delete(step)
        remaining = [item for item in branch_steps if item.id != step.id]
        _reindex(remaining)

    record_local_change(db, "workflow.step.delete")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.post("/{workflow_id}/steps/reorder", response_model=WorkflowRead)
def reorder_workflow_steps(
    workflow_id: str,
    payload: WorkflowStepReorderRequest,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    query = select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
    if payload.branch_id is None:
        query = query.where(WorkflowStep.workflow_branch_id.is_(None))
    else:
        _get_branch(db, workflow_id, payload.branch_id)
        query = query.where(WorkflowStep.workflow_branch_id == payload.branch_id)

    steps = db.scalars(query.order_by(WorkflowStep.order_index)).all()
    step_map = {step.id: step for step in steps}
    if set(step_map.keys()) != set(payload.ordered_step_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ordered step ids must match the target step set")

    for index, step_id in enumerate(payload.ordered_step_ids, start=1):
        step_map[step_id].order_index = index

    record_local_change(db, "workflow.step.reorder")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.post("/{workflow_id}/branches", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow_branch(workflow_id: str, payload: WorkflowBranchCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    anchor_step = _get_step(db, workflow_id, payload.anchor_step_id)
    if anchor_step.workflow_branch_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch anchors must be main workflow steps")

    branch = WorkflowBranch(
        id=_new_id("branch"),
        workflow_id=workflow_id,
        anchor_step_id=payload.anchor_step_id,
        label=payload.label,
    )
    db.add(branch)
    record_local_change(db, "workflow.branch.create")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.patch("/{workflow_id}/branches/{branch_id}", response_model=WorkflowRead)
def update_workflow_branch(
    workflow_id: str,
    branch_id: str,
    payload: WorkflowBranchUpdate,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    branch = _get_branch(db, workflow_id, branch_id)
    branch.label = payload.label
    record_local_change(db, "workflow.branch.update")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.delete("/{workflow_id}/branches/{branch_id}", response_model=WorkflowRead)
def delete_workflow_branch(workflow_id: str, branch_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    branch = _get_branch(db, workflow_id, branch_id)
    db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_branch_id == branch.id))
    db.delete(branch)
    record_local_change(db, "workflow.branch.delete")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.post("/{workflow_id}/branches/{branch_id}/steps", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_branch_step(
    workflow_id: str,
    branch_id: str,
    payload: WorkflowBranchStepCreate,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    branch = _get_branch(db, workflow_id, branch_id)
    branch_steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_branch_id == branch.id)
        .order_by(WorkflowStep.order_index)
    ).all()

    step = WorkflowStep(
        id=_new_id("branch-step"),
        workflow_id=workflow_id,
        workflow_branch_id=branch.id,
        order_index=len(branch_steps) + 1,
        label=payload.label,
        sublabel=payload.sublabel,
        status_template=payload.status_template,
        duration=payload.duration,
        procedure_markdown=payload.procedure_markdown,
        inputs=[item.model_dump(exclude_none=True) for item in payload.inputs],
        parameters=[item.model_dump(exclude_none=True) for item in payload.parameters],
        outputs=[item.model_dump(exclude_none=True) for item in payload.outputs],
        notes=payload.notes,
    )
    db.add(step)
    record_local_change(db, "workflow.branch.step.create")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)
