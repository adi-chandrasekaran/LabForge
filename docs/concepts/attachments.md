# Attachments

Attachments represent photos, gel images, screenshots, and other material linked to workflow steps or experiment step runs.

## Current Behavior

- Workflow-library steps can have image attachments.
- Experiment step runs can have image attachments.
- Attachments are listed with their owning step and previewed in the workflow UI.
- Files are stored locally while metadata is stored in SQLite.

## Storage Split

- Binary file: `data/uploads/{owner_type}/{owner_id}/...`
- Metadata row: `attachments` table

## Why The Split Exists

- Local mode can save files directly on disk.
- Hosted mode can later move file storage to Tigris.
- Workflow and experiment schemas do not need to change when storage backend changes.
