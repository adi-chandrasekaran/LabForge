# PR 6: Local Sync Abstraction And Hosted Readiness

## Concept

This milestone prepares the app for local-first operation today and hosted Fly.io/Supabase/Tigris deployment later without rewriting core application code.

## Technical Details

- Added environment-based config for local SQLite and future hosted Postgres, plus overrideable local data and upload directories.
- Added storage adapter interfaces for local files and future Tigris objects.
- Added auth adapter interfaces for mock local auth and future Supabase JWT.
- Added persistent `sync_state` tracking in SQLite plus placeholder sync routes.
- Added global frontend sync status in the sidebar footer, with a visible local save state and a placeholder sync button.

## Testing Protocol

- Backend/API:
  ```bash
  .venv/bin/python -m pytest backend/tests
  ```
- Frontend build:
  ```bash
  npm run build
  ```
- Playwright demo:
  ```bash
  npm run test:e2e -- e2e/pr-06-sync-status.spec.ts
  ```
- Expected pass criteria:
  - Sync status defaults to local idle.
  - Any workflow/project/experiment/attachment mutation increases pending local changes.
  - Placeholder sync attempts do not clear local changes and report hosted sync as not yet implemented.
  - The sidebar footer updates after a real UI mutation.

## User-Facing How-To

After this PR lands:

- Users can see whether the notebook is idle or has unsynced local changes.
- Users can create or edit data and immediately see the sync status update in the sidebar.
- Users can press the sync button and get a clear placeholder response that hosted sync is planned but not active yet.
- Developers can switch config toward hosted backends later without rewriting route code.

## Acceptance Checklist

- [x] Config abstraction.
- [x] Storage abstraction.
- [x] Auth abstraction.
- [x] Sync placeholder routes.
- [x] Local save/sync UI status.
- [x] Tests and e2e demo.
- [x] Hosted deployment docs.
- [x] Roadmap update.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 6 complete and points to the new sync/status API, frontend sidebar status surface, and hosted-readiness docs.
