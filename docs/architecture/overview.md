# Architecture Overview

NMR Lab is a local-first notebook for lab procedures, workflow templates, and daily experiment runs.

The current frontend is a Vite React app generated from the accepted Figma design. The backend is a FastAPI API with a local SQLite database for laptop usage. PR 6 adds adapter boundaries for auth, storage, and hosted sync readiness. PR 7 adds a persisted Teams surface for lab chat. Later milestones add hosted Postgres, Supabase auth, Tigris storage, and AI/MCP integrations.

## Layers

- React frontend: pages for home, projects, workflow, calculator, profile, teams, and AI placeholders.
- FastAPI backend: Pydantic schemas, OpenAPI, CRUDL routes, RBAC checks, adapter-backed auth/storage, local sync endpoints, and lab-scoped chat APIs.
- SQLite local database: default laptop persistence.
- Upload storage: local files under `data/uploads`, with metadata shaped for future Tigris storage across workflow, experiment, and chat attachments.
