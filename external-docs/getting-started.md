# Getting Started

NMR Lab Notebook runs locally with a React frontend and a FastAPI backend.

## Start The Backend

```bash
npm run backend:dev
```

Open API docs at `http://127.0.0.1:8017/docs`.

## Start The Frontend

```bash
npm run dev
```

Open the URL printed by Vite. The app currently uses mock local identity for Chen, Y.

## Local Save And Sync Status

The sidebar footer shows the current local save state.

- `LOCAL IDLE` means there are no pending local changes beyond what is already saved in SQLite.
- `SAVED LOCALLY` means one or more changes were written locally and are waiting for future hosted sync support.
- The `SYNC` button is present now as a placeholder. It confirms that hosted sync is planned, but it does not push to a server yet.

## What Works Now

- Health route.
- Mock current user route.
- SQLite database initialization.
- Workflow library persistence and ANC2 seed data.
- Experiment instantiation and progress tracking.
- Step photo upload, preview, and delete.
- Home, Profile, Projects, Workflow, and Docs pages backed by the API.
- Local save/sync status in the sidebar.
- Teams channels with persisted local messages and image attachments.
- Engineering and user documentation.
