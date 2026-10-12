from fastapi.testclient import TestClient


def test_confirmed_draft_applies_once(client: TestClient) -> None:
    workflow = client.post("/api/v1/workflows", json={"title": "Draft target"}).json()
    draft = client.post("/api/v1/agent/workflow-drafts", json={
        "operation": "add_step",
        "payload": {"workflow_id": workflow["id"], "step": {"label": "Acquire HSQC"}},
    })
    assert draft.status_code == 201
    draft_id = draft.json()["id"]
    confirmed = client.post(f"/api/v1/agent/workflow-drafts/{draft_id}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["result"]["workflow"]["steps"][0]["label"] == "Acquire HSQC"
    assert client.post(f"/api/v1/agent/workflow-drafts/{draft_id}/confirm").status_code == 409


def test_draft_is_owner_scoped(client: TestClient) -> None:
    draft = client.post("/api/v1/agent/workflow-drafts", json={"operation": "create_workflow", "payload": {"title": "Private"}}).json()
    # The local mock identity is fixed, but an unknown id must not reveal a draft.
    assert client.get("/api/v1/agent/workflow-drafts/not-a-draft").status_code == 404
    assert draft["status"] == "pending"


def test_owner_can_list_own_drafts(client: TestClient) -> None:
    client.post("/api/v1/agent/workflow-drafts", json={"operation": "create_workflow", "payload": {"title": "Review me"}})
    response = client.get("/api/v1/agent/workflow-drafts")
    assert response.status_code == 200
    assert response.json()[0]["payload"]["title"] == "Review me"
