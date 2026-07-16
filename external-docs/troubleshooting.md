# Troubleshooting

## Backend Does Not Start

Confirm Python dependencies are installed:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

Then run:

```bash
npm run backend:dev
```

## Frontend Does Not Start

Run:

```bash
npm install
npm run dev
```

If the frontend loads but shows API errors:

- Make sure the backend is running separately.
- Open `http://127.0.0.1:8017/docs` first.
- If Swagger loads, refresh the frontend.

## Database Issues

The local SQLite database lives at `data/nmr_lab.sqlite3`. Deleting that file resets local data. Do not delete it if you need to preserve experiments.

## Sync Status Looks Stuck

- `SAVED LOCALLY` is expected after edits because hosted sync is still a placeholder.
- Pressing `SYNC` currently records an attempted sync and confirms that the notebook is still operating in local-only mode.
- This is not data loss. Your changes remain in SQLite unless you manually delete the local database.

## Teams Page Does Not Load

- Confirm the backend is running and `http://127.0.0.1:8017/docs` opens.
- In Swagger, verify `GET /api/v1/channels` returns `200`.
- Refresh the frontend after the backend is confirmed healthy.
- If message posting fails, check that the selected image is one of the allowed types: PNG, JPEG, WEBP, GIF, or SVG.
