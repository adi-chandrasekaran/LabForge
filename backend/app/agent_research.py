"""Read-only foundation for the future NMR research-assistant runtime."""
from __future__ import annotations

from datetime import datetime
import json
import logging
from urllib import error as urllib_error
from urllib import request as urllib_request
from typing import Any, Literal, Optional, Protocol, Union
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .agent_tools import TOOL_REGISTRY
from .agent_presenter import format_tool_evidence
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


class AgentProviderDiagnosticRead(BaseModel):
    ok: bool
    provider: str
    model: str
    code: Optional[str] = None
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
    configured: bool

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
        if tool.model_callable or (not tool.confirmation_required and tool.side_effect == "none")
    ]


class OpenAIResponsesResearchAssistant:
    """OpenAI Responses implementation of the research-assistant provider."""
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


class GeminiResearchAssistant:
    """Gemini implementation that preserves the shared read-only tool loop."""

    provider = "gemini"

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self.model = self._settings.gemini_model
        self._contents: list[dict[str, Any]] = []

    @property
    def configured(self) -> bool:
        return bool(self._settings.gemini_api_key)

    def function_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters_json_schema": tool["parameters"],
            }
            for tool in read_only_function_definitions()
        ]

    def _initial_contents(self, input_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []
        for item in input_items:
            role = item.get("role", "user")
            if role not in {"user", "assistant"}:
                continue
            contents.append({
                "role": "model" if role == "assistant" else "user",
                "parts": [{"text": item.get("content", "")}],
            })
        return contents

    def _function_responses(self, input_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = []
        for item in input_items:
            if item.get("type") != "function_call_output":
                continue
            try:
                result = json.loads(item.get("output", "{}"))
            except (TypeError, ValueError, json.JSONDecodeError):
                result = _tool_error("unknown", "invalid_tool_result", "The tool result could not be decoded.")
            parts.append({
                "function_response": {
                    "name": item.get("name", "tool_result"),
                    "response": result,
                }
            })
        return [{"role": "user", "parts": parts}] if parts else []

    def respond(self, input_items: list[dict[str, Any]], previous_response_id: Optional[str] = None) -> ProviderResponse:
        if not self.configured:
            raise AgentExecutionException(503, "agent_unavailable", "The NMR research assistant provider is not configured.")
        from google import genai

        if previous_response_id is None:
            self._contents = self._initial_contents(input_items)
        else:
            self._contents.extend(self._function_responses(input_items))

        client = genai.Client(api_key=self._settings.gemini_api_key)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=self._contents,
                config={
                    "system_instruction": ASSISTANT_INSTRUCTIONS,
                    "tools": [{"function_declarations": self.function_definitions()}],
                },
            )
        except Exception as error:
            logger.warning("agent_provider_failure provider=gemini error_type=%s", type(error).__name__)
            raise AgentExecutionException(502, "provider_failed", "The research assistant provider could not complete the request.") from error

        candidate = response.candidates[0].content if getattr(response, "candidates", None) else None
        if candidate is not None:
            self._contents.append(candidate)
        calls = [
            ProviderToolCall(
                call_id=getattr(call, "id", None) or f"gemini-call-{uuid4().hex}",
                name=call.name,
                arguments=json.dumps(call.args or {}),
            )
            for call in (getattr(response, "function_calls", None) or [])
        ]
        return ProviderResponse(
            id=getattr(response, "response_id", None) or f"gemini-response-{uuid4().hex}",
            tool_calls=calls,
            output_text=getattr(response, "text", "") or "",
        )

    def preflight(self) -> AgentProviderDiagnosticRead:
        if not self.configured:
            return AgentProviderDiagnosticRead(ok=False, provider=self.provider, model=self.model, code="agent_unavailable", detail="Add a server-side Gemini API key before testing the provider.")
        from google import genai
        try:
            genai.Client(api_key=self._settings.gemini_api_key).models.generate_content(
                model=self.model, contents="Reply with OK.", config={"max_output_tokens": 4},
            )
        except Exception as error:
            code, detail = classify_provider_error(error)
            logger.warning("agent_provider_preflight_failed provider=gemini code=%s error_type=%s", code, type(error).__name__)
            return AgentProviderDiagnosticRead(ok=False, provider=self.provider, model=self.model, code=code, detail=detail)
        return AgentProviderDiagnosticRead(ok=True, provider=self.provider, model=self.model, detail="Gemini accepted a minimal server-side preflight request.")


class OllamaResearchAssistant:
    """Local Ollama chat provider using the shared read-only tool loop."""

    provider = "ollama"

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self.model = self._settings.ollama_model
        self._messages: list[dict[str, Any]] = []
        self._tool_rounds = 0
        self._executed_tool_names: set[str] = set()

    @property
    def configured(self) -> bool:
        return bool(self._settings.ollama_base_url and self.model)

    def function_definitions(self) -> list[dict[str, Any]]:
        return [
            {"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["parameters"]}}
            for tool in read_only_function_definitions()
        ]

    def _request(self, path: str, payload: Optional[dict[str, Any]] = None, method: str = "POST") -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        request = urllib_request.Request(
            f"{self._settings.ollama_base_url}{path}", data=body, method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib_request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib_error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            logger.warning("agent_provider_failure provider=ollama status=%s", error.code)
            raise AgentExecutionException(502, "provider_failed", f"Ollama rejected the request (HTTP {error.code}). Check that model '{self.model}' is installed.") from error
        except (urllib_error.URLError, TimeoutError, OSError) as error:
            logger.warning("agent_provider_failure provider=ollama error_type=%s", type(error).__name__)
            raise AgentExecutionException(503, "agent_unavailable", "Ollama is not reachable. Start Ollama locally and try again.") from error
        except (ValueError, json.JSONDecodeError) as error:
            raise AgentExecutionException(502, "provider_failed", "Ollama returned an invalid response.") from error

    def _initial_messages(self, input_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        messages = [{"role": "system", "content": ASSISTANT_INSTRUCTIONS}]
        messages.extend(
            {"role": item.get("role", "user"), "content": item.get("content", "")}
            for item in input_items if item.get("role") in {"user", "assistant"}
        )
        return messages

    def _deterministic_final_answer(self) -> str:
        """Build a safe final response when a small local model ignores the JSON schema."""
        successful: list[dict[str, Any]] = []
        evidence_ids: list[str] = []
        for message in self._messages:
            if message.get("role") != "tool":
                continue
            try:
                result = json.loads(message.get("content") or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(result, dict) or result.get("ok") is not True:
                continue
            audit_id = result.get("audit_tool_call_id")
            if isinstance(audit_id, str) and audit_id:
                evidence_ids.append(audit_id)
            successful.append({
                "tool_name": result.get("tool_name") or message.get("tool_name"),
                "data": result.get("data"),
            })
        if successful and evidence_ids:
            answer = format_tool_evidence(successful)
            final = AgentFinalAnswer(
                answer=answer,
                data_availability="retrieved",
                evidence_tool_call_ids=evidence_ids,
            )
        else:
            final = AgentFinalAnswer(
                answer="The required data is unavailable because the local assistant could not produce a valid response.",
                data_availability="unavailable",
                evidence_tool_call_ids=[],
            )
        return final.model_dump_json()

    @staticmethod
    def _is_usable_final_answer(content: str) -> bool:
        try:
            final = AgentFinalAnswer.model_validate_json(content)
        except Exception:
            return False
        # Small local models sometimes put the response envelope itself inside
        # ``answer``. It satisfies the schema but is not a user-facing answer.
        try:
            nested = json.loads(final.answer)
        except (TypeError, ValueError, json.JSONDecodeError):
            return True
        # JSON records belong in the evidence audit, never in the readable
        # answer. Reject both response envelopes and raw record arrays so the
        # deterministic, tool-specific presenter can summarize them.
        return not isinstance(nested, (dict, list))

    def respond(self, input_items: list[dict[str, Any]], previous_response_id: Optional[str] = None) -> ProviderResponse:
        if previous_response_id is None:
            self._messages = self._initial_messages(input_items)
            self._tool_rounds = 0
            self._executed_tool_names = set()
        else:
            self._tool_rounds += 1
            tool_messages = [
                {"role": "tool", "tool_name": item.get("name", "tool_result"), "content": item.get("output", "{}")}
                for item in input_items if item.get("type") == "function_call_output"
            ]
            self._executed_tool_names.update(message["tool_name"] for message in tool_messages)
            self._messages.extend(tool_messages)
            self._messages.append({
                "role": "user",
                "content": "Use the tool results above to answer. For every successful result (ok=true), set data_availability to retrieved and copy its audit_tool_call_id exactly into evidence_tool_call_ids. Return only the required JSON object.",
            })
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._messages,
            "stream": False,
        }
        if self._tool_rounds < 3:
            payload["tools"] = self.function_definitions()
        else:
            payload["format"] = AgentFinalAnswer.model_json_schema()
        response = self._request("/api/chat", payload)
        message = response.get("message") or {}
        self._messages.append(message)
        requested_names = {
            (call.get("function") or {}).get("name", "")
            for call in message.get("tool_calls") or []
        }
        if requested_names and requested_names.issubset(self._executed_tool_names):
            self._messages.append({
                "role": "user",
                "content": "Do not repeat a tool that already returned a result. Produce the final answer now from the successful tool evidence above, using its exact audit_tool_call_id values.",
            })
            response = self._request("/api/chat", {
                "model": self.model,
                "messages": self._messages,
                "format": AgentFinalAnswer.model_json_schema(),
                "stream": False,
            })
            message = response.get("message") or {}
            self._messages.append(message)
        if not message.get("tool_calls"):
            if not self._is_usable_final_answer(message.get("content") or ""):
                self._messages.append({
                    "role": "user",
                    "content": "Reformat your answer as the required JSON object. If successful tool data was used, set data_availability to retrieved and cite the exact audit_tool_call_id values from the tool results. Do not add markdown or commentary.",
                })
                response = self._request("/api/chat", {
                    "model": self.model,
                    "messages": self._messages,
                    "format": AgentFinalAnswer.model_json_schema(),
                    "stream": False,
                })
                message = response.get("message") or {}
                self._messages.append(message)
                if not self._is_usable_final_answer(message.get("content") or ""):
                    message = {"role": "assistant", "content": self._deterministic_final_answer()}
                    self._messages.append(message)
        calls = []
        for raw_call in message.get("tool_calls") or []:
            function = raw_call.get("function") or {}
            arguments = function.get("arguments") or {}
            calls.append(ProviderToolCall(
                call_id=raw_call.get("id") or f"ollama-call-{uuid4().hex}",
                name=function.get("name", ""),
                arguments=json.dumps(arguments) if isinstance(arguments, dict) else str(arguments),
            ))
        return ProviderResponse(
            id=response.get("created_at") or f"ollama-response-{uuid4().hex}",
            tool_calls=calls,
            output_text=message.get("content") or "",
        )

    def preflight(self) -> AgentProviderDiagnosticRead:
        try:
            response = self._request("/api/tags", method="GET")
        except AgentExecutionException as error:
            return AgentProviderDiagnosticRead(ok=False, provider=self.provider, model=self.model, code=error.code, detail=error.message)
        installed = {item.get("name", "").split(":latest")[0] for item in response.get("models", [])}
        if self.model not in installed and self.model.split(":latest")[0] not in installed:
            return AgentProviderDiagnosticRead(ok=False, provider=self.provider, model=self.model, code="model_unavailable", detail=f"Ollama is running, but model '{self.model}' is not installed. Run: ollama pull {self.model}")
        return AgentProviderDiagnosticRead(ok=True, provider=self.provider, model=self.model, detail="Ollama is running and the configured local model is installed.")


def classify_provider_error(error: Exception) -> tuple[str, str]:
    """Map provider failures to actionable, non-secret messages for the UI."""
    status_code = getattr(error, "code", None) or getattr(error, "status", None)
    # google-genai keeps the API response in ``message`` rather than always in str(error).
    message = " ".join(str(part) for part in (getattr(error, "message", ""), str(error))).casefold()
    if status_code == 401 or "api key" in message or "apikey" in message or "unauthenticated" in message:
        return "invalid_api_key", "Gemini rejected the API key. Create a Gemini API key in Google AI Studio and restart the backend after setting it."
    if status_code == 403 or "permission" in message or "forbidden" in message:
        return "project_permission_denied", "Google denied this project access. Check that the key belongs to a project allowed to use the Gemini API."
    if status_code == 429 or "quota" in message or "resource_exhausted" in message:
        return "provider_quota_exhausted", "Gemini quota is currently unavailable for this project or model. Check the Google AI Studio project quota and try later."
    if status_code == 404 or ("model" in message and ("not found" in message or "unsupported" in message)):
        return "model_unavailable", "The configured Gemini model is unavailable to this key. Choose a model available in Google AI Studio and restart the backend."
    if status_code == 400:
        return "invalid_provider_request", "Gemini rejected this connection request (HTTP 400). The API key may be invalid or restricted, or the selected model is not available to this project."
    return "provider_request_failed", "Gemini rejected the provider request. Use the server diagnostic result and verify the key, Google project permissions, and selected model."


def assistant_status(settings: Optional[Settings] = None) -> AgentStatusRead:
    selected_settings = settings or get_settings()
    try:
        provider = get_research_assistant(selected_settings)
    except AgentExecutionException as error:
        return AgentStatusRead(
            available=False,
            code=error.code,
            provider=selected_settings.agent_provider,
            model="unavailable",
            detail=error.message,
        )
    if not provider.configured:
        return AgentStatusRead(available=False, code="agent_unavailable", provider=provider.provider, model=provider.model,
            detail="The NMR research assistant is unavailable because its server-side provider key is not configured.")
    if isinstance(provider, OllamaResearchAssistant):
        diagnostic = provider.preflight()
        return AgentStatusRead(available=diagnostic.ok, code=diagnostic.code, provider=provider.provider, model=provider.model, detail=diagnostic.detail)
    return AgentStatusRead(available=True, provider=provider.provider, model=provider.model,
        detail="The selected NMR research assistant provider is configured.")


def provider_diagnostic(settings: Optional[Settings] = None) -> AgentProviderDiagnosticRead:
    provider = get_research_assistant(settings)
    if isinstance(provider, GeminiResearchAssistant):
        return provider.preflight()
    if isinstance(provider, OllamaResearchAssistant):
        return provider.preflight()
    if not provider.configured:
        return AgentProviderDiagnosticRead(ok=False, provider=provider.provider, model=provider.model, code="agent_unavailable", detail="Add the provider key before testing the connection.")
    return AgentProviderDiagnosticRead(ok=False, provider=provider.provider, model=provider.model, code="diagnostic_not_supported", detail="Connection diagnostics are not implemented for this provider.")


def get_research_assistant(settings: Optional[Settings] = None) -> NMRResearchAssistant:
    selected_settings = settings or get_settings()
    if selected_settings.agent_provider == "gemini":
        return GeminiResearchAssistant(selected_settings)
    if selected_settings.agent_provider == "openai":
        return OpenAIResponsesResearchAssistant(selected_settings)
    if selected_settings.agent_provider == "ollama":
        return OllamaResearchAssistant(selected_settings)
    raise AgentExecutionException(503, "agent_provider_unsupported", "The selected NMR research assistant provider is not supported.")


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
    from .agent_tools import TOOL_REGISTRY, ToolExecutionContext, ToolInvocationException, ToolInvocationRequest, error_response, invoke

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
        elif not tool.model_callable and (tool.confirmation_required or tool.side_effect != "none"):
            response = _tool_error(call.name, "tool_write_forbidden", "The research assistant may execute read-only tools only.")
        else:
            try:
                response = invoke(
                    db, user, call.name, ToolInvocationRequest(arguments=arguments, confirmed=False),
                    context=ToolExecutionContext(conversation_id=run.conversation_id, run_id=run.id),
                ).model_dump(mode="json")
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
    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "name": call.name,
        "output": json.dumps(response_for_model),
    }


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

    if not getattr(provider, "configured", True):
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
        if error.run_id is None:
            error.run_id = run.id
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
