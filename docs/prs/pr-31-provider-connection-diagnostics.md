# PR 31: Provider connection diagnostics

## Purpose

Make **Test provider connection** authoritative and actionable before the final acceptance pass begins.

## Behavior

- Ollama diagnostics first check that the local service responds and the configured model is installed.
- A second minimal chat request proves that the model can load and generate a response.
- The API returns a stable diagnostic state, safe code, explanation, and corrective action.
- The assistant page clearly distinguishes ready, Ollama unavailable, model missing, configuration required, and provider issue states.
- The ordinary status request remains lightweight and does not load the model; only the explicit diagnostic button runs generation.
- Provider errors never expose API keys or raw internal exceptions.

## Manual test

1. Start Ollama, the backend, and frontend, then open `/assistant`.
2. Click **Test provider connection** and confirm **Provider ready** appears.
3. Quit Ollama, click the button again, and confirm **Ollama unavailable** with an instruction to open Ollama.
4. Configure a model name that is not installed, restart the backend, and confirm **Ollama model missing** with the exact `ollama pull` command.
5. Restore the correct model configuration and confirm the ready state again.

## Merge checklist

- Backend tests pass.
- Production frontend build passes.
- Provider diagnostic browser tests pass without a live model.
- No secrets or raw provider errors are returned.
- Squash merge as `fix: make provider diagnostics actionable`.

