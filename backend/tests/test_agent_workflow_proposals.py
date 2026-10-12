from fastapi.testclient import TestClient

from backend.app.agent_research import ProviderResponse, ProviderToolCall, execute_run
from backend.app.agent_tools import ToolInvocationRequest, invoke
from backend.app.deps import get_current_user


def test_proposal_tool_requires_agent_run_context(client: TestClient) -> None:
    response = client.post("/api/v1/agent/tools/propose_workflow_change/invoke", json={
        "arguments": {"operation": "create_workflow", "payload": {"title": "No direct proposal"}},
        "confirmed": False,
    })
    assert response.status_code == 409


class ProposalProvider:
    provider = "test"; model = "test"; configured = True
    def function_definitions(self): return []
    def __init__(self): self.turn = 0
    def respond(self, inputs, previous_response_id):
        self.turn += 1
        if self.turn == 1:
            return ProviderResponse(id="response-1", tool_calls=[ProviderToolCall(call_id="call-1", name="propose_workflow_change", arguments='{"operation":"create_workflow","payload":{"title":"Agent draft"}}')], output_text="")
        audit_id = __import__("json").loads(inputs[0]["output"])["audit_tool_call_id"]
        return ProviderResponse(id="response-2", output_text='{"answer":"I prepared a draft for review.","data_availability":"general_guidance","evidence_tool_call_ids":[]}')


def test_agent_can_prepare_but_not_apply_workflow_draft(client: TestClient) -> None:
    conversation = client.post("/api/v1/agent/conversations", json={"title": "Draft"}).json()
    from backend.app import database
    from backend.app.agent_research import AgentRunCreate
    db = database.SessionLocal()
    try:
        user = get_current_user(db)
        run = execute_run(db, user, conversation["id"], AgentRunCreate(message="Make a workflow"), assistant=ProposalProvider())
        call = run.tool_calls[0]
        assert call.result["ok"] is True, call.result
        draft_id = call.result["data"]["id"]
        assert client.get(f"/api/v1/agent/workflow-drafts/{draft_id}").json()["status"] == "pending"
        assert "Agent draft" not in [workflow["title"] for workflow in client.get("/api/v1/workflows").json()]
    finally:
        db.close()
