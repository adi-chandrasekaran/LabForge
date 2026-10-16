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

The server reads provider keys only from its environment. OpenAI uses
`NMR_LAB_OPENAI_API_KEY` and `NMR_LAB_AGENT_MODEL`; Gemini uses
`NMR_LAB_GEMINI_API_KEY` and `NMR_LAB_GEMINI_MODEL`. No route, audit record,
log, or frontend state exposes a key. `GET /api/v1/agent/status` returns
`agent_unavailable` when the selected provider is not configured.

The OpenAI Responses, Gemini, and local Ollama provider adapters share one
integration boundary. `NMR_LAB_AGENT_PROVIDER` selects `gemini` by default,
`openai` for OpenAI, or `ollama` for a model running on the user's machine.
Ollama defaults to `http://127.0.0.1:11434` and `llama3.2`; both values are
configurable through `NMR_LAB_OLLAMA_BASE_URL` and `NMR_LAB_OLLAMA_MODEL`.
Ollama requires no API key and sends no prompt or tool result to a hosted model.
All providers generate their function catalog from PR 3's
registry, so unavailable NMR tools and `create_note` remain excluded. The
permanent assistant instruction requires tool evidence for every
dataset-specific claim, prohibits invented experimental values, and requires a
clear statement when data is unavailable.

## Agent Execution Loop

`POST /api/v1/agent/conversations/{conversation_id}/runs` executes the
read-only research assistant for an authenticated conversation. It persists the
request as a running audit record, sends at most the ten most recent completed
runs from that same owned conversation as context, and then calls the selected
provider with the permanent instructions and function definitions.

Function calls are validated through the existing PR 3 registry and execute
in-process with `confirmed: false`. Unknown, unavailable, malformed, failed,
and write-tool calls are persisted and returned to the model as structured tool
errors; they never execute. Every model-selected call records validated
arguments, result/error, sequence, and timestamps. The loop returns outputs to
the provider and stops after a valid final answer or five tool rounds.

Final answers have `answer`, `data_availability`, and
`evidence_tool_call_ids`. A `retrieved` answer must cite successful audit IDs
from its own run; an `unavailable` answer must explicitly state that required
data is unavailable. Provider failures, malformed final output, and exhausted
tool rounds fail the run with stable errors instead of inventing a scientific
answer.

## Frontend Surface

The research assistant at `/assistant` persists the active conversation ID in
the browser and restores its durable backend run history after refresh. Run
details are fetched individually so the ordered evidence and tool audit remains
available. Starting a new conversation clears only the active browser selection;
it does not delete the audit records retained by the backend.

Provider and run failures are rendered as readable messages, while active runs
identify that evidence retrieval and tool execution are in progress. Browser
integration tests mock the provider-facing API boundary so UI reliability does
not depend on paid credentials or a locally running model. See
`docs/agent-local-setup.md` for the supported no-cost Ollama workflow.

## AI Model Placeholder Surface

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
