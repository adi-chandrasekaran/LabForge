# PR 12: NMR Agent Execution Loop

## Scope

This PR makes the read-only NMR research assistant executable through OpenAI's
Responses API. It does not expose `create_note` or any other write operation to
the model.

- `POST /api/v1/agent/conversations/{conversation_id}/runs` persists a user
  request and returns the completed run, answer, evidence IDs, and ordered audit
  calls.
- Context is bounded to the latest ten completed runs in the authenticated
  user's conversation.
- The loop validates provider function calls through PR 3's registry, invokes
  only supported read tools, returns structured result envelopes to the model,
  and permits at most five rounds.
- Tool selection, arguments, outcomes, provider response ID, final answer, and
  stable failures are persisted. Logs omit API keys.
- Final responses require valid JSON and successful same-run evidence for
  retrieved claims. Unavailable answers must explicitly say the data is
  unavailable.

## Environment

Set these only in the backend process environment:

```sh
export NMR_LAB_OPENAI_API_KEY='your-server-only-key'
export NMR_LAB_AGENT_MODEL='gpt-5.5' # optional
npm run backend:dev
```

## Automated checks

```sh
.venv/bin/python -m pytest backend/tests
npm run build
git diff --check
```

Tests use a scripted provider and never call OpenAI.

## Manual test

1. Start the backend with an environment-only OpenAI key, then create a
   conversation with `POST /api/v1/agent/conversations`.
2. Post `{"message":"Which project is ANC2?"}` to that conversation's
   `/runs` route. Confirm its answer follows a retrieval, and retrieve the run
   to inspect tool names, arguments, results, and evidence IDs.
3. Ask for a spectrum, residue shift, or chemical-shift perturbation. Confirm
   the answer explicitly says the required data is unavailable; it must not
   invent a value.
4. Verify an unset key returns `agent_unavailable`, with no provider secret in
   the response or audit record.

## Manual merge checklist

1. Require backend/security review for provider calls, audit data, ownership,
   and stable failures.
2. Require lab-domain review of the scientific-answer safeguards.
3. Confirm production supplies the API key only through server environment
   variables and no model write tool is callable.
4. Squash merge with `feat: add NMR agent execution loop`.
