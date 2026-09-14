from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ChatChannel, ChatMessage, Experiment, Project, User, Workflow
from ..sync import record_local_change


def list_projects(db: Session) -> list[Project]:
    return db.scalars(select(Project).order_by(Project.updated_at.desc(), Project.created_at.desc())).all()


def get_project(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def list_workflows(
    db: Session,
    *,
    tag: Optional[str] = None,
    library_state: Optional[str] = None,
    visibility: Optional[str] = None,
    project_id: Optional[str] = None,
) -> list[Workflow]:
    workflows = db.scalars(select(Workflow).order_by(Workflow.title)).all()
    if tag is not None:
        workflows = [workflow for workflow in workflows if tag in workflow.tags]
    if library_state is not None:
        workflows = [workflow for workflow in workflows if workflow.library_state == library_state]
    if visibility is not None:
        workflows = [workflow for workflow in workflows if workflow.visibility == visibility]
    if project_id is not None:
        workflows = [workflow for workflow in workflows if workflow.project_id == project_id]
    return workflows


def get_workflow(db: Session, workflow_id: str) -> Workflow:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


def list_experiments(db: Session, project_id: Optional[str] = None) -> list[Experiment]:
    query = select(Experiment).order_by(Experiment.experiment_date.desc(), Experiment.created_at.desc())
    if project_id is not None:
        query = query.where(Experiment.project_id == project_id)
    return db.scalars(query).all()


def get_experiment(db: Session, experiment_id: str) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment


def list_channels(db: Session, current_user: User) -> list[ChatChannel]:
    return db.scalars(
        select(ChatChannel)
        .where(ChatChannel.lab_id == current_user.lab_id)
        .order_by(ChatChannel.name, ChatChannel.created_at)
    ).all()


def get_channel_for_user(db: Session, current_user: User, channel_id: str) -> ChatChannel:
    channel = db.get(ChatChannel, channel_id)
    if channel is None or channel.lab_id != current_user.lab_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


def list_channel_messages(db: Session, current_user: User, channel_id: str, limit: int) -> list[ChatMessage]:
    get_channel_for_user(db, current_user, channel_id)
    return db.scalars(
        select(ChatMessage)
        .where(ChatMessage.channel_id == channel_id, ChatMessage.lab_id == current_user.lab_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    ).all()


def validate_message_references(
    db: Session,
    referenced_workflow_id: Optional[str],
    referenced_experiment_id: Optional[str],
) -> None:
    if referenced_workflow_id and db.get(Workflow, referenced_workflow_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced workflow does not exist")
    if referenced_experiment_id and db.get(Experiment, referenced_experiment_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced experiment does not exist")


def create_channel_message(
    db: Session,
    current_user: User,
    *,
    channel_id: str,
    body: str,
    referenced_workflow_id: Optional[str] = None,
    referenced_experiment_id: Optional[str] = None,
) -> ChatMessage:
    channel = get_channel_for_user(db, current_user, channel_id)
    validate_message_references(db, referenced_workflow_id, referenced_experiment_id)
    message = ChatMessage(
        id=f"message-{uuid4().hex[:10]}",
        channel_id=channel.id,
        lab_id=current_user.lab_id,
        author_id=current_user.id,
        body=body,
        referenced_workflow_id=referenced_workflow_id,
        referenced_experiment_id=referenced_experiment_id,
    )
    db.add(message)
    record_local_change(db, "chat.message.create")
    db.commit()
    db.refresh(message)
    return message
