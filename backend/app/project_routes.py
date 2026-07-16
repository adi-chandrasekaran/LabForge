from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .deps import get_or_create_mock_user
from .models import Experiment, ExperimentStepRun, ExperimentWorkflowRun, Project, User
from .schemas import ProjectCreate, ProjectRead
from .sync import record_local_change


router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _new_project_id() -> str:
    return f"project-{uuid4().hex[:10]}"


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
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _get_project(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    projects = db.scalars(select(Project).order_by(Project.updated_at.desc(), Project.created_at.desc())).all()
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
    record_local_change(db, "project.create")
    db.commit()
    db.refresh(project)
    return serialize_project(db, project)


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = _get_project(db, project_id)
    return serialize_project(db, project)
