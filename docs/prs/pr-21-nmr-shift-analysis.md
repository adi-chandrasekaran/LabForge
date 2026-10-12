# PR 21: NMR shift analysis

Adds deterministic, read-only comparison of stored chemical shifts between two lab-scoped spectra and a configurable weighted chemical-shift perturbation calculation.

Shifts are matched by the same residue, nucleus, and atom. Comparison returns signed deltas plus unmatched counts. CSP uses `sqrt(sum((nucleus_weight * delta_ppm)^2))`; defaults are reported explicitly as `1H: 1.0` and `15N: 0.154`, and callers may supply positive alternative weights. Every result includes its formula, weights, source spectrum IDs, matched components, and residue identity so no computed value is detached from evidence.

No calculation is persisted and no agent tool is activated in this PR.
