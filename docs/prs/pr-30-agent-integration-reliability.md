# PR 30: Agent integration reliability

## Purpose

Complete the user-facing NMR assistant workflow with recoverable conversation state, readable failures, deterministic audit visibility, provider-independent browser coverage, and a single local setup guide.

## Behavior

- The active conversation is restored after a browser refresh, including full ordered tool-call evidence.
- **New conversation** clears the active browser conversation without deleting durable backend audit history.
- The interface explains when it is restoring history or retrieving evidence.
- Structured backend errors are shown as readable messages instead of raw JSON.
- Browser tests verify restore, reset, send, evidence display, and failure behavior with a mocked provider; CI does not require Ollama or a paid API.
- `docs/agent-local-setup.md` documents the supported Ollama startup, verification, storage boundary, and common port/configuration failures.

## Manual test

1. Follow `docs/agent-local-setup.md` and open `/assistant`.
2. Click **Test provider connection** and confirm the diagnostic succeeds.
3. Ask `What shifts are stored for residue M1?` and confirm the answer contains only stored values.
4. Expand **Evidence and tool audit** and confirm the successful tools and arguments appear in execution order.
5. Refresh the browser and confirm the question, answer, and audit are restored.
6. Click **New conversation** and confirm the empty assistant screen appears.
7. Stop Ollama, restart the backend if necessary, and confirm a failed request is rendered as a readable message rather than JSON. Restart Ollama afterward.

## Merge checklist

- Full backend test suite passes.
- Production frontend build passes.
- Agent browser reliability tests pass without a live model.
- No API keys, write tools, or direct database access are introduced.
- Squash merge as `feat: complete NMR assistant integration reliability`.

