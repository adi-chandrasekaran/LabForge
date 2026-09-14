# PR 11: NMR Research Assistant Foundation

## Scope

This PR creates the durable foundation for a future NMR research assistant. It
does not make an OpenAI request, execute a tool loop, add a UI, or permit model
writes.

- SQLite `AgentConversation`, `AgentRun`, and `AgentToolCall` records preserve
  ownership, request/answer metadata, ordered tool-call audits, and safe failure
  details.
- Authenticated conversation and audit read APIs enforce current-user ownership.
- `NMR_LAB_OPENAI_API_KEY` stays server-only. `NMR_LAB_AGENT_MODEL` defaults to
  `gpt-5.5`; `GET /api/v1/agent/status` reports `agent_unavailable` without
  returning a secret when no key is configured.
- The OpenAI Responses provider boundary derives strict function definitions
  from the PR 3 registry and excludes `create_note` and every unavailable tool.
- The final-answer contract requires evidence IDs for retrieved data and an
  explicit unavailable statement where required data does not exist.

## Automated checks

```sh
.venv/bin/python -m pytest backend/tests/test_agent_research_api.py backend/tests/test_agent_tools_api.py
.venv/bin/python -m pytest backend/tests
npm run build
```

## Manual test

1. Start the backend with `npm run backend:dev`.
2. Open `GET /api/v1/agent/status`; without a key, verify it returns
   `available: false` and `code: agent_unavailable` and does not expose a key.
3. `POST /api/v1/agent/conversations` with `{"title":"HSQC review"}`. Retrieve
   it and its `/runs` endpoint; confirm the empty audit history is returned.
4. Inspect `GET /api/v1/agent/tools` and confirm its existing catalog remains
   unchanged. This PR does not expose a model-callable write tool.
5. Optionally restart with `NMR_LAB_OPENAI_API_KEY` set and verify only status
   changes to available; no request is made to the provider.

## Manual merge checklist

1. Require backend review for SQLite ownership, audit persistence, and secret
   handling.
2. Require lab-domain review of the non-fabrication instruction and the
   read-only tool list.
3. Confirm there is no live model request, provider key in a response, MCP
   transport, or agent write capability.
4. Squash merge with `feat: add NMR research assistant foundation`.
