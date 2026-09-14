"""Read-only foundation for the future NMR research-assistant runtime."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional, Protocol, Union
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .agent_tools import TOOL_REGISTRY
from .config import Settings, get_settings
from .models import AgentConversation, AgentRun, AgentToolCall, User


ASSISTANT_INSTRUCTIONS = """You are the NMR research assistant for this lab notebook.
Use the supplied read-only tools whenever a statement depends on the user's stored data.
Never invent experimental values, spectra, peak assignments, chemical shifts, residues,
samples, or conclusions about a dataset. If the required data or an appropriate tool is
unavailable, say so explicitly. Clearly distinguish retrieved observations from general
NMR guidance. Return only a JSON object with answer, data_availability, and
evidence_tool_call_ids. A retrieved answer must cite successful tool-call ids from this run."""


class AgentConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="Untitled NMR research conversation", min_length=1, max_length=200)


class AgentConversationRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class AgentToolCallRead(BaseModel):
    id: str
    sequence: int
    tool_name: str
    arguments: dict[str, Any]
    result: Optional[dict[str, Any]]
    status: str
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class AgentRunRead(BaseModel):
    id: str
    conversation_id: str
    user_request: str
    provider: str
    model: str
    status: str
    final_answer: Optional[str]
    data_availability: Optional[str]
    evidence_tool_call_ids: list[str]
    provider_response_id: Optional[str]
    failure_code: Optional[str]
    failure_detail: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AgentRunDetailRead(AgentRunRead):
    tool_calls: list[AgentToolCallRead] = Field(default_factory=list)


class AgentStatusRead(BaseModel):
    available: bool
    code: Optional[str] = None
    provider: str = "openai"
    model: str
    detail: str


class AgentFinalAnswer(BaseModel):
    """The final output contract enforced by the PR 5 execution loop."""
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)
    data_availability: Literal["retrieved", "unavailable", "general_guidance"]
    evidence_tool_call_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence(self) -> "AgentFinalAnswer":
        if self.data_availability == "retrieved" and not self.evidence_tool_call_ids:
            raise ValueError("Retrieved answers must cite at least one successful tool-call id.")
        if self.data_availability == "unavailable" and "unavailable" not in self.answer.casefold():
            raise ValueError("Unavailable answers must explicitly state that required data is unavailable.")
        return self


class NMRResearchAssistant(Protocol):
    provider: str
    model: str

    def function_definitions(self) -> list[dict[str, Any]]: ...


def read_only_function_definitions() -> list[dict[str, Any]]:
    """Translate only executable, non-writing PR 3 tools into Responses tools."""
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_model.model_json_schema(),
            "strict": True,
        }
        for tool in TOOL_REGISTRY.values()
        if not tool.confirmation_required and tool.side_effect == "none"
    ]


class OpenAIResponsesResearchAssistant:
    """Provider boundary only; PR 4 deliberately makes no network request."""
    provider = "openai"

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self.model = self._settings.agent_model

    @property
    def configured(self) -> bool:
        return bool(self._settings.openai_api_key)

    def function_definitions(self) -> list[dict[str, Any]]:
        return read_only_function_definitions()


def assistant_status(settings: Optional[Settings] = None) -> AgentStatusRead:
    provider = OpenAIResponsesResearchAssistant(settings)
    if not provider.configured:
        return AgentStatusRead(available=False, code="agent_unavailable", model=provider.model,
            detail="The NMR research assistant is unavailable because its server-side provider key is not configured.")
    return AgentStatusRead(available=True, model=provider.model,
        detail="The OpenAI Responses provider is configured. Model execution is introduced in PR 5.")


def _conversation_or_404(db: Session, user: User, conversation_id: str) -> AgentConversation:
    conversation = db.scalar(select(AgentConversation).where(
        AgentConversation.id == conversation_id, AgentConversation.owner_id == user.id))
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent conversation not found")
    return conversation


def create_conversation(db: Session, user: User, payload: AgentConversationCreate) -> AgentConversation:
    conversation = AgentConversation(id=f"agent-conversation-{uuid4().hex}", owner_id=user.id, title=payload.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, user: User, conversation_id: str) -> AgentConversation:
    return _conversation_or_404(db, user, conversation_id)


def list_runs(db: Session, user: User, conversation_id: str) -> list[AgentRun]:
    _conversation_or_404(db, user, conversation_id)
    return list(db.scalars(select(AgentRun).where(AgentRun.conversation_id == conversation_id).order_by(AgentRun.created_at.desc())))


def get_run(db: Session, user: User, conversation_id: str, run_id: str) -> AgentRun:
    _conversation_or_404(db, user, conversation_id)
    run = db.scalar(select(AgentRun).options(selectinload(AgentRun.tool_calls)).where(
        AgentRun.id == run_id, AgentRun.conversation_id == conversation_id))
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return run


def serialize_conversation(conversation: AgentConversation) -> AgentConversationRead:
    return AgentConversationRead.model_validate(conversation, from_attributes=True)


def serialize_tool_call(tool_call: AgentToolCall) -> AgentToolCallRead:
    return AgentToolCallRead.model_validate(tool_call, from_attributes=True)


def serialize_run(run: AgentRun, include_tool_calls: bool = False) -> Union[AgentRunRead, AgentRunDetailRead]:
    payload = AgentRunRead.model_validate(run, from_attributes=True).model_dump()
    if include_tool_calls:
        payload["tool_calls"] = [serialize_tool_call(call).model_dump() for call in sorted(run.tool_calls, key=lambda call: call.sequence)]
        return AgentRunDetailRead.model_validate(payload)
    return AgentRunRead.model_validate(payload)
