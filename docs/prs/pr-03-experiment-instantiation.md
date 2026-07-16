# PR 3: Experiment Instantiation And Progress Tracking

## Concept

This milestone separates reusable workflow templates from real experiment runs. An experiment is a dated instantiation of one or more workflows with its own progress, observations, and step states.

## Technical Details

- Added experiment CRUDL endpoints under `/api/v1/experiments`.
- Added `POST /api/v1/experiments/instantiate` to create a dated experiment from one or more workflow templates.
- Added `ExperimentWorkflowRun` and `ExperimentStepRun` snapshot entities so experiments retain the workflow version and step payload that existed at instantiation time.
- Added `PATCH /api/v1/experiments/{experiment_id}/workflow-runs/{workflow_run_id}/steps/{step_run_id}` so experiment step runs can diverge from the template.
- Updated the React workflow page to show a live experiment panel above the ANC2 library workflows and to edit experiment step runs through the same side-sheet editor.

## Testing Protocol

- Backend:
  - `.venv/bin/python -m pytest backend/tests`
  - Covers experiment create/list/get/delete, ANC2 instantiation, step-run updates, persistence, and template immutability.
- Frontend build:
  - `npm run build`
- Playwright demo:
  - `npm run test:e2e -- e2e/pr-03-experiment-instantiation.spec.ts`
  - Starts a new ANC2 run, edits Batch 1 Dialysis in the experiment snapshot, reloads, and verifies the saved note remains visible.

## User-Facing How-To

Users can open `/workflow`, start a new ANC2 experiment run, review Batch 1 and Batch 2 as experiment snapshots, update a live step such as Dialysis, and keep those observations separate from the ANC2 library template.

## Acceptance Checklist

- [x] Experiment CRUDL.
- [x] Instantiate from workflow endpoint.
- [x] Workflow run snapshots.
- [x] Step run status and notes.
- [x] Template immutability tests.
- [x] Playwright experiment demo.
- [x] Docs and roadmap updates.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 3 complete and records the experiment API, workflow page experiment panel, and demo coverage added in this milestone.
