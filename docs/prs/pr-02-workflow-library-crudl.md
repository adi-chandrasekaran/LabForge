# PR 2: Workflow Library CRUDL

## Concept

This milestone turns workflows into persisted reusable templates. ANC2 Batch 1 and Batch 2 become seed data in the workflow library instead of hardcoded frontend state.

## Technical Details

- Added workflow list, read, create, update, delete, and publish endpoints under `/api/v1/workflows`.
- Added step create, update, delete, and reorder endpoints for mainline workflow steps.
- Added persisted `workflow_branches` storage plus branch create, update, delete, and branch-step create endpoints.
- Added seed data for `ANC2 Batch 1` and `ANC2 Batch 2`.
- Added a lightweight schema compatibility path so PR 1 local SQLite databases gain the new branch-step column.
- Integrated the React workflow page with the workflow API so add/edit/branch operations persist through refresh.
- Updated the workflow UI to render every branch track returned by the backend for a step instead of collapsing to the first branch only.

## Testing Protocol

- Backend tests:
  `.venv/bin/python -m pytest backend/tests`
- Playwright demo:
  `npm run test:e2e -- e2e/pr-02-workflow-library.spec.ts`
- Frontend build:
  `npm run build`
- Expected pass criteria:
  ANC2 seed data loads, workflow CRUDL API passes, publish RBAC passes, and the workflow page add/edit/branch flow survives a refresh.

## User-Facing How-To

After this PR, users can open `/workflow`, load ANC2 from the backend, add and edit steps, create one or more troubleshooting branches from a step, and refresh without losing those changes.

## Acceptance Checklist

- [x] Workflow CRUDL endpoints.
- [x] Step CRUDL endpoints.
- [x] Branch track endpoints.
- [x] ANC2 seed data.
- [x] RBAC publish check.
- [x] API tests.
- [x] Playwright workflow CRUDL demo.
- [x] Docs and roadmap updates.

## Roadmap Update Note

`docs/roadmap.md` was updated to mark PR 2 complete and record the workflow-library API surface, browser demo coverage, and documentation updates.
