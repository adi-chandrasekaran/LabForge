from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

import json

from backend.app.agent_research import (
    AgentExecutionException,
    AgentFinalAnswer,
    AgentRunCreate,
    OpenAIResponsesResearchAssistant,
    ProviderResponse,
    ProviderToolCall,
    execute_run,
)
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
        "provider": "openai",
        "model": "gpt-5.5",
        "detail": "The NMR research assistant is unavailable because its server-side provider key is not configured.",
    }
    assert "key" not in response.text.casefold() or "configured" in response.text.casefold()


def test_read_only_function_catalog_preserves_agent_tool_definitions() -> None:
    assistant = OpenAIResponsesResearchAssistant(Settings(openai_api_key="test-secret", agent_model="test-model"))
    functions = assistant.function_definitions()
    names = {item["name"] for item in functions}

    assert assistant.configured is True
    assert assistant.model == "test-model"
    assert {"get_project", "list_experiments", "search_experiment_notes"}.issubset(names)
    assert "create_note" not in names
    assert "get_spectrum" not in names
    get_project = next(item for item in functions if item["name"] == "get_project")
    assert get_project["strict"] is True
    assert get_project["parameters"]["properties"]["project_id"]["minLength"] == 1


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
        ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="get_spectrum", arguments="{}")]),
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
