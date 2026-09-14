# NMR Domain Entity Inventory

**Audit baseline:** `main` at `f80dec69` (2026-09-14)

## Purpose and boundary

This is an evidence-based inventory of the persisted domain and public CRUD
surface that exists today. It is not a proposed NMR schema. In particular, the
application is a local-first laboratory workflow notebook with an NMR-readiness
placeholder; it does **not** yet persist samples, proteins, spectra, peaks,
residues, ligands, assignments, or analysis results.

The local database is SQLite by default (`data/nmr_lab.sqlite3`) and is mapped
with SQLAlchemy models in `backend/app/models.py`. The app can be configured
for a future hosted backend, but the only implemented database representation is
the SQLAlchemy/SQLite one described here.

## Existing persisted entities

| Entity | Persisted fields | Relationships | Database representation | Existing CRUD/API |
| --- | --- | --- | --- | --- |
| User | `id`, `email`, `display_name`, `role`, `lab_id`, `created_at` | Referenced by project/workflow memberships, project/workflow ownership, experiment operator, and chat author/channel creator | `users`; primary key `id`; unique/indexed `email` | Read current user: `GET /api/v1/me`; list lab members: `GET /api/v1/lab-members`. No user write/delete routes. |
| Project | `id`, `title`, `code`, `description`, `owner_id`, `status`, JSON `tags`, timestamps | Has `ProjectMember`; referenced by `Workflow` and `Experiment` | `projects`; `owner_id -> users.id`; unique/indexed `code` | `GET/POST /api/v1/projects`, `GET/PATCH/DELETE /api/v1/projects/{project_id}`. Create also creates a private experimental workflow. |
| ProjectMember | `id`, `project_id`, `user_id`, `role`, timestamps | Join between Project and User; owner membership is maintained on project creation/update | `project_members`; foreign keys to `projects` and `users` | Managed only through the `members` property of project create/update. |
| Workflow | `id`, `title`, `description`, `owner_id`, nullable `project_id`, `visibility`, `library_state`, `version`, JSON `tags`, timestamps | Has steps, branches, and workflow memberships; may belong to a project; is snapshotted into experiment workflow runs | `workflows`; foreign keys to users/projects | `GET/POST /api/v1/workflows`, `GET/PATCH/DELETE /api/v1/workflows/{workflow_id}`; plus publish, standardize, and insert-standardized operations. |
| WorkflowMember | `id`, `workflow_id`, `user_id`, `role`, timestamps | Join between Workflow and User; owner membership is maintained on workflow creation/update | `workflow_members`; foreign keys to `workflows` and `users` | Managed through workflow `members` payloads. |
| WorkflowStep | `id`, `workflow_id`, nullable `workflow_branch_id`, nullable `parent_step_id`, nullable `branch_track_id`, `order_index`, `label`, nullable `sublabel`, `status_template`, nullable `duration`, `procedure_markdown`, JSON `inputs`, `parameters`, `outputs`, `notes`, timestamps | Belongs to a workflow; optionally belongs to a branch; may anchor branches; is copied into `ExperimentStepRun` | `workflow_steps`; foreign keys to workflow, branch, and parent step | Create/read/update/delete/reorder through `/api/v1/workflows/{workflow_id}/steps`; branch-step create route is separate. |
| WorkflowBranch | `id`, `workflow_id`, `anchor_step_id`, `label`, timestamps | Belongs to a workflow; anchored to a mainline workflow step; owns branch steps | `workflow_branches`; foreign keys to workflows and workflow steps | Create/update/delete through `/api/v1/workflows/{workflow_id}/branches`. |
| Experiment | `id`, nullable `project_id`, `title`, `experiment_date`, nullable `operator_id`, `status`, `notes`, timestamps | May belong to a project; is operated by a user; owns workflow-run snapshots | `experiments`; foreign keys to projects and users | `GET/POST /api/v1/experiments`, `POST /api/v1/experiments/instantiate`, `GET/PATCH/DELETE /api/v1/experiments/{experiment_id}`. |
| ExperimentWorkflowRun | `id`, `experiment_id`, `source_workflow_id`, copied `workflow_title`, `workflow_description`, `workflow_version`, `order_index`, `status`, timestamps | Snapshot belonging to an experiment; source points to a workflow; owns step-run snapshots | `experiment_workflow_runs`; foreign keys to experiments and workflows | Created only by experiment instantiation; read nested in experiment responses. No independent update/delete API. |
| ExperimentStepRun | `id`, `experiment_workflow_run_id`, `source_workflow_step_id`, `order_index`, `label`, nullable `sublabel`, `status`, nullable `duration`, `procedure_markdown`, JSON `inputs`, `parameters`, `outputs`, `notes`, timestamps | Snapshot belonging to an experiment workflow run; source points to a workflow step; can own attachments | `experiment_step_runs`; foreign keys to experiment workflow runs and workflow steps | Read nested in experiment responses; update at `PATCH /api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}`. |
| ChatChannel | `id`, `lab_id`, `name`, `topic`, nullable `created_by_id`, timestamps | Lab-scoped container that owns messages | `chat_channels`; creator foreign key to users | `GET/POST /api/v1/channels`, `GET/PATCH/DELETE /api/v1/channels/{channel_id}`. |
| ChatMessage | `id`, `channel_id`, `lab_id`, nullable `author_id`, `body`, nullable `referenced_workflow_id`, nullable `referenced_experiment_id`, timestamps | Belongs to a channel/lab and optionally references a workflow or experiment; can own attachments | `chat_messages`; foreign keys to channels, users, workflows, and experiments | List/create/update/delete beneath `/api/v1/channels/{channel_id}/messages`. |
| Attachment | `id`, `owner_type`, `owner_id`, `filename`, `content_type`, `storage_backend`, nullable `local_path`, nullable `remote_url`, `created_at` | Polymorphic owner relationship, implemented as `owner_type`/`owner_id`; supported types are `workflow_step`, `experiment_step_run`, and `chat_message` | `attachments`; no foreign key for generic owner pair | List/upload routes under workflow steps, experiment step runs, and chat messages; content download and delete at `/api/v1/attachments/{attachment_id}`. |
| SyncState | `id`, `pending_changes`, nullable `last_local_write_at`, `last_sync_attempt_at`, `last_sync_success_at`, `last_error`, `last_operation` | Singleton operational state updated by write routes | `sync_state` | Read `GET /api/v1/sync/status`; push placeholder `POST /api/v1/sync/push`. No domain CRUD. |

## Requested NMR entities: current status

| Requested entity | Current representation | CRUD/tooling consequence |
| --- | --- | --- |
| Sample | None | No sample identifier, storage, route, or service exists. |
| Protein | None | No protein sequence/construct representation or route exists. |
| Spectrum | None | No spectral file/metadata representation or route exists. Attachments are generic files, not spectra. |
| Peak | None | No peak-list representation or route exists. |
| Residue | None | No sequence/residue representation or route exists. |
| Ligand | None | No ligand identity, concentration, or binding representation exists. |
| Assignment | None | No resonance/peak assignment representation or route exists. |
| Analysis | Placeholder only | `GET /api/v1/analysis/modules` returns three static module descriptors; results are not executed or persisted. |
| Note | Embedded, not an entity | Text fields exist on workflow steps, experiment step runs, and experiments. Chat messages are a separate structured discussion entity. There is no standalone Note table or `/notes` API. |

## Relationship and lifecycle rules relevant to future NMR work

- A workflow is a reusable protocol/template. An experiment is a dated execution.
  Instantiation copies workflow and mainline step data into independent run
  snapshots; changing a run must not change its source workflow.
- Project and workflow access are membership-based (`owner`, `editor`,
  `commenter`, `viewer`), though the implemented checks currently enforce
  workflow/project editing and workflow publishing. Local development uses a
  mock authenticated user; hosted Supabase authentication is not implemented.
- NMR readiness is currently only a named placeholder analysis module. It must
  not be represented to an agent or user as a computed score.

## Audit sources

- SQLAlchemy models: `backend/app/models.py`
- API request/response schemas: `backend/app/schemas.py`
- Router implementations: `backend/app/project_routes.py`, `workflow_routes.py`,
  `experiment_routes.py`, `chat_routes.py`, and `attachment_routes.py`
- Current architecture documents: `docs/architecture/data-model.md`,
  `docs/architecture/auth-rbac.md`, and `docs/architecture/ai-mcp.md`
