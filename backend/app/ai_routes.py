from __future__ import annotations

from fastapi import APIRouter, Request
from .config import get_settings
from .schemas import AISettingsRead, AIProviderStatusRead, AnalysisModuleRead, LocalModelRuntimeRead, MCPManifestRead, MCPToolRead


router = APIRouter(prefix="/api/v1", tags=["ai"])
settings = get_settings()

ANALYSIS_MODULES = [
    AnalysisModuleRead(
        id="module-yield-trend",
        name="Yield Trend Analysis",
        status="placeholder",
        category="purification",
        description="Will compare experiment yields across runs and flag downward drift before a project stalls.",
        input_types=["experiment", "step_run", "a280"],
        output_types=["trend_report", "warning"],
    ),
    AnalysisModuleRead(
        id="module-sec-peak-review",
        name="SEC Peak Review",
        status="placeholder",
        category="chromatography",
        description="Will inspect preparative SEC metadata and annotate peak-shape or pooling concerns.",
        input_types=["workflow_step", "chromatogram", "fraction_notes"],
        output_types=["annotation", "pooling_suggestion"],
    ),
    AnalysisModuleRead(
        id="module-nmr-readiness",
        name="NMR Readiness Scoring",
        status="placeholder",
        category="nmr",
        description="Will combine purity, concentration, buffer compatibility, and aggregation notes into an explicit readiness score.",
        input_types=["experiment", "workflow_step", "concentration", "buffer"],
        output_types=["score", "next_steps"],
    ),
]


@router.get("/ai/settings", response_model=AISettingsRead)
def read_ai_settings() -> AISettingsRead:
    return AISettingsRead(
        chat_enabled=False,
        workflow_builder_enabled=False,
        analysis_modules_enabled=False,
        local_models_enabled=False,
        api_keys_enabled=False,
        supported_api_providers=[
            AIProviderStatusRead(
                id="openai",
                label="OpenAI API Key",
                configured=False,
                status="placeholder",
                detail="Key management UI is reserved for a future hosted or local secure settings flow.",
            ),
            AIProviderStatusRead(
                id="anthropic",
                label="Anthropic API Key",
                configured=False,
                status="placeholder",
                detail="Provider slot is reserved. No key storage or request execution is enabled in PR 8.",
            ),
        ],
        local_model_runtimes=[
            LocalModelRuntimeRead(
                id="ollama",
                label="Ollama",
                installed=False,
                enabled=False,
                status="placeholder",
                detail="Local runtime detection is intentionally disabled until model execution and safety flows are implemented.",
            ),
            LocalModelRuntimeRead(
                id="llama-cpp",
                label="llama.cpp",
                installed=False,
                enabled=False,
                status="placeholder",
                detail="Reserved runtime slot for on-laptop inference. No binary discovery or model launch exists yet.",
            ),
        ],
        notes=[
            "AI actions are disabled in PR 8.",
            "These settings reserve the contract for future chat, workflow-building, and analysis integrations.",
            "OpenAPI remains the source contract that future MCP tooling will wrap.",
        ],
    )


@router.get("/analysis/modules", response_model=list[AnalysisModuleRead])
def list_analysis_modules() -> list[AnalysisModuleRead]:
    return ANALYSIS_MODULES


@router.get("/mcp/manifest", response_model=MCPManifestRead)
def read_mcp_manifest(request: Request) -> MCPManifestRead:
    openapi = request.app.openapi()
    tools: list[MCPToolRead] = []
    for path, methods in sorted(openapi.get("paths", {}).items()):
        for method, operation in sorted(methods.items()):
            if method.lower() not in {"get", "post", "patch", "delete"}:
                continue
            tools.append(
                MCPToolRead(
                    name=operation.get("operationId", f"{method}_{path}"),
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary") or operation.get("description") or "No summary provided.",
                )
            )

    return MCPManifestRead(
        server_name="nmr-lab-openapi-placeholder",
        server_version=request.app.version,
        transport="openapi-http",
        status="placeholder",
        openapi_url="/openapi.json",
        tool_count=len(tools),
        tools=tools,
        notes=[
            "This is a placeholder MCP-oriented manifest derived from the current OpenAPI contract.",
            "No agent execution, tool calling session, or chat orchestration is enabled yet.",
            "Future MCP work should convert these HTTP operations into an agent-facing tool surface.",
        ],
    )
