# Storage

PR 1 creates local storage directories. PR 4 adds upload endpoints. PR 6 adds a storage adapter layer.

Local mode:

- SQLite metadata in `data/nmr_lab.sqlite3`.
- Files in `data/uploads`.
- Both paths can be overridden with `NMR_LAB_DATA_DIR` and `NMR_LAB_UPLOADS_DIR`.
- Attachments are written through the local storage adapter.

Hosted mode:

- Postgres for metadata.
- Tigris for files.
- Attachment records keep `storage_backend`, `local_path`, and `remote_url` so the app can move from local files to object storage later.
- The Tigris adapter is declared but intentionally not implemented yet.
