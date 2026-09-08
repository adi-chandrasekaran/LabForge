def test_home_summary_returns_seeded_overview(client) -> None:
    response = client.get("/api/v1/dashboard/home")
    assert response.status_code == 200
    payload = response.json()

    assert payload["user_display_name"] == "Chen, Y."
    assert payload["protocol_count"] == 6
    assert payload["project_count"] >= 1
    assert any(project["id"] == "project-anc2" for project in payload["recent_projects"])


def test_profile_summary_reflects_instantiated_experiment_activity(client) -> None:
    instantiate_response = client.post(
        "/api/v1/experiments/instantiate",
        json={
            "project_id": "project-anc2",
            "title": "ANC2 Summary Run",
            "experiment_date": "2026-07-15",
            "workflow_ids": ["workflow-anc2-batch-1", "workflow-anc2-batch-2"],
            "notes": "",
        },
    )
    assert instantiate_response.status_code == 201

    home_response = client.get("/api/v1/dashboard/home")
    assert home_response.status_code == 200
    home_payload = home_response.json()
    assert home_payload["active_experiment_count"] >= 1
    assert len(home_payload["recent_activity"]) >= 1

    profile_response = client.get("/api/v1/profile/summary")
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["user"]["id"] == "user-dev-chen"
    assert profile["lab_name"] == "Ferretti Lab"
    assert "Protein Purification" in profile["expertise"]
    assert profile["experiment_count"] >= 1
    assert len(profile["monthly_activity"]) == 12
