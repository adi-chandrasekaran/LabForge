# ADR 0001: Local-First SQLite

Status: Accepted

NMR Lab starts with SQLite because students need a laptop-local notebook that works before hosted sync is available.

Consequences:

- Local demos and tests are simple.
- Hosted Postgres must be introduced through a database URL abstraction.
- Sync behavior is a later milestone.
