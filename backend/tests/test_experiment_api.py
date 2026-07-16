def _workflow_run_by_source(experiment: dict, source_workflow_id: str) -> dict:
    return next(workflow_run for workflow_run in experiment["workflow_runs"] if workflow_run["source_workflow_id"] == source_workflow_id)


def _step_run_by_label(workflow_run: dict, label: str) -> dict:
    return next(step_run for step_run in workflow_run["step_runs"] if step_run["label"] == label)


def test_experiment_crudl_and_instantiation_from_anc2(client) -> None:
    create_response = client.post(
        "/api/v1/experiments",
        json={
            "project_id": "project-anc2",
            "title": "Manual ANC2 Run",
            "experiment_date": "2026-07-15",
            "notes": "Created directly for CRUDL coverage.",
        },
    )
    assert create_response.status_code == 201
    created_experiment = create_response.json()
    assert created_experiment["title"] == "Manual ANC2 Run"
    assert created_experiment["workflow_runs"] == []

    list_response = client.get("/api/v1/experiments?project_id=project-anc2")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    instantiate_response = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "ANC2 PR3 Experiment",
            "experiment_date": "2026-07-15",
            "workflow_ids": ["workflow-anc2-batch-1", "workflow-anc2-batch-2"],
            "notes": "Instantiated from ANC2 workflow library.",
        },
    )
    assert instantiate_response.status_code == 201
    experiment = instantiate_response.json()
    assert experiment["title"] == "ANC2 PR3 Experiment"
    assert experiment["status"] == "running"
    assert len(experiment["workflow_runs"]) == 2

    batch_1_run = _workflow_run_by_source(experiment, "workflow-anc2-batch-1")
    batch_2_run = _workflow_run_by_source(experiment, "workflow-anc2-batch-2")
    assert len(batch_1_run["step_runs"]) == 13
    assert len(batch_2_run["step_runs"]) == 10
    assert _step_run_by_label(batch_1_run, "Dialysis")["status"] == "running"
    assert _step_run_by_label(batch_2_run, "Cell Lysis")["status"] == "pending"

    get_response = client.get(f"/api/v1/experiments/{experiment['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == experiment["id"]

    update_response = client.patch(
        f"/api/v1/experiments/{experiment['id']}",
        json={"notes": "Run has started and dialysis is being monitored."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "Run has started and dialysis is being monitored."

    delete_response = client.delete(f"/api/v1/experiments/{created_experiment['id']}")
    assert delete_response.status_code == 204


def test_experiment_step_run_updates_do_not_mutate_workflow_template(client) -> None:
    instantiate_response = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "ANC2 Persistence Check",
            "experiment_date": "2026-07-15",
            "workflow_ids": ["workflow-anc2-batch-1", "workflow-anc2-batch-2"],
            "notes": "",
        },
    )
    assert instantiate_response.status_code == 201
    experiment = instantiate_response.json()

    batch_1_run = _workflow_run_by_source(experiment, "workflow-anc2-batch-1")
    dialysis_step_run = _step_run_by_label(batch_1_run, "Dialysis")

    step_run_update = client.patch(
        f"/api/v1/experiments/{experiment['id']}/workflow-runs/{batch_1_run['id']}/steps/{dialysis_step_run['id']}",
        json={
            "label": "Dialysis",
            "sublabel": "Remove Imidazole",
            "status": "complete",
            "duration": "18 hr",
            "procedure_markdown": "Buffer exchanged twice; imidazole removal verified by A260/A280.",
            "inputs": dialysis_step_run["inputs"],
            "parameters": [
                {"label": "Temp", "value": "4 C"},
                {"label": "Duration", "value": "18 hr"},
                {"label": "Buffer changes", "value": "3x2 L"},
            ],
            "outputs": dialysis_step_run["outputs"],
            "notes": "No precipitation after buffer optimization.",
        },
    )
    assert step_run_update.status_code == 200
    updated_experiment = step_run_update.json()
    updated_batch_1_run = _workflow_run_by_source(updated_experiment, "workflow-anc2-batch-1")
    updated_dialysis = _step_run_by_label(updated_batch_1_run, "Dialysis")
    assert updated_dialysis["status"] == "complete"
    assert updated_dialysis["notes"] == "No precipitation after buffer optimization."
    assert updated_dialysis["parameters"][1]["value"] == "18 hr"
    assert updated_batch_1_run["status"] in {"planned", "running"}
    assert updated_experiment["status"] in {"planned", "running"}

    reloaded_experiment = client.get(f"/api/v1/experiments/{experiment['id']}")
    assert reloaded_experiment.status_code == 200
    reloaded_batch_1_run = _workflow_run_by_source(reloaded_experiment.json(), "workflow-anc2-batch-1")
    assert _step_run_by_label(reloaded_batch_1_run, "Dialysis")["notes"] == "No precipitation after buffer optimization."

    workflow_response = client.get("/api/v1/workflows/workflow-anc2-batch-1")
    assert workflow_response.status_code == 200
    template_dialysis = next(step for step in workflow_response.json()["steps"] if step["id"] == "b1-05")
    assert template_dialysis["status_template"] == "running"
    assert template_dialysis["notes"] == "Confirm imidazole removal before cleavage step."
