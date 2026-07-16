# PR 1: Backend Foundation, Docs Foundation, And Local Database

## Concept

This milestone establishes the local-first base of NMR Lab Notebook. It creates the backend service, the SQLite storage layer, the first API contract, and the documentation structure that every later PR must update.

## Technical Details

- Backend: FastAPI app in `backend/app`.
- Database: SQLAlchemy ORM with local SQLite at `data/nmr_lab.sqlite3`.
- Initial models: users, projects, reusable workflows, workflow steps, experiments, and attachment metadata.
- Initial routes: `GET /api/v1/health`, `GET /api/v1/me`, and generated OpenAPI at `/openapi.json`.
- Auth: mock local user only. Hosted Supabase auth is documented but intentionally not implemented yet.
- Frontend: existing React app remains available while the backend foundation is added.

## Testing Protocol

- Backend tests: `.venv/bin/python -m pytest backend/tests`.
- OpenAPI validation: backend test confirms foundation routes are present in `/openapi.json`.
- Playwright demo: `npm run test:e2e -- e2e/pr-01-smoke.spec.ts`.
- Expected pass criteria: backend health returns `ok`, mock user returns `professor`, the React app renders, and the demo can reach backend health.

## User-Facing How-To

- Start backend: `npm run backend:dev`.
- Start frontend: `npm run dev`.
- Open API docs at `http://127.0.0.1:8017/docs`.
- Open the app at the Vite URL printed by `npm run dev`.
- Read user docs in `external-docs/getting-started.md`.

## Acceptance Checklist

- [x] `/docs` hierarchy exists.
- [x] `/external-docs` hierarchy exists.
- [x] Roadmap exists and defines all planned PRs.
- [x] FastAPI app exists.
- [x] SQLite initialization exists.
- [x] Pydantic response schemas exist.
- [x] Health route exists.
- [x] Mock current user route exists.
- [x] Backend tests exist.
- [x] Playwright smoke demo exists and passes.
- [ ] Workflow persistence is implemented. Planned for PR 2.

## Roadmap Update Note

`docs/roadmap.md` was created with all planned milestones and updated to mark PR 1 complete after backend tests, frontend build, and the Playwright smoke demo passed.
