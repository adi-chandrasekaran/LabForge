"""Read-only foundation for the future NMR research-assistant runtime."""
from __future__ import annotations

from datetime import datetime
import json
import logging
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

logger = logging.getLogger(__name__)
MAX_TOOL_ROUNDS = 5
CONTEXT_RUN_LIMIT = 10


class AgentConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="Untitled NMR research conversation", min_length=1, max_length=200)


class AgentRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=20_000)


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


class AgentExecutionErrorRead(BaseModel):
    code: str
    message: str
    run_id: Optional[str] = None


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
    def respond(self, input_items: list[dict[str, Any]], previous_response_id: Optional[str] = None) -> "ProviderResponse": ...


class ProviderToolCall(BaseModel):
    call_id: str
    name: str
    arguments: str


class ProviderResponse(BaseModel):
    id: str
    tool_calls: list[ProviderToolCall] = Field(default_factory=list)
    output_text: str = ""


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

    def respond(self, input_items: list[dict[str, Any]], previous_response_id: Optional[str] = None) -> ProviderResponse:
        if not self.configured:
            raise AgentExecutionException(503, "agent_unavailable", "The NMR research assistant provider is not configured.")
        from openai import OpenAI

        client = OpenAI(api_key=self._settings.openai_api_key)
        request: dict[str, Any] = {
            "model": self.model,
            "instructions": ASSISTANT_INSTRUCTIONS,
            "input": input_items,
            "tools": self.function_definitions(),
        }
        if previous_response_id:
            request["previous_response_id"] = previous_response_id
        try:
            response = client.responses.create(**request)
        except Exception as error:
            logger.warning("agent_provider_failure provider=openai error_type=%s", type(error).__name__)
            raise AgentExecutionException(502, "provider_failed", "The research assistant provider could not complete the request.") from error

        calls = [
            ProviderToolCall(call_id=item.call_id, name=item.name, arguments=item.arguments)
            for item in response.output
            if getattr(item, "type", None) == "function_call"
        ]
        return ProviderResponse(id=response.id, tool_calls=calls, output_text=getattr(response, "output_text", ""))


def assistant_status(settings: Optional[Settings] = None) -> AgentStatusRead:
    provider = OpenAIResponsesResearchAssistant(settings)
    if not provider.configured:
        return AgentStatusRead(available=False, code="agent_unavailable", model=provider.model,
            detail="The NMR research assistant is unavailable because its server-side provider key is not configured.")
    return AgentStatusRead(available=True, model=provider.model,
        detail="The OpenAI Responses provider is configured. Model execution is introduced in PR 5.")


def get_research_assistant(settings: Optional[Settings] = None) -> NMRResearchAssistant:
    return OpenAIResponsesResearchAssistant(settings)


class AgentExecutionException(Exception):
    def __init__(self, status_code: int, code: str, message: str, run_id: Optional[str] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.run_id = run_id
        super().__init__(message)


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


def _complete_runs_context(db: Session, conversation_id: str) -> list[dict[str, Any]]:
    runs = list(db.scalars(select(AgentRun).where(
        AgentRun.conversation_id == conversation_id,
        AgentRun.status == "completed",
    ).order_by(AgentRun.created_at.desc()).limit(CONTEXT_RUN_LIMIT)))
    context: list[dict[str, Any]] = []
    for run in reversed(runs):
        context.extend([
            {"role": "user", "content": run.user_request},
            {"role": "assistant", "content": json.dumps({
                "answer": run.final_answer,
                "data_availability": run.data_availability,
                "evidence_tool_call_ids": run.evidence_tool_call_ids,
            })},
        ])
    return context


def _mark_failed(db: Session, run: AgentRun, code: str, detail: str) -> None:
    run.status = "failed"
    run.failure_code = code
    run.failure_detail = detail
    run.completed_at = datetime.utcnow()
    db.commit()
    logger.warning("agent_run_failed run_id=%s code=%s", run.id, code)


def _tool_error(name: str, code: str, message: str) -> dict[str, Any]:
    return {"tool_name": name, "ok": False, "data": None, "error": {"code": code, "message": message, "details": None}}


def _execute_provider_tool_call(db: Session, user: User, run: AgentRun, sequence: int, call: ProviderToolCall) -> dict[str, Any]:
    from .agent_tools import TOOL_REGISTRY, ToolInvocationException, ToolInvocationRequest, error_response, invoke

    call_id = f"agent-tool-call-{uuid4().hex}"
    try:
        arguments = json.loads(call.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be an object")
    except (TypeError, ValueError, json.JSONDecodeError):
        arguments = {}
        response = _tool_error(call.name, "invalid_tool_arguments", "Tool arguments must be a JSON object.")
    else:
        tool = TOOL_REGISTRY.get(call.name)
        if tool is None:
            response = _tool_error(call.name, "tool_not_allowed", "This tool is not available to the research assistant.")
        elif tool.confirmation_required or tool.side_effect != "none":
            response = _tool_error(call.name, "tool_write_forbidden", "The research assistant may execute read-only tools only.")
        else:
            try:
                response = invoke(db, user, call.name, ToolInvocationRequest(arguments=arguments, confirmed=False)).model_dump(mode="json")
            except ToolInvocationException as error:
                response = error_response(call.name, error).model_dump(mode="json")

    error = response.get("error")
    record = AgentToolCall(
        id=call_id,
        run_id=run.id,
        sequence=sequence,
        tool_name=call.name,
        arguments=arguments,
        result=response,
        status="completed" if response["ok"] else "failed",
        error_code=error["code"] if error else None,
        error_message=error["message"] if error else None,
        completed_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    logger.info("agent_tool_call run_id=%s tool=%s ok=%s", run.id, call.name, response["ok"])
    response_for_model = {**response, "audit_tool_call_id": call_id}
    return {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(response_for_model)}


def _validate_final_answer(run: AgentRun, text: str) -> AgentFinalAnswer:
    try:
        answer = AgentFinalAnswer.model_validate_json(text)
    except Exception as error:
        raise AgentExecutionException(502, "invalid_final_response", "The research assistant returned an invalid final response.", run.id) from error
    successful_ids = {call.id for call in run.tool_calls if call.status == "completed" and call.result and call.result.get("ok")}
    if answer.data_availability == "retrieved" and not set(answer.evidence_tool_call_ids).issubset(successful_ids):
        raise AgentExecutionException(502, "invalid_final_response", "The research assistant cited invalid retrieval evidence.", run.id)
    return answer


def execute_run(db: Session, user: User, conversation_id: str, payload: AgentRunCreate, assistant: Optional[NMRResearchAssistant] = None) -> AgentRun:
    _conversation_or_404(db, user, conversation_id)
    provider = assistant or get_research_assistant()
    run = AgentRun(
        id=f"agent-run-{uuid4().hex}", conversation_id=conversation_id, user_request=payload.message,
        provider=provider.provider, model=provider.model, status="running", started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    logger.info("agent_run_started run_id=%s provider=%s model=%s", run.id, provider.provider, provider.model)

    if isinstance(provider, OpenAIResponsesResearchAssistant) and not provider.configured:
        _mark_failed(db, run, "agent_unavailable", "The NMR research assistant provider is not configured.")
        raise AgentExecutionException(503, "agent_unavailable", "The NMR research assistant provider is not configured.", run.id)

    inputs = _complete_runs_context(db, conversation_id) + [{"role": "user", "content": payload.message}]
    previous_response_id: Optional[str] = None
    sequence = 1
    try:
        for _round in range(MAX_TOOL_ROUNDS):
            response = provider.respond(inputs, previous_response_id)
            run.provider_response_id = response.id
            db.commit()
            if not response.tool_calls:
                db.refresh(run, ["tool_calls"])
                final_answer = _validate_final_answer(run, response.output_text)
                run.final_answer = final_answer.answer
                run.data_availability = final_answer.data_availability
                run.evidence_tool_call_ids = final_answer.evidence_tool_call_ids
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                db.commit()
                logger.info("agent_run_completed run_id=%s availability=%s", run.id, final_answer.data_availability)
                return get_run(db, user, conversation_id, run.id)
            inputs = []
            for call in response.tool_calls:
                inputs.append(_execute_provider_tool_call(db, user, run, sequence, call))
                sequence += 1
            previous_response_id = response.id
    except AgentExecutionException as error:
        if run.status != "failed":
            _mark_failed(db, run, error.code, error.message)
        raise
    except Exception as error:
        _mark_failed(db, run, "provider_failed", "The research assistant could not complete the request.")
        raise AgentExecutionException(502, "provider_failed", "The research assistant could not complete the request.", run.id) from error

    _mark_failed(db, run, "tool_round_limit_exceeded", "The research assistant exceeded the five-round tool limit.")
    raise AgentExecutionException(502, "tool_round_limit_exceeded", "The research assistant exceeded the five-round tool limit.", run.id)


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
