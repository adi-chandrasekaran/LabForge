# Agent Capability Map

## Status

This is an executable agent-tool contract, not an LLM or MCP server. Its source
of truth is the authenticated FastAPI tool gateway at `/api/v1/agent/tools`.
The machine-readable companion is
`docs/contracts/agent-tool-contract.v1.json`.

The gateway delegates to shared application operations used by the existing
routes. It does not query SQLAlchemy models directly or duplicate the route
layer's serialization, validation, authorization, and sync behavior.

## Cross-cutting rules

- Resolve the actor only through the current authentication adapter. Do not
  accept a user id, lab id, role, or ownership claim as an agent input.
- Preserve existing backend access checks and scopes. Current local mode uses
  mock authentication; the future hosted auth adapter is not implemented.
- Read tools do not mutate state. `create_note` is the only mapped write tool,
  and it creates a lab-scoped `ChatMessage`, not an embedded experiment or
  workflow-step note.
- A future runtime must ask the user for confirmation immediately before the
  `create_note` write. It must return the persisted message including its id,
  author, timestamps, and any resolved workflow/experiment references.
- Never label a static placeholder or generic attachment as an NMR analysis or
  spectrum.

## Supported tool groups

| Group | Agent tool | Backend operation reused | Parameters | Permission / result |
| --- | --- | --- | --- | --- |
| Project lookup | `get_project` | `GET /api/v1/projects/{project_id}` | `project_id` | Read; return existing `ProjectRead`. |
| Project listing | `list_projects` | `GET /api/v1/projects` | none | Read; return existing list shape. |
| Workflow lookup | `get_workflow` | `GET /api/v1/workflows/{workflow_id}` | `workflow_id` | Read; return existing `WorkflowRead`, including steps/branches. |
| Workflow listing | `list_workflows` | `GET /api/v1/workflows` | optional `tag`, `library_state`, `visibility`, `project_id` | Read; preserve existing filters. |
| Experiment lookup | `get_experiment` | `GET /api/v1/experiments/{experiment_id}` | `experiment_id` | Read; return run snapshots and step runs. |
| Experiment listing | `list_experiments` | `GET /api/v1/experiments` | optional `project_id` | Read; preserve existing filter and ordering. |
| Run-step lookup | `get_experiment_run_step` | Parent `GET /api/v1/experiments/{experiment_id}` | `experiment_id`, `workflow_run_id`, `step_run_id` | Read; select the requested child only from the returned parent. |
| Experiment-note search | `search_experiment_notes` | `GET /api/v1/experiments` plus local filter | required `query`; optional `project_id`, `limit` | Read; case-insensitive substring matching on the returned `notes` field only. |
| Lab context | `list_chat_channels`, `list_channel_messages` | `GET /api/v1/channels`; `GET /api/v1/channels/{channel_id}/messages` | channel id and optional limit for messages | Read; existing backend scopes chat to the actor's lab. |
| Scoped note creation | `create_note` | `POST /api/v1/channels/{channel_id}/messages` | `channel_id`, `body`; optional workflow/experiment references | Write; existing backend sets author, enforces lab scope, and validates references. Requires runtime confirmation. |

`search_experiment_notes` is deliberately limited: there is no server-side
full-text search, ranker, or pagination. The future adapter may filter only the
experiments returned by the existing list operation, then truncate to the
requested limit (default 20, maximum 100).

## Requested tools that cannot be implemented from current backend logic

| Tool | Reason |
| --- | --- |
| `get_sample`, `list_samples` | No Sample model, table, API, or service. |
| `get_spectrum`, `compare_spectra` | No Spectrum model, spectral file format, or comparison logic. |
| `get_peak_assignments` | No Peak or Assignment model, table, API, or service. |
| `find_residue`, `get_residue_shifts` | No Protein/sequence/Residue or chemical-shift representation. |
| `calculate_chemical_shift_perturbation` | No shift data or calculation backend implementation. |

The existing `NMR Readiness Scoring` item is a static analysis-module
placeholder and must not be exposed as a calculating agent tool.

## Future implementation boundary

Future work can adapt this gateway to an LLM or MCP transport. It must not add
provider keys, prompt orchestration, or NMR scientific calculations until the
missing data models and validated calculation requirements exist.
