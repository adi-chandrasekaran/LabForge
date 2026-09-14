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

## Executable Agent Tool Layer

`GET /api/v1/agent/tools` exposes the supported agent-tool catalog, including
each tool's description, JSON input and output schema, permission statement,
side-effect classification, and whether confirmation is required.

`POST /api/v1/agent/tools/{tool_name}/invoke` validates an invocation and
returns a stable `{ tool_name, ok, data, error }` response. The implementation
delegates to the same shared application operations used by project, workflow,
experiment, and chat routes; the tool registry does not query the database
directly.

`create_note` is the only write tool. It requires `confirmed: true`, then
creates a lab-scoped `ChatMessage` through the existing backend rules. This is
an execution guard, not a replacement for the future agent UI obtaining a
person's confirmation immediately before the write.

The tool layer is intentionally not an LLM provider, prompt loop, or MCP
transport. Unsupported NMR data tools remain discoverable as unavailable rather
than fabricating results.

## NMR Research Assistant Foundation

PR 4 adds the durable, provider-backed boundary for a future NMR research
assistant without making a model request. The SQLite audit model consists of
owned `AgentConversation` records, `AgentRun` records, and ordered
`AgentToolCall` records. Conversation and audit endpoints are authenticated and
only return records owned by the current user.

The server reads `NMR_LAB_OPENAI_API_KEY` only from its environment and uses
`NMR_LAB_AGENT_MODEL` (default `gpt-5.5`) as model metadata. No route, audit
record, log, or frontend state exposes the key. `GET /api/v1/agent/status`
returns `agent_unavailable` when the key is absent.

`OpenAIResponsesResearchAssistant` is the integration boundary for the OpenAI
Responses API. Its function catalog is generated from PR 3's registry, but it
includes only supported read tools: unavailable NMR tools and `create_note` are
excluded. The permanent assistant instruction requires tool evidence for every
dataset-specific claim, prohibits invented experimental values, and requires a
clear statement when data is unavailable. PR 5 will add the bounded execution
loop and model request.

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
