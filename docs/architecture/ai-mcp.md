# AI And MCP Architecture

AI work is intentionally staged after the notebook CRUDL, experiment tracking, attachments, and chat surfaces are stable.

## PR 8 Scope

PR 8 does not ship model execution. It ships contract placeholders so later AI work can be built on stable interfaces instead of prototype-only UI.

Implemented placeholder routes:

- `GET /api/v1/ai/settings`
- `GET /api/v1/analysis/modules`
- `GET /api/v1/mcp/manifest`

## AI Settings Placeholder

`GET /api/v1/ai/settings` reserves the backend shape for:

- chat enablement
- workflow-builder agent enablement
- analysis module enablement
- local model runtime enablement
- API key provider enablement

The current response is explicit:

- every feature flag is disabled
- provider entries describe future OpenAI and Anthropic configuration slots
- local runtime entries describe future Ollama and llama.cpp support
- notes explain that execution is intentionally unavailable

## Analysis Module Registry

`GET /api/v1/analysis/modules` exposes a placeholder registry for future scientific analysis modules.

PR 8 seeds three placeholders:

- Yield Trend Analysis
- SEC Peak Review
- NMR Readiness Scoring

These define the contract shape for:

- module identity
- category
- description
- input types
- output types

This makes later module execution pluggable without changing the page contract.

## MCP Placeholder

`GET /api/v1/mcp/manifest` is derived from FastAPI's live OpenAPI schema.

Current behavior:

- iterates current OpenAPI routes
- exposes them as tool-like entries with method, path, and summary
- returns manifest metadata such as status, transport, version, and tool count

This is not a functioning MCP server yet. It is a placeholder manifest that proves the future MCP surface can be generated from the real HTTP contract instead of a hand-maintained duplicate.

## Frontend Surface

`/ai-model` now loads backend placeholder data and renders:

- AI settings summary
- provider placeholder cards
- local runtime placeholder cards
- analysis module cards
- MCP manifest preview

The page is intentionally clear that:

- nothing is enabled
- no key storage exists yet
- no local runtime detection exists yet
- no chat orchestration exists yet

## Future Work

Later milestones can extend this foundation with:

- secure API key storage
- local runtime discovery and configuration
- MCP server transport implementation
- chat orchestration
- workflow-building agents
- executed analysis modules with persisted outputs
