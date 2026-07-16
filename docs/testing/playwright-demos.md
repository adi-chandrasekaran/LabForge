# Playwright Demos

Playwright tests are also demos. They should run with trace/video enabled in CI or debug mode and should exercise visible user flows.

PR 1 demo:

- Open the React app.
- Verify the sidebar shell loads.
- Verify backend health is reachable.

Planned command:

```bash
npm run test:e2e
```

PR 2 demo:

- Open `/workflow`.
- Load ANC2 from the API-backed workflow library.
- Insert a step after Dialysis in Batch 1.
- Edit the inserted step.
- Create a troubleshooting branch from the inserted step.
- Refresh and verify the workflow mutations persisted.

PR 3 demo:

- Open `/workflow`.
- Start a new ANC2 experiment run.
- Edit the Batch 1 `Dialysis` step inside the experiment snapshot.
- Save a unique note and refresh the page.
- Verify the experiment note persisted and the library view remains separate.

PR 4 demo:

- Open `/workflow`.
- Upload an image to a workflow-library step.
- Delete that image and verify the editor updates immediately.
- Start a new ANC2 experiment run.
- Upload an image to the Batch 1 `Dialysis` experiment step.
- Delete that image and verify the experiment editor updates immediately.

PR 5 demo:

- Open `/`.
- Verify Home loads persisted summary cards and recent activity from the API.
- Open `/profile`.
- Verify the profile page loads backend-backed identity and expertise data.
- Open `/projects`.
- Verify ANC2 loads from persisted backend data.
- Create a new project and refresh the page.
- Verify the new project persists after reload.
- Open `/docs`.
- Load the `Workflow Library` guide from the API-backed external docs surface.

PR 6 demo:

- Open `/`.
- Verify the sidebar shows a local sync state.
- Create a new project from `/projects`.
- Verify the sidebar sync state changes to `SAVED LOCALLY`.
- Press the sync button.
- Verify the UI reports that hosted sync is not active yet and local changes remain saved.

PR 7 demo:

- Open `/teams`.
- Create a new channel.
- Post a message that references `ANC2 Batch 1`.
- Attach an image to that message.
- Refresh the page.
- Verify the new channel, message body, and image still appear.

PR 8 demo:

- Open `/ai-model`.
- Verify the AI page loads without a frontend API error.
- Verify the AI settings summary shows placeholder or disabled states.
- Verify the analysis module registry shows three placeholder modules.
- Verify the MCP summary shows a non-zero tool count.
- Verify the MCP tool preview includes `/api/v1/ai/settings`.
