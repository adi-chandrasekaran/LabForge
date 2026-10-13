# PR 28: Human-readable assistant results

## Purpose

Present evidence-backed agent results as concise research summaries instead of raw backend JSON. This changes presentation only: tool execution, permissions, audit persistence, and evidence validation remain authoritative.

## Behavior

- Deterministic fallback answers are formatted by tool type for projects, workflows, experiments, chat records, and the stored NMR domain.
- Scientific values retain their units, including ppm, concentration, pH, and confidence.
- Internal identifiers and full raw records are omitted from the main answer unless they are scientifically meaningful.
- Raw tool arguments and results remain available under **Evidence and tool audit**.
- Empty retrievals explicitly report that no matching records were found.
- The assistant page preserves line breaks so lists remain readable.

## Manual test

1. Run Ollama with `llama3.2`, then start the backend with `NMR_LAB_AGENT_PROVIDER=ollama` and the frontend normally.
2. Open `/assistant` and ask `List all my projects`.
3. Confirm the answer is a short bulleted list with project titles, codes, status, and counts—not a raw JSON object.
4. Expand **Evidence and tool audit** and confirm the original `list_projects` result is still present.
5. Ask for stored spectra or residue shifts and confirm nuclei and ppm values remain visible.

## Merge checklist

- Backend tests pass.
- Frontend production build passes.
- Review confirms summaries use only fields present in successful tool results.
- Squash merge as `feat: add human-readable assistant results`.
