from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user
from .models import AgentConversation, AgentRun, AgentWorkflowDraft, User, Workflow, WorkflowBranch, WorkflowMember, WorkflowStep
from .sync import record_local_change
from .workflow_routes import _assert_project_exists, _assert_standardized_workflow_has_type, _get_branch, _get_step, _get_workflow, _replace_workflow_members, _serialize_workflow, _upsert_workflow_owner_membership, _new_id
from .schemas import WorkflowCreate, WorkflowStepCreate, WorkflowStepUpdate, WorkflowStepReorderRequest, WorkflowBranchCreate, WorkflowUpdate

router = APIRouter(prefix="/api/v1/agent/workflow-drafts", tags=["agent-workflow-drafts"])

class DraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Literal["create_workflow", "update_workflow", "add_step", "update_step", "reorder_steps", "create_branch", "replace_members"]
    payload: dict[str, Any]
    conversation_id: Optional[str] = None
    run_id: Optional[str] = None

class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; owner_id: str; conversation_id: Optional[str]; run_id: Optional[str]
    operation: str; payload: dict[str, Any]; resource_versions: dict[str, Any]; status: str
    result: Optional[dict[str, Any]]; failure_code: Optional[str]; failure_detail: Optional[str]
    expires_at: datetime; created_at: datetime; decided_at: Optional[datetime]

def _owned(db: Session, user: User, draft_id: str) -> AgentWorkflowDraft:
    draft = db.scalar(select(AgentWorkflowDraft).where(AgentWorkflowDraft.id == draft_id, AgentWorkflowDraft.owner_id == user.id))
    if draft is None: raise HTTPException(404, "Workflow change draft not found")
    return draft

def _workflow_for_payload(db: Session, payload: dict[str, Any]) -> Optional[Workflow]:
    workflow_id = payload.get("workflow_id")
    return _get_workflow(db, workflow_id) if workflow_id else None

def _can_edit(db: Session, user: User, workflow: Workflow) -> None:
    member = db.scalar(select(WorkflowMember).where(WorkflowMember.workflow_id == workflow.id, WorkflowMember.user_id == user.id))
    if workflow.owner_id != user.id and (member is None or member.role not in {"owner", "editor"}):
        raise HTTPException(403, "Current user cannot edit this workflow")

def _step_values(data: WorkflowStepCreate | WorkflowStepUpdate) -> dict[str, Any]:
    values = data.model_dump(exclude={"after_step_id"}, exclude_none=True)
    for field in ("inputs", "parameters", "outputs"):
        values[field] = [item.model_dump(exclude_none=True) if hasattr(item, "model_dump") else item for item in values[field]]
    return values

def create_workflow_draft(db: Session, user: User, payload: DraftCreate) -> AgentWorkflowDraft:
    if payload.conversation_id and db.scalar(select(AgentConversation).where(AgentConversation.id == payload.conversation_id, AgentConversation.owner_id == user.id)) is None:
        raise HTTPException(404, "Agent conversation not found")
    if payload.run_id and db.scalar(select(AgentRun).join(AgentConversation).where(AgentRun.id == payload.run_id, AgentConversation.owner_id == user.id)) is None:
        raise HTTPException(404, "Agent run not found")
    workflow = _workflow_for_payload(db, payload.payload)
    if workflow: _can_edit(db, user, workflow)
    versions = {"workflow_id": workflow.id, "workflow_version": workflow.version, "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None} if workflow else {}
    draft = AgentWorkflowDraft(id=f"agent-workflow-draft-{uuid4().hex}", owner_id=user.id, conversation_id=payload.conversation_id, run_id=payload.run_id, operation=payload.operation, payload=payload.payload, resource_versions=versions, expires_at=datetime.utcnow()+timedelta(hours=24))
    db.add(draft); db.commit(); db.refresh(draft)
    return draft

@router.post("", response_model=DraftRead, status_code=201)
def create_draft(payload: DraftCreate, db: Session = Depends(get_db)) -> DraftRead:
    return create_workflow_draft(db, get_current_user(db), payload)

@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> DraftRead:
    return _owned(db, get_current_user(db), draft_id)

@router.post("/{draft_id}/confirm", response_model=DraftRead)
def confirm_draft(draft_id: str, db: Session = Depends(get_db)) -> DraftRead:
    user = get_current_user(db); draft = _owned(db, user, draft_id)
    if draft.status != "pending": raise HTTPException(409, "This draft has already been decided")
    if draft.expires_at.replace(tzinfo=None) < datetime.utcnow():
        draft.status="expired"; draft.decided_at=datetime.utcnow(); db.commit(); raise HTTPException(409, "This draft has expired")
    try:
        p = draft.payload; workflow = _workflow_for_payload(db, p)
        if workflow:
            _can_edit(db, user, workflow)
            recorded = draft.resource_versions
            if recorded.get("updated_at") and workflow.updated_at and recorded["updated_at"] != workflow.updated_at.isoformat():
                draft.status="stale"; draft.failure_code="stale_resource"; draft.failure_detail="The workflow changed after this draft was prepared."; draft.decided_at=datetime.utcnow(); db.commit(); raise HTTPException(409, draft.failure_detail)
        if draft.operation == "create_workflow":
            data=WorkflowCreate.model_validate(p); _assert_standardized_workflow_has_type(data); _assert_project_exists(db,data.project_id)
            workflow=Workflow(id=_new_id("workflow"), title=data.title, description=data.description, owner_id=user.id, project_id=data.project_id, visibility=data.visibility, library_state=data.library_state, version=data.version, tags=data.tags); db.add(workflow); db.flush(); _upsert_workflow_owner_membership(db,workflow)
            if data.members is not None: _replace_workflow_members(db,workflow,[m.model_dump() for m in data.members])
        elif draft.operation == "update_workflow":
            data=WorkflowUpdate.model_validate(p["changes"]); updates=data.model_dump(exclude_unset=True); members=updates.pop("members",None)
            for key,value in updates.items(): setattr(workflow,key,value)
            if members is not None: _replace_workflow_members(db,workflow,[m if isinstance(m,dict) else m.model_dump() for m in members])
        elif draft.operation == "add_step":
            data=WorkflowStepCreate.model_validate(p["step"]); steps=db.scalars(select(WorkflowStep).where(WorkflowStep.workflow_id==workflow.id,WorkflowStep.workflow_branch_id.is_(None)).order_by(WorkflowStep.order_index)).all(); index=len(steps)+1
            if data.after_step_id: index=_get_step(db,workflow.id,data.after_step_id).order_index+1
            for step in steps:
                if step.order_index>=index: step.order_index+=1
            db.add(WorkflowStep(id=_new_id("step"),workflow_id=workflow.id,order_index=index,**_step_values(data)))
        elif draft.operation == "update_step":
            step=_get_step(db,workflow.id,p["step_id"]); data=WorkflowStepUpdate.model_validate(p["changes"])
            for key,value in _step_values(data).items(): setattr(step,key,value)
        elif draft.operation == "reorder_steps":
            data=WorkflowStepReorderRequest.model_validate(p["reorder"]); steps=db.scalars(select(WorkflowStep).where(WorkflowStep.workflow_id==workflow.id, WorkflowStep.workflow_branch_id == data.branch_id if data.branch_id else WorkflowStep.workflow_branch_id.is_(None))).all(); mapping={s.id:s for s in steps}
            if set(mapping)!=set(data.ordered_step_ids): raise HTTPException(400,"Ordered step ids must match the target step set")
            for i,step_id in enumerate(data.ordered_step_ids,1): mapping[step_id].order_index=i
        elif draft.operation == "create_branch":
            data=WorkflowBranchCreate.model_validate(p["branch"]); anchor=_get_step(db,workflow.id,data.anchor_step_id)
            if anchor.workflow_branch_id: raise HTTPException(400,"Branch anchors must be main workflow steps")
            db.add(WorkflowBranch(id=_new_id("branch"),workflow_id=workflow.id,anchor_step_id=data.anchor_step_id,label=data.label))
        elif draft.operation == "replace_members":
            _replace_workflow_members(db,workflow,p["members"])
        record_local_change(db, "agent.workflow_draft.confirm")
        db.flush(); draft.status="confirmed"; draft.decided_at=datetime.utcnow(); draft.result={"workflow": _serialize_workflow(db,workflow).model_dump(mode="json")}; db.commit(); db.refresh(draft); return draft
    except HTTPException:
        raise
    except Exception as error:
        db.rollback(); draft = _owned(db,user,draft_id); draft.status="failed"; draft.failure_code="apply_failed"; draft.failure_detail="The draft could not be applied."; draft.decided_at=datetime.utcnow(); db.commit(); raise HTTPException(422,"The draft could not be applied.") from error
