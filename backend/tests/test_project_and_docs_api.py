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


def test_external_docs_list_and_read(client) -> None:
    list_response = client.get("/api/v1/docs")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert any(doc["slug"] == "workflow-library" for doc in docs)

    read_response = client.get("/api/v1/docs/workflow-library")
    assert read_response.status_code == 200
    doc = read_response.json()
    assert doc["title"] == "Workflow Library"
    assert "ANC2 Batch 1 and Batch 2" in doc["content"]

    missing_response = client.get("/api/v1/docs/does-not-exist")
    assert missing_response.status_code == 404
