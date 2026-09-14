from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.agent_research import AgentFinalAnswer, OpenAIResponsesResearchAssistant
from backend.app.config import Settings
from backend.app import database
from backend.app.models import AgentRun, AgentToolCall, User


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
