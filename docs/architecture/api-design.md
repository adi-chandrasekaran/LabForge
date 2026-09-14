# API Design

The API is versioned under `/api/v1`. FastAPI generates `/openapi.json` and interactive docs at `/docs`.

## System Routes

- `GET /api/v1/health`
- `GET /api/v1/me`

## Project Routes

- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`

## Workflow Library Routes

- `GET /api/v1/workflows`
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{workflow_id}`
- `PATCH /api/v1/workflows/{workflow_id}`
- `DELETE /api/v1/workflows/{workflow_id}`
- `POST /api/v1/workflows/{workflow_id}/publish`
- `POST /api/v1/workflows/{workflow_id}/steps`
- `PATCH /api/v1/workflows/{workflow_id}/steps/{step_id}`
- `DELETE /api/v1/workflows/{workflow_id}/steps/{step_id}`
- `POST /api/v1/workflows/{workflow_id}/steps/reorder`
- `POST /api/v1/workflows/{workflow_id}/branches`
- `PATCH /api/v1/workflows/{workflow_id}/branches/{branch_id}`
- `DELETE /api/v1/workflows/{workflow_id}/branches/{branch_id}`
- `POST /api/v1/workflows/{workflow_id}/branches/{branch_id}/steps`

## Experiment Routes

- `GET /api/v1/experiments`
- `POST /api/v1/experiments`
- `POST /api/v1/experiments/instantiate`
- `GET /api/v1/experiments/{experiment_id}`
- `PATCH /api/v1/experiments/{experiment_id}`
- `DELETE /api/v1/experiments/{experiment_id}`
- `PATCH /api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}`

## Attachment Routes

- `GET /api/v1/workflows/{workflow_id}/steps/{step_id}/attachments`
- `POST /api/v1/workflows/{workflow_id}/steps/{step_id}/attachments`
- `GET /api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}/attachments`
- `POST /api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}/attachments`
- `DELETE /api/v1/attachments/{attachment_id}`
- `GET /api/v1/attachments/{attachment_id}/content`

## External Docs Routes

- `GET /api/v1/docs`
- `GET /api/v1/docs/{slug}`

## Sync Routes

- `GET /api/v1/sync/status`
- `POST /api/v1/sync/push`

## Chat Routes

- `GET /api/v1/channels`
- `POST /api/v1/channels`
- `GET /api/v1/channels/{channel_id}`
- `PATCH /api/v1/channels/{channel_id}`
- `DELETE /api/v1/channels/{channel_id}`
- `GET /api/v1/channels/{channel_id}/messages`
- `POST /api/v1/channels/{channel_id}/messages`
- `PATCH /api/v1/channels/{channel_id}/messages/{message_id}`
- `DELETE /api/v1/channels/{channel_id}/messages/{message_id}`
- `GET /api/v1/channels/{channel_id}/messages/{message_id}/attachments`
- `POST /api/v1/channels/{channel_id}/messages/{message_id}/attachments`

## AI, Agent Tool, And MCP Routes

- `GET /api/v1/ai/settings`
- `GET /api/v1/analysis/modules`
- `GET /api/v1/mcp/manifest`
- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/tools/{tool_name}/invoke`
- `GET /api/v1/agent/status`
- `POST /api/v1/agent/conversations`
- `GET /api/v1/agent/conversations/{conversation_id}`
- `GET /api/v1/agent/conversations/{conversation_id}/runs`
- `GET /api/v1/agent/conversations/{conversation_id}/runs/{run_id}`

## PR 3 Behavior Notes

- `POST /api/v1/experiments/instantiate` takes `project_id`, `title`, `experiment_date`, `workflow_ids`, and optional `notes`.
- Instantiation snapshots the selected workflow templates into `ExperimentWorkflowRun` records and their mainline steps into `ExperimentStepRun` records.
- `PATCH` on an experiment step run updates the experiment snapshot only. It does not change the workflow library template.
- `GET /api/v1/experiments?project_id=...` is the current frontend entry point for loading the latest experiment for ANC2.
- Attachment uploads are image-only in local mode and return metadata plus a download URL. Delete calls remove both the metadata row and the local file when present.
- `GET /api/v1/projects` now returns frontend summary fields such as `owner_display_name`, `experiment_count`, `workflow_count`, and `progress_percent`.
- `GET /api/v1/docs` and `GET /api/v1/docs/{slug}` expose `/external-docs` as API content for in-app help surfaces.
- `GET /api/v1/sync/status` returns current local sync state plus backend adapter choices.
- `POST /api/v1/sync/push` is currently a placeholder route that records a sync attempt but keeps local changes pending.
- Chat routes are lab-scoped through the current user `lab_id`. Users can only see channels and messages from their own lab.
- Chat messages can optionally reference a workflow template or an experiment run.
- Chat message attachments reuse the shared `Attachment` table with `owner_type = "chat_message"`.
- Message edits and deletes are allowed for the author or a professor override in local mode.
- AI placeholder routes are intentionally read-only in PR 8.
- The MCP manifest is generated from the live FastAPI OpenAPI schema, not from a separate manual registry.
- The agent-tool catalog is the executable, schema-backed tool boundary. It returns supported and unavailable tools, while invocations return a stable `{ tool_name, ok, data, error }` envelope.
- `create_note` requires `confirmed: true` and delegates to the existing chat-message operation; it cannot update embedded experiment or workflow-step notes.
- Agent conversations and their run/tool-call audit records are owner-scoped. PR 4 exposes their retrieval APIs only; PR 5 will create and execute runs.
- `GET /api/v1/agent/status` intentionally reports configuration availability without revealing a provider secret.

Future routes may add an MCP transport and analysis execution.

## Design Rules

- Request and response bodies use Pydantic models.
- API routes return stable identifiers and timestamps.
- Local mode uses a mock current user until Supabase JWT verification is added.
- OpenAPI is the source of truth for future MCP conversion.
