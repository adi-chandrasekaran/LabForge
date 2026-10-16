# Local NMR research assistant setup

The recommended no-cost local provider is Ollama. It runs the model on your computer, requires no API key, and does not use OpenAI or Gemini billing.

## One-time setup

Install Ollama, then download the configured model:

```bash
ollama pull llama3.2
ollama list
```

`llama3.2` must appear in the list. The Ollama desktop app normally starts its local service automatically. If `ollama serve` says port `11434` is already in use, the service is already running; do not start another copy.

## Start LabForge

Use two terminal windows from the LabForge repository.

Terminal 1 — backend:

```bash
export NMR_LAB_AGENT_PROVIDER=ollama
export NMR_LAB_OLLAMA_MODEL=llama3.2
npm run backend:dev
```

Terminal 2 — frontend:

```bash
npm run dev
```

Open `http://localhost:5173/assistant`. The badge should show `ollama · ready`. Use **Test provider connection** for a live model check before asking a scientific question. A successful check says **Provider ready** only after the configured model produces a real response. Failures identify whether Ollama is unavailable, the model is missing, configuration is required, or the provider returned another error, and show the next corrective action.

## Verify from the terminal

```bash
curl http://127.0.0.1:8000/api/v1/agent/status
curl -X POST http://127.0.0.1:8000/api/v1/agent/provider-diagnostic
```

The status endpoint checks configuration and local model availability. The diagnostic endpoint makes a small provider request, so it is the stronger end-to-end check.

## What the assistant stores

- Conversation and run audit records are stored in LabForge's local SQLite database.
- The browser remembers only the active conversation ID so the conversation can be restored after refresh.
- **New conversation** clears the active browser conversation and starts a new one; it does not delete historical audit records.
- Each answer exposes its ordered evidence and tool audit. Experimental claims must be backed by successful tool calls.

## Troubleshooting

### `agent unavailable`

Stop the backend and restart it from the same terminal in which these were exported:

```bash
export NMR_LAB_AGENT_PROVIDER=ollama
export NMR_LAB_OLLAMA_MODEL=llama3.2
npm run backend:dev
```

Environment variables set in a different terminal are not inherited by the running backend.

### Port 8000 is already in use

Find the existing backend:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

If it is an older LabForge process, stop it with `kill PID`, replacing `PID` with the number printed by `lsof`, and restart the backend. Do not type angle brackets around the number.

### Ollama port 11434 is already in use

This usually means Ollama is already running. Confirm it instead of starting a second server:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
```

### Model is missing

```bash
ollama pull llama3.2
```

Then restart the LabForge backend and use **Test provider connection** again.

### Assistant returned an unavailable answer

Expand **Evidence and tool audit**. An unavailable answer is correct when the requested record is not stored or a required tool returned no match. Add or import the missing NMR record, then ask again.
