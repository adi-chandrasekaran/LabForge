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
| NMR entities | `get_sample`, `list_samples`, `get_protein`, `list_proteins`, `get_ligand`, `list_ligands` | `/api/v1/nmr/{samples|proteins|ligands}` | entity IDs and optional project filter | Read; service-enforced lab scope. |
| Spectral data | `get_spectrum`, `list_spectra`, `get_peak`, `list_peaks`, `get_peak_assignments` | `/api/v1/nmr/{spectra|peaks|assignments}` | spectrum, sample, or peak IDs | Read through the lab-scoped parent spectrum. |
| Residue data | `find_residue`, `get_residue_shifts` | `/api/v1/nmr/{residues|chemical-shifts}` | protein/residue IDs, optional position/text/spectrum filters | Read; returns stored values only. |
| Shift analysis | `compare_spectra`, `calculate_chemical_shift_perturbation` | `/api/v1/nmr/analyses/*` | two spectrum IDs; optional nuclei/weights | Deterministic service calculation; returns source IDs, components, formula, and weights. |

`search_experiment_notes` is deliberately limited: there is no server-side
full-text search, ranker, or pagination. The future adapter may filter only the
experiments returned by the existing list operation, then truncate to the
requested limit (default 20, maximum 100).

## Requested NMR tools

All originally requested NMR tools now have executable, service-backed registry entries. The discovery response therefore has no unavailable requested tools.

The existing `NMR Readiness Scoring` item is a static analysis-module
placeholder and must not be exposed as a calculating agent tool.

## Future implementation boundary

The registry remains the boundary for LLM and future MCP transports. Provider
keys stay server-side, and model calls cannot bypass tool validation, lab
scope, stored evidence, or deterministic calculation services.
