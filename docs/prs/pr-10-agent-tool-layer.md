# PR 10: Executable Agent Tool Layer

## Summary

Adds an authenticated FastAPI gateway and in-process registry for the supported
agent tools. It extracts their shared application operations from route handlers
so tools reuse backend behavior without direct database access. No LLM, prompt
orchestration, MCP transport, provider key, or scientific calculation is added.

## API

- `GET /api/v1/agent/tools` returns names, descriptions, JSON input/output
  schemas, permission requirements, side effects, confirmation requirements,
  and unavailable NMR tools.
- `POST /api/v1/agent/tools/{tool_name}/invoke` accepts `arguments` and
  `confirmed`, then returns `{ tool_name, ok, data, error }`.
- Invalid inputs, unavailable/unknown tools, missing records, forbidden access,
  and missing write confirmation return stable structured error responses.

## Automated verification

```sh
.venv/bin/python -m pytest \
  backend/tests/test_agent_tools_api.py \
  backend/tests/test_project_and_docs_api.py \
  backend/tests/test_workflow_api.py \
  backend/tests/test_experiment_api.py \
  backend/tests/test_chat_api.py \
  backend/tests/test_ai_api.py
```

## Manual test

1. Start the backend, then open `GET /api/v1/agent/tools`; confirm every
   supported tool exposes schemas and each unavailable NMR tool explains why it
   cannot run.
2. Invoke `get_project` and `search_experiment_notes` with valid arguments;
   verify `ok: true` and structured `data`.
3. Invoke an unavailable tool and malformed input; verify structured errors and
   their HTTP statuses.
4. Invoke `create_note` without `confirmed: true`; verify it returns
   `confirmation_required` and no message is created. Repeat with confirmation,
   then reload the channel and verify the message appears once under the current
   user.

## Manual merge

1. Require backend review for service extraction and tool/error contracts, plus
   lab-domain review for unavailable NMR capabilities.
2. Confirm no model provider, API key, MCP transport, or unsupported NMR
   calculation is introduced.
3. Squash merge with `feat: add agent tool layer`.
