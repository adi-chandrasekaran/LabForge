from __future__ import annotations

from backend.app import database
from backend.app.models import ChatChannel


def invoke(client, tool_name: str, arguments: dict | None = None, confirmed: bool = False):
    return client.post(
        f"/api/v1/agent/tools/{tool_name}/invoke",
        json={"arguments": arguments or {}, "confirmed": confirmed},
    )


def test_agent_tool_catalog_exposes_schemas_permissions_and_unavailable_tools(client) -> None:
    response = client.get("/api/v1/agent/tools")
    assert response.status_code == 200
    payload = response.json()

    tools = {tool["name"]: tool for tool in payload["tools"]}
    assert {"get_project", "get_experiment", "create_note"}.issubset(tools)
    assert tools["get_experiment"]["input_schema"]["required"] == ["experiment_id"]
    assert tools["create_note"]["confirmation_required"] is True
    assert tools["create_note"]["side_effect"].startswith("creates one ChatMessage")
    assert "properties" in tools["get_project"]["output_schema"]
    unavailable = {tool["name"] for tool in payload["unavailable_tools"]}
    assert {"get_sample", "get_spectrum", "calculate_chemical_shift_perturbation"}.issubset(unavailable)


def test_project_workflow_and_experiment_tools_return_structured_results(client) -> None:
    project = invoke(client, "get_project", {"project_id": "project-anc2"})
    assert project.status_code == 200
    assert project.json() == {
        "tool_name": "get_project",
        "ok": True,
        "data": project.json()["data"],
        "error": None,
    }
    assert project.json()["data"]["id"] == "project-anc2"

    workflows = invoke(client, "list_workflows", {"tag": "anc2"})
    assert workflows.status_code == 200
    assert workflows.json()["ok"] is True
    assert workflows.json()["data"]
    assert all("anc2" in workflow["tags"] for workflow in workflows.json()["data"])

    experiment_create = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "Agent tool snapshot",
            "experiment_date": "2026-09-14",
            "workflow_ids": ["workflow-anc2-batch-1"],
            "notes": "Need an agent-visible note.",
        },
    )
    assert experiment_create.status_code == 201
    experiment = experiment_create.json()

    fetched = invoke(client, "get_experiment", {"experiment_id": experiment["id"]})
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == experiment["id"]

    workflow_run = experiment["workflow_runs"][0]
    step_run = workflow_run["step_runs"][0]
    nested = invoke(
        client,
        "get_experiment_run_step",
        {
            "experiment_id": experiment["id"],
            "workflow_run_id": workflow_run["id"],
            "step_run_id": step_run["id"],
        },
    )
    assert nested.status_code == 200
    assert nested.json()["data"]["id"] == step_run["id"]


def test_note_search_validation_and_deterministic_errors(client) -> None:
    created = client.post(
        "/api/v1/experiments",
        json={
            "project_id": "project-anc2",
            "title": "Search target",
            "experiment_date": "2026-09-14",
            "notes": "Alpha shift review is pending.",
        },
    )
    assert created.status_code == 201

    search = invoke(client, "search_experiment_notes", {"query": "ALPHA", "limit": 1})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["data"]] == [created.json()["id"]]

    invalid = invoke(client, "search_experiment_notes", {"query": "", "limit": 101})
    assert invalid.status_code == 422
    assert invalid.json()["ok"] is False
    assert invalid.json()["error"]["code"] == "invalid_input"
    assert invalid.json()["error"]["details"]

    invalid_envelope = client.post("/api/v1/agent/tools/list_projects/invoke", json={"confirmed": "yes"})
    assert invalid_envelope.status_code == 422
    assert invalid_envelope.json()["error"]["code"] == "invalid_invocation"

    missing = invoke(client, "get_experiment", {"experiment_id": "experiment-missing"})
    assert missing.status_code == 404
    assert missing.json()["error"] == {
        "code": "not_found",
        "message": "Experiment not found",
        "details": None,
    }

    unavailable = invoke(client, "get_spectrum")
    assert unavailable.status_code == 501
    assert unavailable.json()["error"]["code"] == "tool_unavailable"

    unknown = invoke(client, "does_not_exist")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "tool_not_found"


def test_chat_tools_enforce_lab_scope_and_confirmed_note_creation(client) -> None:
    channels = invoke(client, "list_chat_channels")
    assert channels.status_code == 200
    assert all(channel["lab_id"] == "local-lab" for channel in channels.json()["data"])

    before = invoke(client, "list_channel_messages", {"channel_id": "channel-general"})
    assert before.status_code == 200
    before_count = len(before.json()["data"])

    unconfirmed = invoke(
        client,
        "create_note",
        {"channel_id": "channel-general", "body": "Do not persist this note."},
    )
    assert unconfirmed.status_code == 409
    assert unconfirmed.json()["error"]["code"] == "confirmation_required"

    after_unconfirmed = invoke(client, "list_channel_messages", {"channel_id": "channel-general"})
    assert len(after_unconfirmed.json()["data"]) == before_count

    created = invoke(
        client,
        "create_note",
        {
            "channel_id": "channel-general",
            "body": "Confirmed agent note.",
            "referenced_workflow_id": "workflow-anc2-batch-1",
        },
        confirmed=True,
    )
    assert created.status_code == 200
    assert created.json()["data"]["body"] == "Confirmed agent note."
    assert created.json()["data"]["author_id"] == "user-dev-chen"
    assert created.json()["data"]["referenced_workflow_id"] == "workflow-anc2-batch-1"

    with database.SessionLocal() as db:
        db.add(
            ChatChannel(
                id="channel-foreign-agent-tool",
                lab_id="other-lab",
                name="foreign-agent-tool",
                topic="not visible",
                created_by_id="user-pi-ferretti",
            )
        )
        db.commit()

    foreign = invoke(client, "list_channel_messages", {"channel_id": "channel-foreign-agent-tool"})
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "not_found"
