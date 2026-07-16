def test_ai_settings_placeholder_contract(client) -> None:
    response = client.get("/api/v1/ai/settings")
    assert response.status_code == 200
    payload = response.json()

    assert payload["chat_enabled"] is False
    assert payload["workflow_builder_enabled"] is False
    assert payload["analysis_modules_enabled"] is False
    assert payload["local_models_enabled"] is False
    assert payload["api_keys_enabled"] is False
    assert {provider["id"] for provider in payload["supported_api_providers"]} == {"openai", "anthropic"}
    assert {runtime["id"] for runtime in payload["local_model_runtimes"]} == {"ollama", "llama-cpp"}
    assert any("OpenAPI" in note for note in payload["notes"])


def test_analysis_module_registry_lists_placeholders(client) -> None:
    response = client.get("/api/v1/analysis/modules")
    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 3
    assert {module["id"] for module in payload} == {
        "module-yield-trend",
        "module-sec-peak-review",
        "module-nmr-readiness",
    }
    assert all(module["status"] == "placeholder" for module in payload)


def test_mcp_manifest_is_derived_from_openapi(client) -> None:
    response = client.get("/api/v1/mcp/manifest")
    assert response.status_code == 200
    payload = response.json()

    assert payload["server_name"] == "nmr-lab-openapi-placeholder"
    assert payload["status"] == "placeholder"
    assert payload["openapi_url"] == "/openapi.json"
    assert payload["tool_count"] >= 1
    assert any(tool["path"] == "/api/v1/workflows" for tool in payload["tools"])
    assert any(tool["path"] == "/api/v1/ai/settings" for tool in payload["tools"])
    assert any("placeholder MCP-oriented manifest" in note for note in payload["notes"])
