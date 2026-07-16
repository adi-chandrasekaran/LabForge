# Local-First Sync

The current implementation persists to SQLite on the user's laptop and tracks local save state in a dedicated `sync_state` record.

Current behavior:

- Every write route records a local change and increments `pending_changes`.
- The sidebar footer shows whether the app is idle or has locally saved changes waiting for hosted sync.
- `GET /api/v1/sync/status` exposes local sync status, backend mode, and backend adapter choices.
- `POST /api/v1/sync/push` is a placeholder that records an attempted sync without clearing local changes.

Planned next concepts:

- Server-issued hosted IDs for mirrored records.
- Conflict-safe version fields for workflow templates and experiment runs.
- Push/pull sync flows once Fly.io, Supabase, Postgres, and Tigris are active.
