# PR 29: Guided NMR assistant

## Purpose

Make the local Ollama assistant reliably choose and sequence the stored NMR tools without weakening the evidence or permission boundaries.

## Behavior

- The permanent research policy explains ID resolution and the supported multi-step paths for residue shifts, peak assignments, spectrum comparisons, and CSP.
- Ollama receives a compact tool catalog selected from the user's request instead of the full registry.
- Name-based questions begin with the appropriate list operation so later calls use real stored IDs.
- Exact repeated tool calls are stopped, while the same tool remains available for different IDs.
- The assistant landing state suggests representative NMR questions.
- All execution remains read-only and every dataset claim still requires successful persisted tool evidence.

## Manual test

1. Start Ollama, the backend, and the frontend.
2. Ask `List my HSQC spectra` and confirm `list_spectra` appears in the audit.
3. Ask `What shifts are stored for residue M1?` and confirm the audit resolves protein/residue records before reporting stored ppm values.
4. Ask for peak assignments and confirm the assistant does not invent an assignment when none is stored.
5. Ask to compare two named spectra. Confirm it resolves their IDs and either runs the comparison or explicitly reports that the required spectra are unavailable.

## Merge checklist

- Full backend suite passes.
- Production frontend build passes.
- No write tool or direct database access is introduced.
- Squash merge as `feat: guide NMR assistant tool selection`.
