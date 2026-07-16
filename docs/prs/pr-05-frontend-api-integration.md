# PR 5: Frontend API Integration And State Cleanup

## Concept

This milestone replaces hardcoded prototype state with real API-backed data while preserving the Figma visual direction.

## Technical Details

- Add a typed frontend API client.
- Replace hardcoded notebook state with backend calls across Home, Profile, Projects, Workflow, Experiments, and Docs.
- Add persisted project list/create/read routes and wire the `Projects` page to them.
- Add dashboard and profile summary routes and wire the `Home` and `Profile` pages to them.
- Add external-docs list/read routes and expose them through a new in-app `Docs` page.
- Bind the sidebar footer to `/api/v1/me`.
- Add loading, empty, and error states.
- Fix workflow editor save flow so async persistence completes before the edit dialog closes.
- Align the workflow UI with the branch-track API by rendering every branch track attached to a step.
- Preserve current dark terminal-style UI and light-mode support.
- Add in-app documentation entry points backed by `/external-docs`.

## Testing Protocol

- Frontend build: `npm run build`.
- Backend regression: `.venv/bin/python -m pytest backend/tests`.
- Playwright demo covers persisted Home, Profile, Projects, and Docs behavior:
  - `npm run test:e2e -- e2e/pr-05-projects-and-docs.spec.ts`
- Full PR 1 through PR 5 browser regression:
  - `npm run test:e2e -- e2e/pr-01-smoke.spec.ts e2e/pr-02-workflow-library.spec.ts e2e/pr-03-experiment-instantiation.spec.ts e2e/pr-04-photo-attachments.spec.ts e2e/pr-05-projects-and-docs.spec.ts`

## User-Facing How-To

Users can open the app and see persisted summary data on Home, review their backend-backed identity and activity on Profile, create projects on the `Projects` page and revisit them after refresh, and open API-served help content from the `Docs` page. Workflow and experiment editing now also wait for saves to finish before dismissing the editor.

## Acceptance Checklist

- [x] API client.
- [x] Persisted projects page.
- [x] Persisted workflow page.
- [x] Persisted experiment flows.
- [x] Persisted home page.
- [x] Persisted profile page.
- [x] In-app docs entry points.
- [x] Loading/error states.
- [x] Build and e2e tests for the projects/docs slice.
- [x] Full PR 1 to PR 5 verification after integration cleanup.
- [x] Docs and roadmap updates.

## Roadmap Update Note

`docs/roadmap.md` now marks PR 5 complete with persisted Home, Profile, Projects, Workflow, Experiment, and Docs coverage plus the final PR 1 to PR 5 verification pass.
