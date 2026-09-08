def test_list_and_create_projects(client) -> None:
    seeded_response = client.get("/api/v1/projects")
    assert seeded_response.status_code == 200
    seeded_projects = seeded_response.json()
    assert any(project["id"] == "project-anc2" for project in seeded_projects)

    create_response = client.post(
        "/api/v1/projects",
        json={
            "title": "SEC Optimization",
            "code": "SEC-2026-07",
            "description": "Track SEC conditions and pooled fractions.",
            "status": "active",
            "tags": ["sec", "anc2"],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "SEC Optimization"
    assert created["code"] == "SEC-2026-07"
    assert created["owner_display_name"] == "Chen, Y."
    assert created["experiment_count"] == 0

    duplicate_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Duplicate SEC Optimization",
            "code": "SEC-2026-07",
            "description": "",
            "status": "active",
            "tags": [],
        },
    )
    assert duplicate_response.status_code == 400


def test_local_showcase_projects_are_deterministic(client) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    titles = {project["title"] for project in response.json()}
    assert titles == {
        "ANC2 Protein Purification",
        "RPC10 Purification Process And Troubleshooting",
        "CCL20 Transformation And Culture",
        "Shared Methods",
    }
    assert all(project["owner_display_name"] == "Chen, Y." for project in response.json())


def test_local_demo_can_delete_seeded_placeholder_project(client) -> None:
    delete_response = client.delete("/api/v1/projects/project-ccl20")
    assert delete_response.status_code == 204

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    project_ids = {project["id"] for project in response.json()}
    assert "project-ccl20" not in project_ids


def test_new_project_gets_blank_experimental_workflow_and_can_delete_cascade(client) -> None:
    create_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Temporary Demo Project",
            "code": "TEMP-DEMO",
            "description": "Should get its own workflow tab.",
            "status": "active",
            "tags": ["temporary"],
        },
    )
    assert create_response.status_code == 201
    project = create_response.json()

    workflows_response = client.get(f"/api/v1/workflows?tag=experimental&project_id={project['id']}")
    assert workflows_response.status_code == 200
    workflows = workflows_response.json()
    assert len(workflows) == 1
    assert workflows[0]["title"] == "Temporary Demo Project Experimental Workflow"
    assert workflows[0]["steps"] == []

    delete_response = client.delete(f"/api/v1/projects/{project['id']}")
    assert delete_response.status_code == 204

    workflows_after_delete = client.get(f"/api/v1/workflows?tag=experimental&project_id={project['id']}")
    assert workflows_after_delete.status_code == 200
    assert workflows_after_delete.json() == []


def test_project_detail_update_delete_and_lab_members(client) -> None:
    members_response = client.get("/api/v1/users/lab-members")
    assert members_response.status_code == 200
    members = members_response.json()
    member_ids = {member["id"] for member in members}
    assert {"user-dev-chen", "user-pi-ferretti", "user-postdoc-okafor"}.issubset(member_ids)

    detail_response = client.get("/api/v1/projects/project-anc2")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert any(member["project_role"] == "owner" for member in detail["members"])

    update_response = client.patch(
        "/api/v1/projects/project-anc2",
        json={
            "description": "Updated ANC2 notes for project detail testing.",
            "members": [
                {"user_id": "user-dev-chen", "role": "owner"},
                {"user_id": "user-pi-ferretti", "role": "editor"},
                {"user_id": "user-postdoc-okafor", "role": "viewer"},
            ],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] == "Updated ANC2 notes for project detail testing."
    assert any(
        member["user_id"] == "user-postdoc-okafor" and member["project_role"] == "viewer"
        for member in updated["members"]
    )

    create_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Delete Me",
            "code": "DELETE-ME-2026",
            "description": "Delete path coverage.",
            "status": "active",
            "tags": ["delete"],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    delete_response = client.delete(f"/api/v1/projects/{created['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/projects/{created['id']}")
    assert missing_response.status_code == 404


def test_external_docs_list_and_read(client) -> None:
    list_response = client.get("/api/v1/docs")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert any(doc["slug"] == "workflow-library" for doc in docs)

    read_response = client.get("/api/v1/docs/workflow-library")
    assert read_response.status_code == 200
    doc = read_response.json()
    assert doc["title"] == "Experimental Workflows"
    assert "`ANC2`: two batch workflows shown once, side by side." in doc["content"]

    missing_response = client.get("/api/v1/docs/does-not-exist")
    assert missing_response.status_code == 404
