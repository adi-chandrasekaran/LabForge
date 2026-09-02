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
    assert any(member["workflow_role"] == "owner" for member in batch_1["members"])
    assert any(member["workflow_role"] == "editor" for member in batch_1["members"])


def test_standardized_workflow_filters_and_memberships(client) -> None:
    response = client.get("/api/v1/workflows?tag=standardized&library_state=published&visibility=library")
    assert response.status_code == 200
    workflows = response.json()
    titles = {workflow["title"] for workflow in workflows}
    assert "Reverse Nickel Chromatography" in titles
    assert "Ion Exchange Chromatography" in titles
    reverse_nickel = _workflow_by_title(workflows, "Reverse Nickel Chromatography")
    assert any(member["workflow_role"] == "owner" for member in reverse_nickel["members"])
    assert any(member["workflow_role"] == "editor" for member in reverse_nickel["members"])


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


def test_blank_project_workflow_can_receive_first_rich_step(client) -> None:
    project_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Blank Workflow Backend Test",
            "code": "BLANK-BACKEND-TEST",
            "description": "Blank workflow authoring coverage.",
            "status": "active",
            "tags": ["blank-workflow-test"],
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()

    workflows_response = client.get(f"/api/v1/workflows?project_id={project['id']}")
    assert workflows_response.status_code == 200
    workflows = workflows_response.json()
    assert len(workflows) == 1
    workflow = workflows[0]
    assert workflow["steps"] == []

    step_response = client.post(
        f"/api/v1/workflows/{workflow['id']}/steps",
        json={
            "after_step_id": None,
            "label": "Prepare starter culture",
            "sublabel": "overnight growth",
            "status_template": "running",
            "duration": "16 hr",
            "procedure_markdown": "Inoculate LB antibiotic media and grow overnight at 37 C.",
            "inputs": [{"name": "picked colony", "type": "sample", "value": "1 colony"}],
            "parameters": [{"label": "Temperature", "value": "37 C"}],
            "outputs": [{"name": "starter culture", "type": "sample", "value": "5 mL"}],
            "notes": "Expected cloudy growth by morning.",
        },
    )
    assert step_response.status_code == 201
    steps = step_response.json()["steps"]
    assert len(steps) == 1
    assert steps[0]["label"] == "Prepare starter culture"
    assert steps[0]["parameters"][0]["value"] == "37 C"


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


def test_standardized_workflow_authoring_and_delete(client) -> None:
    create_response = client.post(
        "/api/v1/workflows",
        json={
            "title": "Dummy Standardized Workflow",
            "description": "Temporary reusable protocol.",
            "visibility": "library",
            "library_state": "published",
            "version": 1,
            "tags": ["standardized", "dummy"],
        },
    )
    assert create_response.status_code == 201
    workflow = create_response.json()
    assert workflow["title"] == "Dummy Standardized Workflow"
    assert workflow["project_id"] is None
    assert workflow["library_state"] == "published"

    add_step = client.post(
        f"/api/v1/workflows/{workflow['id']}/steps",
        json={
            "label": "Prepare sample",
            "sublabel": "standard protocol",
            "status_template": "pending",
            "duration": "10 min",
            "procedure_markdown": "Prepare the standardized sample.",
            "inputs": [{"name": "Sample", "type": "sample", "value": "1 mL"}],
            "parameters": [{"label": "Temp", "value": "4 C"}],
            "outputs": [{"name": "Prepared sample", "type": "sample"}],
            "notes": "Authoring coverage.",
        },
    )
    assert add_step.status_code == 201
    workflow = add_step.json()
    step = workflow["steps"][0]
    assert step["label"] == "Prepare sample"

    edit_step = client.patch(
        f"/api/v1/workflows/{workflow['id']}/steps/{step['id']}",
        json={
            "label": "Prepare edited sample",
            "sublabel": "edited standard protocol",
            "status_template": "running",
            "duration": "15 min",
            "procedure_markdown": "Prepare and document the standardized sample.",
            "inputs": [{"name": "Sample", "type": "sample", "value": "2 mL"}],
            "parameters": [{"label": "Temp", "value": "room temp"}],
            "outputs": [{"name": "Prepared sample", "type": "sample"}],
            "notes": "Edited authoring coverage.",
        },
    )
    assert edit_step.status_code == 200
    assert edit_step.json()["steps"][0]["label"] == "Prepare edited sample"

    branch = client.post(
        f"/api/v1/workflows/{workflow['id']}/branches",
        json={"anchor_step_id": step["id"], "label": "Side check"},
    )
    assert branch.status_code == 201
    branch_id = branch.json()["steps"][0]["branch_tracks"][0]["id"]

    delete_branch = client.delete(f"/api/v1/workflows/{workflow['id']}/branches/{branch_id}")
    assert delete_branch.status_code == 200
    assert delete_branch.json()["steps"][0]["branch_tracks"] == []

    delete_step = client.delete(f"/api/v1/workflows/{workflow['id']}/steps/{step['id']}")
    assert delete_step.status_code == 200
    assert delete_step.json()["steps"] == []

    delete_workflow = client.delete(f"/api/v1/workflows/{workflow['id']}")
    assert delete_workflow.status_code == 204
    missing = client.get(f"/api/v1/workflows/{workflow['id']}")
    assert missing.status_code == 404


def test_standardize_and_insert_standardized_workflow_copy(client) -> None:
    standardize_response = client.post(
        "/api/v1/workflows/workflow-rpc10-troubleshooting/standardize",
        json={
            "title": "RPC10 Snapshot Standard",
            "description": "Snapshot from the experimental workflow.",
            "tags": ["rpc10", "snapshot"],
        },
    )
    assert standardize_response.status_code == 201
    standardized = standardize_response.json()
    assert standardized["title"] == "RPC10 Snapshot Standard"
    assert "standardized" in standardized["tags"]
    assert standardized["project_id"] is None
    assert len(standardized["steps"]) > 0

    insert_response = client.post(
        "/api/v1/workflows/workflow-ccl20-transformation/insert-standardized",
        json={
            "standardized_workflow_id": "workflow-standard-reverse-nickel",
            "after_step_id": "ccl20-02",
        },
    )
    assert insert_response.status_code == 200
    labels = [step["label"] for step in insert_response.json()["steps"]]
    assert "Equilibrate Reverse Ni-NTA" in labels
    assert "Load Cleavage Mixture" in labels

    branch_insert = client.post(
        "/api/v1/workflows/workflow-ccl20-transformation/insert-standardized",
        json={
            "standardized_workflow_id": "workflow-standard-ion-exchange",
            "anchor_step_id": "ccl20-03",
            "branch_label": "Ion exchange troubleshooting",
        },
    )
    assert branch_insert.status_code == 200
    anchor = next(step for step in branch_insert.json()["steps"] if step["id"] == "ccl20-03")
    assert anchor["branch_tracks"][0]["label"] == "Ion exchange troubleshooting"
    assert anchor["branch_tracks"][0]["steps"][0]["label"] == "Prepare Low-Salt Start Buffer"
