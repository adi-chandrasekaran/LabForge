# Fly.io, Supabase, And Tigris Plan

Hosted mode is planned after local-first persistence works.

- Fly.io hosts the FastAPI backend.
- Supabase provides auth and Postgres.
- Tigris stores photos and other files.
- Local mode remains available for laptop-only usage.

PR 6 hosted-readiness work already in place:

- Config fields exist for app mode, database backend, auth backend, and storage backend.
- Local auth and storage implementations already sit behind adapter interfaces.
- Sync status already distinguishes local-only mode from future hosted-ready mode.

Still missing before real hosted deployment:

- Supabase JWT verification and session handling.
- Postgres-backed runtime configuration and migrations.
- Tigris upload/download implementation.
- Real push/pull sync logic between SQLite and hosted storage.
