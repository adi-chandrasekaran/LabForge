def test_health_initializes_database(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "reachable"


def test_openapi_contains_foundation_routes(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/me" in paths
    assert "/api/v1/workflows" in paths
    assert "/api/v1/projects" in paths
    assert "/api/v1/docs" in paths
    assert "/api/v1/dashboard/home" in paths
    assert "/api/v1/profile/summary" in paths
    assert "/api/v1/ai/settings" in paths
    assert "/api/v1/analysis/modules" in paths
    assert "/api/v1/mcp/manifest" in paths


def test_mock_current_user_is_created(client) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "user-dev-chen"
    assert payload["role"] == "professor"


def test_cors_allows_localhost_dev_ports(client) -> None:
    response = client.options(
        "/api/v1/dashboard/home",
        headers={
            "Origin": "http://127.0.0.1:4180",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4180"
