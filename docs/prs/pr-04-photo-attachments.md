# PR 4: Photo Attachments

## Concept

This milestone lets users attach visual evidence to workflow steps and experiment step runs, including gels, column photos, screenshots, and notebook images.

## Technical Details

- Store uploaded image files under `data/uploads/{owner_type}/{owner_id}`.
- Persist attachment metadata in SQLite using the existing `Attachment` table.
- Added upload/list endpoints for workflow steps and experiment step runs.
- Added `DELETE /api/v1/attachments/{attachment_id}` so users can remove uploaded evidence cleanly.
- Added `GET /api/v1/attachments/{attachment_id}/content` to stream stored files back to the UI.
- Added image-only content type validation and explicit owner linkage for both workflow steps and experiment step runs.
- Added upload, preview, and delete controls inside the workflow step side-sheet editor and attachment previews inside expanded inner schematics.

## Testing Protocol

- Backend:
  - `.venv/bin/python -m pytest backend/tests`
  - Covers workflow-step upload/list/delete/content, experiment-step upload/list/delete, owner linkage, invalid content-type rejection, and serializer embedding.
- Frontend build:
  - `npm run build`
- Playwright demo:
  - `npm run test:e2e -- e2e/pr-04-photo-attachments.spec.ts`
  - Uploads one image to a workflow-library step and one image to an experiment step run, deletes both, and verifies the UI reflects those changes.

## User-Facing How-To

Users can open a workflow or experiment step editor, upload a gel image or screenshot, remove an outdated image if needed, close and reopen the step, and still see the correct attachment state after refresh.

## Acceptance Checklist

- [x] Local upload storage.
- [x] Attachment metadata endpoints.
- [x] Workflow step attachment support.
- [x] Experiment step run attachment support.
- [x] Frontend upload/preview/delete.
- [x] API tests.
- [x] Playwright upload/delete demo.
- [x] Docs and roadmap updates.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 4 complete and ADR 0003 records the current local storage and API abstraction behavior.
