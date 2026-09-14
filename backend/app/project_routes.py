from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .deps import get_current_user, get_or_create_mock_user
from .models import (
    Attachment,
    Experiment,
    ExperimentStepRun,
    ExperimentWorkflowRun,
    Project,
    ProjectMember,
    User,
    Workflow,
    WorkflowBranch,
    WorkflowMember,
    WorkflowStep,
)
from .schemas import ProjectCreate, ProjectMemberRead, ProjectRead, ProjectUpdate
from .sync import record_local_change
from .services import lookup as lookup_service


router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _new_project_id() -> str:
    return f"project-{uuid4().hex[:10]}"


def _new_project_member_id() -> str:
    return f"project-member-{uuid4().hex[:10]}"


def _new_workflow_id() -> str:
    return f"workflow-{uuid4().hex[:10]}"


def _new_workflow_member_id() -> str:
    return f"workflow-member-{uuid4().hex[:10]}"


def _is_local_demo_mode() -> bool:
    settings = get_settings()
    return settings.app_mode == "local" or settings.auth_backend == "mock"


def _serialize_project_members(db: Session, project_id: str) -> list[ProjectMemberRead]:
    members = db.scalars(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at, ProjectMember.id)
    ).all()
    users = {member.user_id: db.get(User, member.user_id) for member in members}
    serialized = [
        ProjectMemberRead(
            user_id=member.user_id,
            display_name=users[member.user_id].display_name if users.get(member.user_id) else member.user_id,
            email=users[member.user_id].email if users.get(member.user_id) else "",
            lab_role=users[member.user_id].role if users.get(member.user_id) else "unknown",
            project_role=member.role,
        )
        for member in members
    ]
    return sorted(serialized, key=lambda member: (0 if member.project_role == "owner" else 1, member.display_name.lower()))


def serialize_project(db: Session, project: Project) -> ProjectRead:
    owner = db.get(User, project.owner_id) if project.owner_id else None
    experiments = db.scalars(
        select(Experiment)
        .where(Experiment.project_id == project.id)
        .order_by(Experiment.experiment_date.desc(), Experiment.created_at.desc())
    ).all()
    experiment_ids = [experiment.id for experiment in experiments]

    workflow_runs = (
        db.scalars(
            select(ExperimentWorkflowRun).where(ExperimentWorkflowRun.experiment_id.in_(experiment_ids))
        ).all()
        if experiment_ids
        else []
    )
    workflow_run_ids = [workflow_run.id for workflow_run in workflow_runs]
    step_runs = (
        db.scalars(
            select(ExperimentStepRun).where(ExperimentStepRun.experiment_workflow_run_id.in_(workflow_run_ids))
        ).all()
        if workflow_run_ids
        else []
    )

    complete_step_count = sum(1 for step_run in step_runs if step_run.status == "complete")
    progress_percent = round((complete_step_count / len(step_runs)) * 100) if step_runs else 0

    return ProjectRead(
        id=project.id,
        title=project.title,
        code=project.code,
        description=project.description,
        owner_id=project.owner_id,
        status=project.status,
        tags=project.tags,
        owner_display_name=owner.display_name if owner else None,
        experiment_count=len(experiments),
        workflow_count=len({workflow_run.source_workflow_id for workflow_run in workflow_runs}),
        progress_percent=progress_percent,
        members=_serialize_project_members(db, project.id),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _get_project(db: Session, project_id: str) -> Project:
    return lookup_service.get_project(db, project_id)


def _upsert_project_owner_membership(db: Session, project: Project) -> None:
    if not project.owner_id:
        return

    owner_membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == project.owner_id,
        )
    )
    if owner_membership is None:
        db.add(
            ProjectMember(
                id=_new_project_member_id(),
                project_id=project.id,
                user_id=project.owner_id,
                role="owner",
            )
        )
    else:
        owner_membership.role = "owner"


def _replace_project_members(db: Session, project: Project, members: list[dict[str, str]]) -> None:
    member_map = {
        member["user_id"]: member["role"]
        for member in members
        if member["user_id"] and member["role"]
    }
    if project.owner_id:
        member_map[project.owner_id] = "owner"

    existing = db.scalars(select(ProjectMember).where(ProjectMember.project_id == project.id)).all()
    existing_by_user_id = {member.user_id: member for member in existing}

    for user_id, role in member_map.items():
        if db.get(User, user_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lab user {user_id} does not exist")
        if user_id in existing_by_user_id:
            existing_by_user_id[user_id].role = role
        else:
            db.add(
                ProjectMember(
                    id=_new_project_member_id(),
                    project_id=project.id,
                    user_id=user_id,
                    role=role,
                )
            )

    for member in existing:
        if member.user_id not in member_map:
            db.delete(member)


def _create_blank_experimental_workflow(db: Session, project: Project, user: User) -> Workflow:
    workflow = Workflow(
        id=_new_workflow_id(),
        title=f"{project.title} Experimental Workflow",
        description=f"Editable experimental workflow for {project.title}.",
        owner_id=user.id,
        project_id=project.id,
        visibility="private",
        library_state="draft",
        version=1,
        tags=list(dict.fromkeys(["experimental", *project.tags])),
    )
    db.add(workflow)
    db.flush()
    db.add(
        WorkflowMember(
            id=_new_workflow_member_id(),
            workflow_id=workflow.id,
            user_id=user.id,
            role="owner",
        )
    )
    return workflow


def _delete_project_cascade(db: Session, project: Project) -> None:
    workflows = db.scalars(select(Workflow).where(Workflow.project_id == project.id)).all()
    for workflow in workflows:
        step_ids = db.scalars(select(WorkflowStep.id).where(WorkflowStep.workflow_id == workflow.id)).all()
        if step_ids:
            db.execute(delete(Attachment).where(Attachment.owner_type == "workflow_step", Attachment.owner_id.in_(step_ids)))
        db.execute(delete(WorkflowMember).where(WorkflowMember.workflow_id == workflow.id))
        db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id, WorkflowStep.workflow_branch_id.is_not(None)))
        db.execute(delete(WorkflowBranch).where(WorkflowBranch.workflow_id == workflow.id))
        db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id))
        db.delete(workflow)

    experiments = db.scalars(select(Experiment).where(Experiment.project_id == project.id)).all()
    for experiment in experiments:
        workflow_runs = db.scalars(select(ExperimentWorkflowRun).where(ExperimentWorkflowRun.experiment_id == experiment.id)).all()
        workflow_run_ids = [workflow_run.id for workflow_run in workflow_runs]
        if workflow_run_ids:
            step_run_ids = db.scalars(
                select(ExperimentStepRun.id).where(ExperimentStepRun.experiment_workflow_run_id.in_(workflow_run_ids))
            ).all()
            if step_run_ids:
                db.execute(
                    delete(Attachment).where(
                        Attachment.owner_type == "experiment_step_run",
                        Attachment.owner_id.in_(step_run_ids),
                    )
                )
            db.execute(delete(ExperimentStepRun).where(ExperimentStepRun.experiment_workflow_run_id.in_(workflow_run_ids)))
            db.execute(delete(ExperimentWorkflowRun).where(ExperimentWorkflowRun.id.in_(workflow_run_ids)))
        db.delete(experiment)

    db.execute(delete(ProjectMember).where(ProjectMember.project_id == project.id))
    db.delete(project)


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    projects = lookup_service.list_projects(db)
    return [serialize_project(db, project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    existing = db.scalar(select(Project).where(Project.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project code already exists")

    user = get_or_create_mock_user(db)
    project = Project(
        id=_new_project_id(),
        title=payload.title,
        code=payload.code,
        description=payload.description,
        owner_id=user.id,
        status=payload.status,
        tags=payload.tags,
    )
    db.add(project)
    db.flush()
    _upsert_project_owner_membership(db, project)
    _create_blank_experimental_workflow(db, project, user)
    record_local_change(db, "project.create")
    db.commit()
    db.refresh(project)
    return serialize_project(db, project)


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = _get_project(db, project_id)
    return serialize_project(db, project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectRead:
    current_user = get_current_user(db)
    project = _get_project(db, project_id)

    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if membership is None or membership.role not in {"owner", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user cannot edit this project")

    updates = payload.model_dump(exclude_unset=True)
    members = updates.pop("members", None)
    for field, value in updates.items():
        setattr(project, field, value)

    _upsert_project_owner_membership(db, project)
    if members is not None:
        _replace_project_members(db, project, members)

    record_local_change(db, "project.update")
    db.commit()
    db.refresh(project)
    return serialize_project(db, project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> Response:
    current_user = get_current_user(db)
    project = _get_project(db, project_id)
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == current_user.id,
        )
    )
    local_demo_override = _is_local_demo_mode() or current_user.id == get_settings().mock_user_id
    if not local_demo_override and (membership is None or membership.role not in {"owner", "editor"}):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user cannot delete this project")

    _delete_project_cascade(db, project)
    record_local_change(db, "project.delete")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
