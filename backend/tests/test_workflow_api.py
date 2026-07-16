from backend.app import database
from backend.app.models import User


def _workflow_by_title(workflows: list[dict], title: str) -> dict:
    return next(workflow for workflow in workflows if workflow["title"] == title)


def test_seeded_anc2_workflows_are_listed(client) -> None:
    response = client.get("/api/v1/workflows?tag=anc2")
    assert response.status_code == 200
    workflows = response.json()
    titles = {workflow["title"] for workflow in workflows}
    assert "ANC2 Batch 1" in titles
    assert "ANC2 Batch 2" in titles

    batch_1 = _workflow_by_title(workflows, "ANC2 Batch 1")
    assert len(batch_1["steps"]) == 13
    assert batch_1["steps"][4]["label"] == "Dialysis"


def test_workflow_step_crudl_and_reorder(client) -> None:
    workflow_id = "workflow-anc2-batch-1"

    create_response = client.post(
        f"/api/v1/workflows/{workflow_id}/steps",
        json={
            "after_step_id": "b1-01",
            "label": "PR2 Inserted Step",
            "sublabel": "API test",
            "status_template": "pending",
            "duration": "30 min",
            "procedure_markdown": "Test insert",
            "inputs": [],
            "parameters": [],
            "outputs": [],
            "notes": "Inserted by test",
        },
    )
    assert create_response.status_code == 201
    workflow = create_response.json()
    inserted = next(step for step in workflow["steps"] if step["label"] == "PR2 Inserted Step")
    assert inserted["order_index"] == 2

    update_response = client.patch(
        f"/api/v1/workflows/{workflow_id}/steps/{inserted['id']}",
        json={
            "label": "PR2 Edited Step",
            "sublabel": "API test updated",
            "status_template": "running",
            "duration": "45 min",
            "procedure_markdown": "Edited",
            "inputs": [{"name": "Input A", "type": "sample", "value": "5 mL"}],
            "parameters": [{"label": "Temp", "value": "4 C"}],
            "outputs": [{"name": "Output A", "type": "sample"}],
            "notes": "Edited by test",
        },
    )
    assert update_response.status_code == 200
    workflow = update_response.json()
    edited = next(step for step in workflow["steps"] if step["id"] == inserted["id"])
    assert edited["label"] == "PR2 Edited Step"
    assert edited["status_template"] == "running"

    reorder_response = client.post(
        f"/api/v1/workflows/{workflow_id}/steps/reorder",
        json={
            "ordered_step_ids": [step["id"] for step in workflow["steps"][1:]] + [workflow["steps"][0]["id"]],
        },
    )
    assert reorder_response.status_code == 200
    reordered = reorder_response.json()["steps"]
    assert reordered[-1]["id"] == "b1-01"

    delete_response = client.delete(f"/api/v1/workflows/{workflow_id}/steps/{inserted['id']}")
    assert delete_response.status_code == 200
    labels = {step["label"] for step in delete_response.json()["steps"]}
    assert "PR2 Edited Step" not in labels


def test_branch_creation_branch_steps_and_branch_delete(client) -> None:
    workflow_id = "workflow-anc2-batch-1"
    create_branch = client.post(
        f"/api/v1/workflows/{workflow_id}/branches",
        json={"anchor_step_id": "b1-02", "label": "Troubleshooting Run"},
    )
    assert create_branch.status_code == 201
    workflow = create_branch.json()
    sup1 = next(step for step in workflow["steps"] if step["id"] == "b1-02")
    assert sup1["branch_tracks"][0]["label"] == "Troubleshooting Run"
    branch_id = sup1["branch_tracks"][0]["id"]

    add_branch_step = client.post(
        f"/api/v1/workflows/{workflow_id}/branches/{branch_id}/steps",
        json={
            "label": "Repeat Clarification",
            "sublabel": "Branch step",
            "status_template": "pending",
            "duration": "20 min",
            "procedure_markdown": "Repeat the clarification spin.",
            "inputs": [],
            "parameters": [],
            "outputs": [],
            "notes": "Branch work",
        },
    )
    assert add_branch_step.status_code == 201
    workflow = add_branch_step.json()
    sup1 = next(step for step in workflow["steps"] if step["id"] == "b1-02")
    assert sup1["branch_tracks"][0]["steps"][0]["label"] == "Repeat Clarification"

    delete_branch = client.delete(f"/api/v1/workflows/{workflow_id}/branches/{branch_id}")
    assert delete_branch.status_code == 200
    sup1 = next(step for step in delete_branch.json()["steps"] if step["id"] == "b1-02")
    assert sup1["branch_tracks"] == []


def test_publish_requires_allowed_role(client) -> None:
    workflow_id = "workflow-anc2-batch-2"
    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        user.role = "student"
        db.commit()

    forbidden = client.post(f"/api/v1/workflows/{workflow_id}/publish")
    assert forbidden.status_code == 403

    with database.SessionLocal() as db:
        user = db.get(User, "user-dev-chen")
        user.role = "professor"
        db.commit()

    allowed = client.post(f"/api/v1/workflows/{workflow_id}/publish")
    assert allowed.status_code == 200
    assert allowed.json()["library_state"] == "published"
    assert allowed.json()["visibility"] == "library"
