# PR 13: Gemini Agent Provider

## Scope

This PR adds Gemini 2.5 Flash as the default development provider for the
existing read-only NMR research assistant. It preserves the OpenAI provider,
agent tool registry, validation, audit records, evidence requirements, and
five-round execution limit.

## Configuration

Set configuration only in the backend process environment:

```sh
export NMR_LAB_AGENT_PROVIDER='gemini'
export NMR_LAB_GEMINI_API_KEY='server-only-key'
export NMR_LAB_GEMINI_MODEL='gemini-2.5-flash'
```

Use `NMR_LAB_AGENT_PROVIDER='openai'` with the existing OpenAI variables to
select the prior provider. Keys are never returned by an API or written to the
agent audit log.

## Behavior

- Gemini receives the same permanent non-fabrication instructions and
  read-only function catalog as OpenAI.
- Gemini function calls pass through the existing PR 3 registry. `create_note`
  and unavailable NMR tools cannot be invoked by the model.
- Provider errors are stable and intentionally do not expose provider details.
- Gemini free-tier availability and limits are external account concerns; all
  automated tests use a fake provider and do not send data to Gemini.

## Automated checks

```sh
.venv/bin/python -m pytest backend/tests
npm run build
git diff --check
```

## Manual test

1. Set a Gemini API key only in the backend process environment and start the
   backend.
2. Check `GET /api/v1/agent/status`; verify it reports `gemini` and the
   configured model without exposing a key.
3. Create a conversation and ask a project or experiment question. Verify the
   completed audit shows a read-only tool call before a retrieved answer.
4. Ask for a spectrum or chemical-shift value. Verify the assistant says the
   required data is unavailable rather than inventing a value.
5. Restart with `NMR_LAB_AGENT_PROVIDER='openai'` and verify the existing
   provider remains selectable.

## Manual merge checklist

1. Require backend/security review for provider configuration, key handling,
   function-call translation, and safe errors.
2. Require lab-domain review of continued non-fabrication and read-only rules.
3. Confirm no Gemini key, raw provider error, image data, or write tool is
   exposed.
4. Squash merge with `feat: add Gemini agent provider`.
