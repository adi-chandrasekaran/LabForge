from backend.app.config import get_settings


def test_local_mode_defaults_are_exposed(client) -> None:
    get_settings.cache_clear()
    status_response = client.get("/api/v1/sync/status")
    assert status_response.status_code == 200

    payload = status_response.json()
    assert payload["app_mode"] == "local"
    assert payload["database_backend"] == "sqlite"
    assert payload["auth_backend"] == "mock"
    assert payload["storage_backend"] == "local"
    assert payload["local_status"] == "idle"
    assert payload["pending_changes"] == 0
    assert payload["hosted_sync_ready"] is False


def test_sync_status_tracks_local_mutations(client) -> None:
    initial_status = client.get("/api/v1/sync/status")
    assert initial_status.status_code == 200
    assert initial_status.json()["pending_changes"] == 0

    create_project = client.post(
        "/api/v1/projects",
        json={
            "title": "PR6 Sync Project",
            "code": "SYNC-2026-07",
            "description": "Created to verify local sync tracking.",
            "status": "active",
            "tags": ["sync"],
        },
    )
    assert create_project.status_code == 201

    status_after_create = client.get("/api/v1/sync/status")
    assert status_after_create.status_code == 200
    payload = status_after_create.json()
    assert payload["local_status"] == "saved_locally"
    assert payload["pending_changes"] == 1
    assert payload["last_local_write_at"] is not None
    assert payload["last_operation"] == "project.create"


def test_sync_push_placeholder_reports_attempt_without_clearing_changes(client) -> None:
    instantiate_response = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "PR6 Sync Attempt",
            "experiment_date": "2026-07-16",
            "workflow_ids": ["workflow-anc2-batch-1", "workflow-anc2-batch-2"],
            "notes": "Created to test local sync placeholder.",
        },
    )
    assert instantiate_response.status_code == 201

    push_response = client.post("/api/v1/sync/push")
    assert push_response.status_code == 200
    payload = push_response.json()
    assert payload["pending_changes"] >= 1
    assert payload["last_sync_attempt_at"] is not None
    assert payload["hosted_sync_ready"] is False
    assert "not implemented yet" in payload["last_error"]
    assert "not configured in local mode" in payload["message"]
