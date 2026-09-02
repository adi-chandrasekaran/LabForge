from __future__ import annotations

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .attachments import serialize_attachment
from .config import get_settings
from .database import get_db
from .deps import get_current_user, get_or_create_mock_user
from .models import Attachment, User, Workflow, WorkflowBranch, WorkflowMember, WorkflowStep
from .schemas import (
    WorkflowBranchCreate,
    WorkflowBranchRead,
    WorkflowBranchStepCreate,
    WorkflowBranchStepRead,
    WorkflowBranchUpdate,
    WorkflowCreate,
    WorkflowInsertStandardizedRequest,
    WorkflowMemberRead,
    WorkflowRead,
    WorkflowStandardizeRequest,
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


def _new_workflow_member_id() -> str:
    return f"workflow-member-{uuid4().hex[:10]}"


def _is_local_demo_mode() -> bool:
    settings = get_settings()
    return settings.app_mode == "local" or settings.auth_backend == "mock"


def _serialize_workflow_members(db: Session, workflow_id: str) -> list[WorkflowMemberRead]:
    members = db.scalars(
        select(WorkflowMember)
        .where(WorkflowMember.workflow_id == workflow_id)
        .order_by(WorkflowMember.created_at, WorkflowMember.id)
    ).all()
    users = {member.user_id: db.get(User, member.user_id) for member in members}
    serialized = [
        WorkflowMemberRead(
            user_id=member.user_id,
            display_name=users[member.user_id].display_name if users.get(member.user_id) else member.user_id,
            email=users[member.user_id].email if users.get(member.user_id) else "",
            lab_role=users[member.user_id].role if users.get(member.user_id) else "unknown",
            workflow_role=member.role,
        )
        for member in members
    ]
    return sorted(serialized, key=lambda member: (0 if member.workflow_role == "owner" else 1, member.display_name.lower()))


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
        project_id=workflow.project_id,
        visibility=workflow.visibility,
        library_state=workflow.library_state,
        version=workflow.version,
        tags=workflow.tags,
        members=_serialize_workflow_members(db, workflow.id),
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


def _upsert_workflow_owner_membership(db: Session, workflow: Workflow) -> None:
    if not workflow.owner_id:
        return

    owner_membership = db.scalar(
        select(WorkflowMember).where(
            WorkflowMember.workflow_id == workflow.id,
            WorkflowMember.user_id == workflow.owner_id,
        )
    )
    if owner_membership is None:
        db.add(
            WorkflowMember(
                id=_new_workflow_member_id(),
                workflow_id=workflow.id,
                user_id=workflow.owner_id,
                role="owner",
            )
        )
    else:
        owner_membership.role = "owner"


def _replace_workflow_members(db: Session, workflow: Workflow, members: list[dict[str, str]]) -> None:
    member_map = {
        member["user_id"]: member["role"]
        for member in members
        if member["user_id"] and member["role"]
    }
    if workflow.owner_id:
        member_map[workflow.owner_id] = "owner"

    existing = db.scalars(select(WorkflowMember).where(WorkflowMember.workflow_id == workflow.id)).all()
    existing_by_user_id = {member.user_id: member for member in existing}

    for user_id, role in member_map.items():
        if db.get(User, user_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lab user {user_id} does not exist")
        if user_id in existing_by_user_id:
            existing_by_user_id[user_id].role = role
        else:
            db.add(
                WorkflowMember(
                    id=_new_workflow_member_id(),
                    workflow_id=workflow.id,
                    user_id=user_id,
                    role=role,
                )
            )

    for member in existing:
        if member.user_id not in member_map:
            db.delete(member)


def _assert_workflow_can_edit(db: Session, workflow: Workflow) -> None:
    current_user = get_current_user(db)
    if _is_local_demo_mode() or current_user.id == get_settings().mock_user_id:
        return
    membership = db.scalar(
        select(WorkflowMember).where(
            WorkflowMember.workflow_id == workflow.id,
            WorkflowMember.user_id == current_user.id,
        )
    )
    if membership is None or membership.role not in {"owner", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user cannot edit this workflow")


def _step_clone_kwargs(step: WorkflowStep, workflow_id: str, order_index: int, branch_id: Optional[str] = None) -> dict:
    return {
        "id": _new_id("step" if branch_id is None else "branch-step"),
        "workflow_id": workflow_id,
        "workflow_branch_id": branch_id,
        "parent_step_id": step.parent_step_id,
        "branch_track_id": branch_id,
        "order_index": order_index,
        "label": step.label,
        "sublabel": step.sublabel,
        "status_template": step.status_template,
        "duration": step.duration,
        "procedure_markdown": step.procedure_markdown,
        "inputs": list(step.inputs or []),
        "parameters": list(step.parameters or []),
        "outputs": list(step.outputs or []),
        "notes": step.notes or "",
    }


def _copy_main_steps(db: Session, source_workflow_id: str, target_workflow_id: str, start_index: int) -> None:
    source_steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == source_workflow_id, WorkflowStep.workflow_branch_id.is_(None))
        .order_by(WorkflowStep.order_index)
    ).all()
    for offset, source_step in enumerate(source_steps):
        db.add(WorkflowStep(**_step_clone_kwargs(source_step, target_workflow_id, start_index + offset)))


def _main_step_count(db: Session, workflow_id: str) -> int:
    return len(
        db.scalars(
            select(WorkflowStep.id).where(
                WorkflowStep.workflow_id == workflow_id,
                WorkflowStep.workflow_branch_id.is_(None),
            )
        ).all()
    )


def _copy_branch_steps(
    db: Session,
    source_workflow_id: str,
    target_workflow_id: str,
    branch_id: str,
    parent_step_id: str,
) -> None:
    source_steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == source_workflow_id, WorkflowStep.workflow_branch_id.is_(None))
        .order_by(WorkflowStep.order_index)
    ).all()
    for offset, source_step in enumerate(source_steps, start=1):
        kwargs = _step_clone_kwargs(source_step, target_workflow_id, offset, branch_id)
        kwargs["parent_step_id"] = parent_step_id
        db.add(WorkflowStep(**kwargs))


@router.get("", response_model=list[WorkflowRead])
def list_workflows(
    tag: Optional[str] = Query(default=None),
    library_state: Optional[str] = Query(default=None),
    visibility: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[WorkflowRead]:
    query = select(Workflow).order_by(Workflow.title)
    workflows = db.scalars(query).all()
    if tag is not None:
        workflows = [workflow for workflow in workflows if tag in workflow.tags]
    if library_state is not None:
        workflows = [workflow for workflow in workflows if workflow.library_state == library_state]
    if visibility is not None:
        workflows = [workflow for workflow in workflows if workflow.visibility == visibility]
    if project_id is not None:
        workflows = [workflow for workflow in workflows if workflow.project_id == project_id]
    return [_serialize_workflow(db, workflow) for workflow in workflows]


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    user = get_or_create_mock_user(db)
    workflow = Workflow(
        id=_new_id("workflow"),
        title=payload.title,
        description=payload.description,
        owner_id=user.id,
        project_id=payload.project_id,
        visibility=payload.visibility,
        library_state=payload.library_state,
        version=payload.version,
        tags=payload.tags,
    )
    db.add(workflow)
    db.flush()
    _upsert_workflow_owner_membership(db, workflow)
    if payload.members is not None:
        _replace_workflow_members(
            db,
            workflow,
            [member.model_dump() for member in payload.members],
        )
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
    _assert_workflow_can_edit(db, workflow)
    updates = payload.model_dump(exclude_unset=True)
    members = updates.pop("members", None)
    for field, value in updates.items():
        setattr(workflow, field, value)
    _upsert_workflow_owner_membership(db, workflow)
    if members is not None:
        _replace_workflow_members(db, workflow, members)
    record_local_change(db, "workflow.update")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)) -> Response:
    workflow = _get_workflow(db, workflow_id)
    _assert_workflow_can_edit(db, workflow)
    step_ids = db.scalars(select(WorkflowStep.id).where(WorkflowStep.workflow_id == workflow.id)).all()
    if step_ids:
        db.execute(
            delete(Attachment).where(
                Attachment.owner_type == "workflow_step",
                Attachment.owner_id.in_(step_ids),
            )
        )
    branch_ids = db.scalars(select(WorkflowBranch.id).where(WorkflowBranch.workflow_id == workflow.id)).all()
    if branch_ids:
        db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_branch_id.in_(branch_ids)))
        db.execute(delete(WorkflowBranch).where(WorkflowBranch.id.in_(branch_ids)))
    db.execute(
        delete(WorkflowStep).where(
            WorkflowStep.workflow_id == workflow.id,
            WorkflowStep.workflow_branch_id.is_(None),
        )
    )
    db.execute(delete(WorkflowMember).where(WorkflowMember.workflow_id == workflow.id))
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
    _assert_workflow_can_edit(db, workflow)
    workflow.library_state = "published"
    workflow.visibility = "library"
    record_local_change(db, "workflow.publish")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.post("/{workflow_id}/standardize", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def standardize_workflow(
    workflow_id: str,
    payload: WorkflowStandardizeRequest,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    source = _get_workflow(db, workflow_id)
    _assert_workflow_can_edit(db, source)
    user = get_or_create_mock_user(db)
    tags = list(dict.fromkeys(["standardized", *payload.tags]))
    standardized = Workflow(
        id=_new_id("workflow-standard"),
        title=payload.title,
        description=payload.description,
        owner_id=user.id,
        project_id=None,
        visibility="library",
        library_state="published",
        version=1,
        tags=tags,
    )
    db.add(standardized)
    db.flush()
    _upsert_workflow_owner_membership(db, standardized)
    if payload.members is not None:
        _replace_workflow_members(
            db,
            standardized,
            [member.model_dump() for member in payload.members],
        )
    _copy_main_steps(db, source.id, standardized.id, 1)
    record_local_change(db, "workflow.standardize")
    db.commit()
    db.refresh(standardized)
    return _serialize_workflow(db, standardized)


@router.post("/{workflow_id}/insert-standardized", response_model=WorkflowRead)
def insert_standardized_workflow(
    workflow_id: str,
    payload: WorkflowInsertStandardizedRequest,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    target = _get_workflow(db, workflow_id)
    _assert_workflow_can_edit(db, target)
    source = _get_workflow(db, payload.standardized_workflow_id)

    if payload.anchor_step_id:
        anchor_step = _get_step(db, workflow_id, payload.anchor_step_id)
        if anchor_step.workflow_branch_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch anchors must be main workflow steps")
        branch = WorkflowBranch(
            id=_new_id("branch"),
            workflow_id=workflow_id,
            anchor_step_id=anchor_step.id,
            label=payload.branch_label or source.title,
        )
        db.add(branch)
        db.flush()
        _copy_branch_steps(db, source.id, target.id, branch.id, anchor_step.id)
        record_local_change(db, "workflow.standardized.insert.branch")
        db.commit()
        db.refresh(target)
        return _serialize_workflow(db, target)

    main_steps = db.scalars(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow_id, WorkflowStep.workflow_branch_id.is_(None))
        .order_by(WorkflowStep.order_index)
    ).all()
    insert_index = len(main_steps) + 1
    if payload.after_step_id is not None:
        after_step = _get_step(db, workflow_id, payload.after_step_id)
        if after_step.workflow_branch_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use branch insertion for branch steps")
        insert_index = after_step.order_index + 1
    for step in main_steps:
        if step.order_index >= insert_index:
            step.order_index += _main_step_count(db, source.id)
    _copy_main_steps(db, source.id, target.id, insert_index)
    record_local_change(db, "workflow.standardized.insert.mainline")
    db.commit()
    db.refresh(target)
    return _serialize_workflow(db, target)


@router.post("/{workflow_id}/steps", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow_step(workflow_id: str, payload: WorkflowStepCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
    branch = _get_branch(db, workflow_id, branch_id)
    branch.label = payload.label
    record_local_change(db, "workflow.branch.update")
    db.commit()
    db.refresh(workflow)
    return _serialize_workflow(db, workflow)


@router.delete("/{workflow_id}/branches/{branch_id}", response_model=WorkflowRead)
def delete_workflow_branch(workflow_id: str, branch_id: str, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = _get_workflow(db, workflow_id)
    _assert_workflow_can_edit(db, workflow)
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
    _assert_workflow_can_edit(db, workflow)
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
