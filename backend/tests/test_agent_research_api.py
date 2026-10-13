from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

import json
import copy
from types import SimpleNamespace

from backend.app.agent_research import (
    AgentExecutionException,
    AgentFinalAnswer,
    AgentRunCreate,
    GeminiResearchAssistant,
    OllamaResearchAssistant,
    OpenAIResponsesResearchAssistant,
    ProviderResponse,
    ProviderToolCall,
    assistant_status,
    classify_provider_error,
    execute_run,
    guided_tool_names,
)


@pytest.mark.parametrize(("message", "expected"), [
    ("401 API key not valid", "invalid_api_key"),
    ("403 permission denied", "project_permission_denied"),
    ("429 quota exhausted", "provider_quota_exhausted"),
    ("model not found", "model_unavailable"),
])
def test_gemini_error_classification_is_actionable_and_safe(message: str, expected: str) -> None:
    code, detail = classify_provider_error(Exception(message))
    assert code == expected
    assert "test-secret" not in detail


def test_gemini_error_classification_uses_structured_client_status() -> None:
    class ProviderError(Exception):
        code = 403
        message = "opaque"
    assert classify_provider_error(ProviderError())[0] == "project_permission_denied"


def test_provider_diagnostic_requires_no_key(client: TestClient) -> None:
    response = client.post("/api/v1/agent/provider-diagnostic")
    assert response.status_code == 200
    assert response.json()["code"] == "agent_unavailable"
from backend.app.config import Settings
from backend.app import database
from backend.app.models import AgentRun, AgentToolCall, User


class ScriptedProvider:
    provider = "fake"
    model = "fake-model"

    def __init__(self, responses):
        self.responses = list(responses)
        self.inputs = []

    def function_definitions(self):
        return []

    def respond(self, input_items, previous_response_id=None):
        self.inputs.append((input_items, previous_response_id))
        response = self.responses.pop(0)
        return response(input_items, previous_response_id) if callable(response) else response


def test_agent_status_is_safe_when_key_is_not_configured(client: TestClient) -> None:
    response = client.get("/api/v1/agent/status")

    assert response.status_code == 200
    assert response.json() == {
        "available": False,
        "code": "agent_unavailable",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "detail": "The NMR research assistant is unavailable because its server-side provider key is not configured.",
    }
    assert "key" not in response.text.casefold() or "configured" in response.text.casefold()


def test_read_only_function_catalog_preserves_agent_tool_definitions() -> None:
    assistant = OpenAIResponsesResearchAssistant(Settings(openai_api_key="test-secret", agent_model="test-model"))
    functions = assistant.function_definitions()
    names = {item["name"] for item in functions}

    assert assistant.configured is True
    assert assistant.model == "test-model"
    assert {"get_project", "list_experiments", "search_experiment_notes", "get_sample", "get_spectrum", "calculate_chemical_shift_perturbation"}.issubset(names)
    assert "create_note" not in names
    assert "get_spectrum" in names
    get_project = next(item for item in functions if item["name"] == "get_project")
    assert get_project["strict"] is True
    assert get_project["parameters"]["properties"]["project_id"]["minLength"] == 1


def test_gemini_provider_translates_the_read_only_catalog_and_messages() -> None:
    assistant = GeminiResearchAssistant(Settings(gemini_api_key="test-secret", gemini_model="test-gemini"))
    functions = assistant.function_definitions()
    names = {item["name"] for item in functions}

    assert assistant.configured is True
    assert assistant.model == "test-gemini"
    assert "get_project" in names
    assert "create_note" not in names
    get_project = next(item for item in functions if item["name"] == "get_project")
    assert get_project["parameters_json_schema"]["properties"]["project_id"]["minLength"] == 1
    assert assistant._initial_contents([
        {"role": "user", "content": "Find ANC2"},
        {"role": "assistant", "content": "I will retrieve it."},
    ]) == [
        {"role": "user", "parts": [{"text": "Find ANC2"}]},
        {"role": "model", "parts": [{"text": "I will retrieve it."}]},
    ]
    responses = assistant._function_responses([{
        "type": "function_call_output",
        "name": "get_project",
        "output": '{"tool_name":"get_project","ok":true}',
    }])
    assert responses[0]["parts"][0]["function_response"]["name"] == "get_project"


def test_gemini_provider_maps_function_calls_and_results(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = []

    class FakeModels:
        def generate_content(self, **request):
            captured.append(copy.deepcopy(request))
            return SimpleNamespace(
                response_id="gemini-response-1",
                candidates=[SimpleNamespace(content={"role": "model", "parts": []})],
                function_calls=[SimpleNamespace(id="gemini-call-1", name="get_project", args={"project_id": "project-anc2"})],
                text="",
            )

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr("google.genai.Client", lambda api_key: FakeClient())
    assistant = GeminiResearchAssistant(Settings(gemini_api_key="test-secret"))
    first = assistant.respond([{"role": "user", "content": "Get ANC2"}])
    second = assistant.respond([{
        "type": "function_call_output",
        "call_id": first.tool_calls[0].call_id,
        "name": "get_project",
        "output": '{"tool_name":"get_project","ok":true}',
    }], previous_response_id=first.id)

    assert first.tool_calls[0].name == "get_project"
    assert second.id == "gemini-response-1"
    assert captured[0]["config"]["tools"][0]["function_declarations"]
    assert captured[1]["contents"][-1]["parts"][0]["function_response"]["name"] == "get_project"


def test_ollama_provider_maps_tools_messages_and_results(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="qwen3:4b"))
    requests = []
    responses = [
        {"created_at": "response-1", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_project", "arguments": {"project_id": "project-anc2"}}}]}},
        {"created_at": "response-2", "message": {"role": "assistant", "content": '{"answer":"ANC2 retrieved","data_availability":"retrieved","evidence_tool_call_ids":["call-1"]}'}},
    ]
    def fake_request(path, payload=None, method="POST"):
        requests.append(copy.deepcopy((path, payload, method)))
        return responses.pop(0)
    monkeypatch.setattr(assistant, "_request", fake_request)

    first = assistant.respond([{"role": "user", "content": "Find ANC2"}])
    second = assistant.respond([{"type": "function_call_output", "name": "get_project", "output": '{"ok":true}'}], first.id)

    assert assistant.configured is True
    assert first.tool_calls[0].name == "get_project"
    assert json.loads(first.tool_calls[0].arguments) == {"project_id": "project-anc2"}
    assert second.output_text.startswith('{"answer"')
    assert requests[0][1]["tools"][0]["function"]["parameters"]
    assert requests[1][1]["messages"][-2] == {"role": "tool", "tool_name": "get_project", "content": '{"ok":true}'}
    assert requests[1][1]["messages"][-1]["role"] == "user"


def test_ollama_preflight_reports_model_install_state(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="qwen3:4b"))
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: {"models": [{"name": "qwen3:4b"}]})
    assert assistant.preflight().ok is True
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: {"models": []})
    result = assistant.preflight()
    assert result.ok is False
    assert result.code == "model_unavailable"
    assert "ollama pull qwen3:4b" in result.detail


def test_ollama_status_uses_live_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(OllamaResearchAssistant, "_request", lambda *args, **kwargs: {"models": [{"name": "llama3.2:latest"}]})
    result = assistant_status(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    assert result.available is True
    assert result.provider == "ollama"
    assert result.model == "llama3.2"


def test_ollama_stops_duplicate_tool_loops_and_forces_final_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    requests = []
    responses = [
        {"created_at": "one", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "list_projects", "arguments": {}}}]}},
        {"created_at": "two", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "list_projects", "arguments": {}}}]}},
        {"created_at": "three", "message": {"role": "assistant", "content": '{"answer":"ANC2","data_availability":"retrieved","evidence_tool_call_ids":["audit-1"]}'}},
    ]
    def fake_request(path, payload=None, method="POST"):
        requests.append(copy.deepcopy(payload))
        return responses.pop(0)
    monkeypatch.setattr(assistant, "_request", fake_request)

    first = assistant.respond([{"role": "user", "content": "List projects"}])
    second = assistant.respond([{"type": "function_call_output", "name": "list_projects", "output": '{"ok":true,"audit_tool_call_id":"audit-1"}'}], first.id)

    assert second.tool_calls == []
    assert AgentFinalAnswer.model_validate_json(second.output_text).evidence_tool_call_ids == ["audit-1"]
    assert "tools" in requests[0] and "tools" in requests[1]
    assert "tools" not in requests[2]
    assert requests[2]["format"]["properties"]["answer"]


@pytest.mark.parametrize(("message", "expected"), [
    ("List my HSQC spectra", {"list_spectra", "get_spectrum", "list_samples"}),
    ("What shifts are stored for residue M1?", {"list_proteins", "find_residue", "list_spectra", "get_residue_shifts"}),
    ("Show the assignments for this peak", {"list_spectra", "list_peaks", "get_peak_assignments"}),
    ("Compare these spectra and calculate CSP", {"list_spectra", "compare_spectra", "calculate_chemical_shift_perturbation"}),
])
def test_guided_tool_names_include_nmr_discovery_chains(message: str, expected: set[str]) -> None:
    assert expected.issubset(guided_tool_names(message))


def test_ollama_allows_same_tool_with_different_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    responses = [
        {"created_at": "one", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_spectrum", "arguments": {"spectrum_id": "spectrum-a"}}}]}},
        {"created_at": "two", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_spectrum", "arguments": {"spectrum_id": "spectrum-b"}}}]}},
    ]
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: responses.pop(0))

    first = assistant.respond([{"role": "user", "content": "Compare spectra A and B"}])
    second = assistant.respond([{
        "type": "function_call_output", "name": "get_spectrum", "output": '{"ok":true,"audit_tool_call_id":"audit-a"}',
    }], first.id)

    assert second.tool_calls[0].name == "get_spectrum"
    assert json.loads(second.tool_calls[0].arguments) == {"spectrum_id": "spectrum-b"}


def test_ollama_sends_only_request_relevant_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    captured = []
    monkeypatch.setattr(assistant, "_request", lambda _path, payload, **_kwargs: captured.append(payload) or {
        "created_at": "one", "message": {"role": "assistant", "content": '{"answer":"General guidance only.","data_availability":"general_guidance","evidence_tool_call_ids":[]}'},
    })

    assistant.respond([{"role": "user", "content": "Show shifts for residue M1"}])

    names = {tool["function"]["name"] for tool in captured[0]["tools"]}
    assert names == {"list_proteins", "find_residue", "list_spectra", "get_residue_shifts"}


def test_ollama_falls_back_to_successful_tool_data_after_invalid_repairs(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    responses = [
        {"created_at": "one", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "list_projects", "arguments": {}}}]}},
        {"created_at": "two", "message": {"role": "assistant", "content": "Here are your projects."}},
        {"created_at": "three", "message": {"role": "assistant", "content": "Still not JSON."}},
    ]
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: responses.pop(0))

    first = assistant.respond([{"role": "user", "content": "List projects"}])
    second = assistant.respond([{
        "type": "function_call_output",
        "name": "list_projects",
        "output": '{"tool_name":"list_projects","ok":true,"data":[{"title":"ANC2","code":"ANC2","status":"active"}],"audit_tool_call_id":"audit-1"}',
    }], first.id)

    answer = AgentFinalAnswer.model_validate_json(second.output_text)
    assert answer.data_availability == "retrieved"
    assert answer.evidence_tool_call_ids == ["audit-1"]
    assert "ANC2" in answer.answer


def test_ollama_rejects_nested_metadata_as_the_user_facing_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    nested_answer = json.dumps({
        "answer": json.dumps({"data_availability": "retrieved", "evidence_tool_call_ids": ["audit-1"]}),
        "data_availability": "retrieved",
        "evidence_tool_call_ids": ["audit-1"],
    })
    responses = [
        {"created_at": "one", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "list_projects", "arguments": {}}}]}},
        {"created_at": "two", "message": {"role": "assistant", "content": nested_answer}},
        {"created_at": "three", "message": {"role": "assistant", "content": nested_answer}},
    ]
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: responses.pop(0))

    first = assistant.respond([{"role": "user", "content": "List projects"}])
    second = assistant.respond([{
        "type": "function_call_output",
        "name": "list_projects",
        "output": '{"tool_name":"list_projects","ok":true,"data":[{"title":"ANC2","code":"ANC2","status":"active"}],"audit_tool_call_id":"audit-1"}',
    }], first.id)

    answer = AgentFinalAnswer.model_validate_json(second.output_text)
    assert answer.answer.startswith("I found 1 project:")
    assert "ANC2" in answer.answer


def test_ollama_rejects_raw_record_array_as_the_user_facing_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = OllamaResearchAssistant(Settings(agent_provider="ollama", ollama_model="llama3.2"))
    raw_answer = json.dumps({
        "answer": json.dumps([{"id": "project-anc2", "title": "ANC2", "owner_id": "user-dev-chen"}]),
        "data_availability": "retrieved",
        "evidence_tool_call_ids": ["audit-1"],
    })
    responses = [
        {"created_at": "one", "message": {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "list_projects", "arguments": {}}}]}},
        {"created_at": "two", "message": {"role": "assistant", "content": raw_answer}},
        {"created_at": "three", "message": {"role": "assistant", "content": raw_answer}},
    ]
    monkeypatch.setattr(assistant, "_request", lambda *args, **kwargs: responses.pop(0))

    first = assistant.respond([{"role": "user", "content": "List projects"}])
    second = assistant.respond([{
        "type": "function_call_output",
        "name": "list_projects",
        "output": '{"tool_name":"list_projects","ok":true,"data":[{"title":"ANC2","code":"ANC2","status":"active"}],"audit_tool_call_id":"audit-1"}',
    }], first.id)

    answer = AgentFinalAnswer.model_validate_json(second.output_text)
    assert answer.answer == "I found 1 project:\n- ANC2 (ANC2) — active; 0 experiments, 0 workflows"
    assert "owner_id" not in answer.answer


def test_conversation_and_empty_audit_history_are_owned(client: TestClient) -> None:
    created = client.post("/api/v1/agent/conversations", json={"title": "HSQC review"})
    assert created.status_code == 201
    conversation = created.json()
    assert conversation["title"] == "HSQC review"

    fetched = client.get(f"/api/v1/agent/conversations/{conversation['id']}")
    runs = client.get(f"/api/v1/agent/conversations/{conversation['id']}/runs")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == conversation["id"]
    assert runs.status_code == 200
    assert runs.json() == []


def test_conversation_rejects_unknown_or_empty_title(client: TestClient) -> None:
    assert client.get("/api/v1/agent/conversations/missing").status_code == 404
    assert client.post("/api/v1/agent/conversations", json={"title": ""}).status_code == 422


def test_run_audit_serializes_tool_calls_in_sequence(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Audit"}).json()
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        run = AgentRun(
            id="agent-run-test",
            conversation_id=conversation["id"],
            user_request="Which project is active?",
            provider="openai",
            model="gpt-5.5",
            status="completed",
            final_answer="The project is active.",
            data_availability="retrieved",
            evidence_tool_call_ids=["tool-call-2"],
        )
        db.add(run)
        db.add_all([
            AgentToolCall(id="tool-call-2", run_id=run.id, sequence=2, tool_name="get_project", arguments={"project_id": "project-1"}, result={"ok": True}, status="completed"),
            AgentToolCall(id="tool-call-1", run_id=run.id, sequence=1, tool_name="list_projects", arguments={}, result={"ok": True}, status="completed"),
        ])
        assert user is not None
        db.commit()

    response = client.get(f"/api/v1/agent/conversations/{conversation['id']}/runs/agent-run-test")
    assert response.status_code == 200
    assert [call["id"] for call in response.json()["tool_calls"]] == ["tool-call-1", "tool-call-2"]


def test_final_answer_schema_requires_retrieved_evidence_and_unavailable_wording() -> None:
    with pytest.raises(ValidationError):
        AgentFinalAnswer(answer="The project is active.", data_availability="retrieved")
    with pytest.raises(ValidationError):
        AgentFinalAnswer(answer="I cannot find the spectrum.", data_availability="unavailable")

    answer = AgentFinalAnswer(
        answer="The required spectrum data is unavailable in this notebook.",
        data_availability="unavailable",
    )
    assert answer.evidence_tool_call_ids == []


def test_execution_loop_persists_tool_audit_and_returns_results_to_next_turn(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Execution"}).json()
    provider = ScriptedProvider([
        ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="get_project", arguments='{"project_id":"project-anc2"}')]),
        ProviderResponse(id="response-2", output_text=json.dumps({
            "answer": "The retrieved project is ANC2.",
            "data_availability": "retrieved",
            "evidence_tool_call_ids": [],
        })),
    ])
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        with pytest.raises(AgentExecutionException, match="invalid final response"):
            execute_run(db, user, conversation["id"], AgentRunCreate(message="Which project is ANC2?"), provider)

        failed = db.scalar(select(AgentRun).where(AgentRun.conversation_id == conversation["id"]))
        assert failed.status == "failed"
        assert failed.tool_calls[0].tool_name == "get_project"
        assert json.loads(provider.inputs[1][0][0]["output"])["audit_tool_call_id"] == failed.tool_calls[0].id


def test_execution_loop_rejects_write_tool_and_marks_run_failed(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Write rejection"}).json()
    provider = ScriptedProvider([
        ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="create_note", arguments='{"channel_id":"channel-general","body":"no"}')]),
        ProviderResponse(id="response-2", output_text="not json"),
    ])
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        with pytest.raises(AgentExecutionException) as error:
            execute_run(db, user, conversation["id"], AgentRunCreate(message="Write a note"), provider)
        assert error.value.code == "invalid_final_response"
        run = db.scalar(select(AgentRun).where(AgentRun.conversation_id == conversation["id"]))
        assert run.tool_calls[0].error_code == "tool_write_forbidden"


def test_execution_loop_returns_unknown_tool_error_to_provider(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Unknown tool"}).json()
    provider = ScriptedProvider([
        ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="does_not_exist", arguments="{}")]),
        ProviderResponse(id="response-2", output_text="not json"),
    ])
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        with pytest.raises(AgentExecutionException):
            execute_run(db, user, conversation["id"], AgentRunCreate(message="Get a spectrum"), provider)
        run = db.scalar(select(AgentRun).where(AgentRun.conversation_id == conversation["id"]))
        assert run.tool_calls[0].error_code == "tool_not_allowed"


def test_execution_loop_accepts_successful_retrieval_evidence(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Evidence"}).json()

    def final_response(inputs, _previous_response_id):
        audit_id = json.loads(inputs[0]["output"])["audit_tool_call_id"]
        return ProviderResponse(id="response-2", output_text=json.dumps({
            "answer": "The retrieved project is ANC2.",
            "data_availability": "retrieved",
            "evidence_tool_call_ids": [audit_id],
        }))

    provider = ScriptedProvider([
        ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="get_project", arguments='{"project_id":"project-anc2"}')]),
        final_response,
    ])
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        run = execute_run(db, user, conversation["id"], AgentRunCreate(message="Which project is ANC2?"), provider)
        assert run.status == "completed"
        assert run.evidence_tool_call_ids == [run.tool_calls[0].id]


def test_run_endpoint_persists_agent_unavailable_failure(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "No provider"}).json()
    response = client.post(f"/api/v1/agent/conversations/{conversation['id']}/runs", json={"message": "Which project is ANC2?"})

    assert response.status_code == 503
    assert response.json()["code"] == "agent_unavailable"
    run = client.get(f"/api/v1/agent/conversations/{conversation['id']}/runs/{response.json()['run_id']}")
    assert run.status_code == 200
    assert run.json()["status"] == "failed"


def test_provider_failure_keeps_the_persisted_run_reference(client: TestClient) -> None:
    class FailingProvider:
        provider = "fake"
        model = "fake-model"
        configured = True

        def function_definitions(self):
            return []

        def respond(self, input_items, previous_response_id=None):
            raise AgentExecutionException(502, "provider_failed", "The provider rejected the request.")

    conversation = client.post("/api/v1/agent/conversations", json={"title": "Provider failure"}).json()
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        with pytest.raises(AgentExecutionException) as error:
            execute_run(db, user, conversation["id"], AgentRunCreate(message="Which project is ANC2?"), FailingProvider())
        assert error.value.run_id is not None
