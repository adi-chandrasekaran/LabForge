# PR 35: Stabilization and polish

## Purpose

Fix reproducible reliability, authorization, and UI-state issues found during the post-agent acceptance audit without changing established workflows or scientific calculations.

## Fixes

- A successful provider retest now updates the assistant's effective availability immediately; a failed retest disables new requests.
- Temporary conversation-restore failures retain the saved conversation instead of silently discarding it. Only a confirmed 404 clears a stale conversation ID.
- NMR detail requests expose API failures instead of presenting failed loads as empty datasets.
- Protein, spectrum, peak, assignment, and shift selection requests ignore stale responses after the user changes selection.
- Refreshing the NMR explorer now refreshes residues, peaks, assignments, and shifts as well as top-level counts.
- Detail panels show loading states and distinguish an unassigned peak from no selected peak.
- Spectrum-analysis results clear when inputs or mode change, and empty comparison/CSP results explain why no table rows appear.
- Re-selecting a removed CSV works, and NMR workspace tabs expose their selected state to assistive technology.
- CSV validation preserves original source row numbers even when earlier rows fail parsing, and continues validating remaining parseable rows.
- Peak, assignment, and chemical-shift updates require ownership of the original spectral record before allowing a move to another parent.
- API errors retain their HTTP status so the UI can distinguish stale resources from temporary failures.

## Manual test

1. Start the merged app with Ollama configured but stopped. Open `/assistant`, start Ollama, click **Test provider connection**, and confirm the input becomes usable without refreshing.
2. Stop Ollama, click the diagnostic again, and confirm the assistant request button becomes disabled.
3. Open `/nmr-data`, switch rapidly between proteins, spectra, and peaks, and confirm details always match the current selection.
4. Click **Refresh records** and confirm nested residues, peaks, assignments, and shifts refresh.
5. Run a spectrum comparison with no matched shifts and confirm the explicit empty-result explanation.
6. Change analysis mode or spectrum selection and confirm the previous result disappears.
7. In **Import CSV**, choose a file, remove it, then choose the same file again and confirm it is accepted.

## Merge checklist

- Full backend suite passes.
- Production frontend build passes.
- Current NMR, agent-integration, provider-diagnostic, and stabilization browser suites pass.
- No scientific formula, tool permission, or write-confirmation boundary changes.
- Squash merge as `fix: stabilize NMR workflows and assistant state`.
