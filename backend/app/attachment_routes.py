from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .attachments import (
    assert_allowed_image_type,
    new_attachment_id,
    serialize_attachment,
)
from .database import get_db
from .models import Attachment, Experiment, ExperimentStepRun, ExperimentWorkflowRun, Workflow, WorkflowStep
from .schemas import AttachmentRead
from .storage import get_storage_backend
from .sync import record_local_change


router = APIRouter(tags=["attachments"])


def _get_workflow(db: Session, workflow_id: str) -> Workflow:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


def _get_workflow_step(db: Session, workflow_id: str, step_id: str) -> WorkflowStep:
    step = db.get(WorkflowStep, step_id)
    if step is None or step.workflow_id != workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow step not found")
    return step


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


def _get_experiment_step_run(db: Session, workflow_run_id: str, step_run_id: str) -> ExperimentStepRun:
    step_run = db.get(ExperimentStepRun, step_run_id)
    if step_run is None or step_run.experiment_workflow_run_id != workflow_run_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment step run not found")
    return step_run


def _list_attachments(db: Session, owner_type: str, owner_id: str) -> list[AttachmentRead]:
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.owner_type == owner_type, Attachment.owner_id == owner_id)
        .order_by(Attachment.created_at)
    ).all()
    return [serialize_attachment(attachment) for attachment in attachments]


def _store_attachment(db: Session, owner_type: str, owner_id: str, upload: UploadFile) -> AttachmentRead:
    content_type = assert_allowed_image_type(upload.content_type)
    attachment_id = new_attachment_id()
    stored_ref = get_storage_backend().save_attachment(
        owner_type=owner_type,
        owner_id=owner_id,
        attachment_id=attachment_id,
        filename=upload.filename,
        content_type=content_type,
        fileobj=upload.file,
    )

    attachment = Attachment(
        id=attachment_id,
        owner_type=owner_type,
        owner_id=owner_id,
        filename=upload.filename or attachment_id,
        content_type=content_type,
        storage_backend=stored_ref.storage_backend,
        local_path=stored_ref.local_path,
        remote_url=stored_ref.remote_url,
    )
    db.add(attachment)
    record_local_change(db, f"attachment.upload:{owner_type}")
    db.commit()
    db.refresh(attachment)
    return serialize_attachment(attachment)


def _get_attachment(db: Session, attachment_id: str) -> Attachment:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return attachment


def _delete_attachment(db: Session, attachment_id: str) -> Response:
    attachment = _get_attachment(db, attachment_id)
    db.delete(attachment)
    record_local_change(db, f"attachment.delete:{attachment.owner_type}")
    db.commit()
    get_storage_backend().delete_attachment(attachment)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/workflows/{workflow_id}/steps/{step_id}/attachments", response_model=list[AttachmentRead])
def list_workflow_step_attachments(workflow_id: str, step_id: str, db: Session = Depends(get_db)) -> list[AttachmentRead]:
    _get_workflow(db, workflow_id)
    _get_workflow_step(db, workflow_id, step_id)
    return _list_attachments(db, "workflow_step", step_id)


@router.post("/api/v1/workflows/{workflow_id}/steps/{step_id}/attachments", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
def upload_workflow_step_attachment(
    workflow_id: str,
    step_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AttachmentRead:
    _get_workflow(db, workflow_id)
    _get_workflow_step(db, workflow_id, step_id)
    return _store_attachment(db, "workflow_step", step_id, file)


@router.get(
    "/api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}/attachments",
    response_model=list[AttachmentRead],
)
def list_experiment_step_run_attachments(
    experiment_id: str,
    workflow_run_id: str,
    step_run_id: str,
    db: Session = Depends(get_db),
) -> list[AttachmentRead]:
    _get_experiment(db, experiment_id)
    _get_experiment_workflow_run(db, experiment_id, workflow_run_id)
    _get_experiment_step_run(db, workflow_run_id, step_run_id)
    return _list_attachments(db, "experiment_step_run", step_run_id)


@router.post(
    "/api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_experiment_step_run_attachment(
    experiment_id: str,
    workflow_run_id: str,
    step_run_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AttachmentRead:
    _get_experiment(db, experiment_id)
    _get_experiment_workflow_run(db, experiment_id, workflow_run_id)
    _get_experiment_step_run(db, workflow_run_id, step_run_id)
    return _store_attachment(db, "experiment_step_run", step_run_id, file)


@router.get("/api/v1/attachments/{attachment_id}/content")
def read_attachment_content(attachment_id: str, db: Session = Depends(get_db)) -> FileResponse:
    attachment = _get_attachment(db, attachment_id)
    local_path = get_storage_backend().resolve_local_path(attachment)
    if local_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file is unavailable")
    return FileResponse(
        local_path,
        media_type=attachment.content_type,
        filename=attachment.filename,
    )


@router.delete("/api/v1/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(attachment_id: str, db: Session = Depends(get_db)) -> Response:
    return _delete_attachment(db, attachment_id)
