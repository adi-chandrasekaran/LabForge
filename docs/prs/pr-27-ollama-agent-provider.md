# PR 27: Local Ollama agent provider

## Summary

Adds Ollama as a third provider for the existing research-assistant execution
loop. This removes API billing and key requirements during local development
while preserving the same read-only tools, validation, audit records,
five-round limit, evidence citations, and non-fabrication policy.

## Configuration

Start Ollama, then configure the backend process:

```sh
export NMR_LAB_AGENT_PROVIDER='ollama'
export NMR_LAB_OLLAMA_MODEL='llama3.2'
npm run backend:dev
```

`NMR_LAB_OLLAMA_BASE_URL` optionally changes the default
`http://127.0.0.1:11434`. No API key is needed. OpenAI and Gemini remain
available through their existing configuration.

## Behavior

- Ollama receives the permanent system instruction and all read-only function
  definitions from the shared registry.
- Tool requests return through the existing validation and audit loop.
- Tool outputs return as Ollama `tool` messages for additional reasoning.
- Repeated requests for an already executed tool are intercepted and converted
  into final-answer synthesis; distinct follow-up tools remain available, with
  a maximum of three Ollama retrieval rounds before forced synthesis.
- Final output must satisfy the existing strict answer/evidence schema.
- Status and provider diagnostics verify that Ollama is reachable and the
  configured model is installed.
- Connection and missing-model errors contain actionable local commands and no
  secrets.

## Verification

- Provider mapping tests cover function schemas, calls, tool-result messages,
  final content, successful preflight, and missing-model diagnostics.
- No automated test downloads a model or calls a hosted provider.
- Full backend regression and frontend production build pass.

## Manual merge

Require backend/security review of the localhost transport and lab-domain
review of the unchanged evidence policy. Squash merge as
`feat: add local Ollama agent provider`.
