from __future__ import annotations

from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .deps import get_or_create_mock_user
from .models import Experiment, ExperimentStepRun, ExperimentWorkflowRun, Project, Workflow
from .project_routes import serialize_project
from .schemas import ActivityItemRead, HomeSummaryRead, ProfileSummaryRead, UserRead


router = APIRouter(prefix="/api/v1", tags=["summary"])

PROFILE_EXPERTISE = [
    "Protein Purification",
    "FPLC/AKTA",
    "Crystallography",
    "SDS-PAGE",
    "NMR spectroscopy",
    "PCR & Cloning",
    "Cell culture",
    "Western blotting",
    "Mass spectrometry",
    "Python / BioPython",
]


def _build_recent_activity(db: Session, limit: int = 6) -> list[ActivityItemRead]:
    workflow_runs = db.scalars(select(ExperimentWorkflowRun)).all()
    workflow_run_by_id = {workflow_run.id: workflow_run for workflow_run in workflow_runs}
    experiments = db.scalars(select(Experiment)).all()
    experiment_by_id = {experiment.id: experiment for experiment in experiments}

    recent_step_runs = db.scalars(
        select(ExperimentStepRun).order_by(ExperimentStepRun.updated_at.desc()).limit(limit)
    ).all()

    activity: list[ActivityItemRead] = []
    for step_run in recent_step_runs:
        workflow_run = workflow_run_by_id.get(step_run.experiment_workflow_run_id)
        experiment = experiment_by_id.get(workflow_run.experiment_id) if workflow_run else None
        if experiment is None:
            continue

        verb = {
            "running": "Started",
            "complete": "Completed",
            "error": "Flagged error in",
            "planned": "Updated",
            "pending": "Updated",
            "blocked": "Blocked",
        }.get(step_run.status, "Updated")

        activity.append(
            ActivityItemRead(
                occurred_at=step_run.updated_at,
                message=f"{verb} {step_run.label} - {experiment.title}",
                type=step_run.status,
                context=workflow_run.workflow_title,
            )
        )

    if activity:
        return activity

    recent_experiments = db.scalars(
        select(Experiment).order_by(Experiment.created_at.desc()).limit(limit)
    ).all()
    return [
        ActivityItemRead(
            occurred_at=experiment.created_at,
            message=f"Created experiment - {experiment.title}",
            type=experiment.status,
            context=experiment.experiment_date.isoformat(),
        )
        for experiment in recent_experiments
    ]


def _completed_experiment_count(experiments: list[Experiment]) -> int:
    return sum(1 for experiment in experiments if experiment.status == "complete")


@router.get("/dashboard/home", response_model=HomeSummaryRead)
def read_home_summary(db: Session = Depends(get_db)) -> HomeSummaryRead:
    user = get_or_create_mock_user(db)
    projects = db.scalars(select(Project).order_by(Project.updated_at.desc(), Project.created_at.desc())).all()
    workflows = db.scalars(select(Workflow).order_by(Workflow.updated_at.desc(), Workflow.created_at.desc())).all()
    experiments = db.scalars(select(Experiment).order_by(Experiment.updated_at.desc(), Experiment.created_at.desc())).all()

    active_experiment_count = sum(1 for experiment in experiments if experiment.status in {"planned", "running", "blocked"})

    return HomeSummaryRead(
        user_display_name=user.display_name,
        active_experiment_count=active_experiment_count,
        protocol_count=len(workflows),
        project_count=len(projects),
        completed_experiment_count=_completed_experiment_count(experiments),
        recent_projects=[serialize_project(db, project) for project in projects[:3]],
        recent_activity=_build_recent_activity(db),
    )


@router.get("/profile/summary", response_model=ProfileSummaryRead)
def read_profile_summary(db: Session = Depends(get_db)) -> ProfileSummaryRead:
    user = get_or_create_mock_user(db)
    workflows = db.scalars(select(Workflow)).all()
    projects = db.scalars(select(Project)).all()
    experiments = db.scalars(select(Experiment)).all()

    month_counts = Counter(experiment.experiment_date.month for experiment in experiments if experiment.experiment_date)
    monthly_activity = [month_counts.get(month, 0) for month in range(1, 13)]

    return ProfileSummaryRead(
        user=UserRead.model_validate(user),
        institution="MIT",
        lab_name="Ferretti Lab",
        focus="Protein biochemistry focus",
        expertise=PROFILE_EXPERTISE,
        experiment_count=len(experiments),
        protocol_count=len(workflows),
        project_count=len(projects),
        completed_experiment_count=_completed_experiment_count(experiments),
        recent_activity=_build_recent_activity(db),
        monthly_activity=monthly_activity,
    )
