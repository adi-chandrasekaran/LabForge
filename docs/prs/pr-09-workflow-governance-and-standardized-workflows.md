# PR 9: Four Workflow Functionality Fixes

## Concept

This milestone completes the requested workflow cleanup as four PR-sized slices:

1. deterministic local project cleanup
2. permissive local demo deletion for editable content
3. standardized workflow authoring
4. project-tabbed experimental workflows

The app now separates editable project-owned experimental workflows from reusable standardized workflows. Standardized workflows remain reusable library records, while inserted standardized content becomes an editable copy inside the target experimental workflow.

## Technical Details

- Added `project_id` to persisted workflows and migration support for existing SQLite databases.
- Added deterministic stale demo cleanup while keeping the three approved showcase projects:
  - ANC2 Protein Purification
  - RPC10 Purification Process And Troubleshooting
  - CCL20 Transformation And Culture
- Seeded project-linked experimental workflows:
  - ANC2 Batch 1 and Batch 2
  - RPC10 purification/troubleshooting
  - CCL20 transformation/culture
- Creating a project now creates a blank editable experimental workflow for that project.
- Local mock-user mode can delete project/workflow/step/branch records for localhost demo use.
- Project deletion cascades linked workflows, runs, steps, branches, members, and attachments.
- Added workflow member serialization to workflow API reads.
- Added workflow membership update support on workflow patch.
- Added owner/editor permission checks for:
  - workflow update
  - workflow delete
  - workflow publish
  - workflow step CRUDL
  - workflow branch CRUDL
- Added workflow list filters for:
  - `tag`
  - `library_state`
  - `visibility`
- Seeded standardized library workflows:
  - Reverse Nickel Chromatography
  - Ion Exchange Chromatography
- Seeded showcase project/workflow records for:
  - ANC2
  - RPC10
  - CCL20
- Added frontend standardized workflows page and route.
- Added standardized workflow creation from the Standardized tab.
- Added owner/editor step authoring for standardized workflows:
  - add step
  - edit step details, procedure, inputs, outputs, parameters, and notes
  - delete step
  - add/delete branch
- Replaced the ANC2-only workflow page with project tabs loaded from projects.
- Removed the duplicated ANC2 experiment-run framing from the primary workflow UX.
- Added standardized workflow dropdown insertion to mainline add-step and branch flows.
- Added `Standardize` action to copy an experimental workflow into the standardized workflow library.

## Testing Protocol

### Backend

Run:

```bash
.venv/bin/python -m pytest backend/tests
```

Expected:

- all 32 tests pass
- standardized workflow filters return seeded library workflows
- workflow member data is present in API responses
- project list starts from the three approved showcase projects on clean local seed
- local demo deletes return success and cascade child records
- standardized snapshot/copy insertion endpoints work

### Frontend

Run:

```bash
npm run build
```

Expected:

- production build succeeds

### Playwright Browser Demo

Run:

```bash
NMR_LAB_DATA_DIR=/private/tmp/nmr-lab-four-pr-fixes-data \
NMR_LAB_UPLOADS_DIR=/private/tmp/nmr-lab-four-pr-fixes-uploads \
PLAYWRIGHT_BACKEND_PORT=8017 \
PLAYWRIGHT_FRONTEND_PORT=4174 \
npm run test:e2e -- e2e/pr-09-four-workflow-functionality-fixes.spec.ts
```

Expected:

- the demo passes
- Projects shows only ANC2, RPC10, and CCL20 on a clean seeded DB
- creating a project creates a workflow tab
- RPC10 and CCL20 tabs render distinct seeded workflow content
- a dummy standardized workflow can be created, edited with a step, and deleted
- Ion Exchange can be inserted into an experimental workflow
- an experimental workflow can be standardized into the library
- deleting the temporary project succeeds

### Manual Browser Demo

1. Start backend on the NMR Lab backend port.
2. Start frontend.
3. Open `/projects` and confirm only ANC2, RPC10, and CCL20 are shown before creating anything new.
4. Create a new project, then delete it and confirm the delete modal appears first.
5. Open `/workflow`.
6. Switch the ANC2, RPC10, and CCL20 project tabs and confirm each tab shows different workflow content.
7. Create another new project from `/projects`, return to `/workflow`, and confirm it has a blank workflow tab.
8. On `/workflow`, use `+ Add step`, switch source to standardized workflow, and insert Ion Exchange or Reverse Nickel.
9. On `/workflow`, use the branch control, switch source to standardized workflow, and insert a standardized troubleshooting branch.
10. Click `Standardize` on an experimental workflow and confirm the new workflow appears under `/standardized-workflows`.
11. Open `/standardized-workflows`, create a dummy workflow, add/edit/delete a step, then delete the dummy workflow.

## User-Facing How-To

After this milestone, the user can:

- open Projects and work from the three intended showcase projects without stale demo clutter
- create a project and automatically get a blank editable experimental workflow tab
- delete local demo projects, workflows, workflow steps, standardized workflows, and branches after confirmation
- switch `/workflow` across project tabs
- edit ANC2, RPC10, and CCL20 experimental workflows
- create new standardized workflows from scratch
- add, edit, and delete standardized workflow steps as owner/editor
- insert a standardized workflow into an experimental workflow as an editable copy
- standardize a successful experimental workflow into the reusable library

## Acceptance Checklist

- [x] Workflow membership data is returned by the API
- [x] Workflow edit/delete/publish routes are permission-gated
- [x] Standardized workflows have a dedicated frontend page
- [x] Reverse Nickel and Ion Exchange standardized workflows are seeded
- [x] Only ANC2, RPC10, and CCL20 appear on a clean local showcase seed
- [x] Local demo deletion works for projects, workflows, steps, and branches
- [x] Project cards can be deleted after confirmation
- [x] Standardized workflows can be created from the Standardized tab
- [x] Owners/editors can edit standardized workflow steps
- [x] `/workflow` is project-tabbed
- [x] RPC10 and CCL20 have seeded experimental workflows
- [x] New projects get blank experimental workflow tabs
- [x] Standardized workflows can be inserted through add-step and branch flows
- [x] Experimental workflows can be standardized into the library
- [x] Backend tests pass
- [x] Frontend build passes
- [x] Focused Playwright demo passes
- [x] Roadmap updated
- [x] External docs updated
- [ ] Full audit history and app-wide search remain future scope

## Roadmap Update Note

`docs/roadmap.md` now marks PR 9 complete with deterministic showcase cleanup, local demo deletion, standardized authoring, project-tabbed workflows, standardized insertion, and standardize-copy coverage.
