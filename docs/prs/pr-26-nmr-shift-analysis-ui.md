# PR 26: NMR shift-analysis UI

## Summary

Adds **Analyze shifts** to the NMR data workspace. Researchers can select a
reference and comparison spectrum, inspect matched chemical-shift deltas, and
calculate residue-level chemical-shift perturbation (CSP) with explicit nucleus
weights.

## Scientific boundary

- Results come exclusively from the existing NMR analysis service.
- The frontend never estimates missing shifts or performs its own calculation.
- A spectrum cannot be compared with itself.
- The default CSP weights are `1H = 1.0` and `15N = 0.154`; users can change
  them to positive values before calculation.
- The returned formula and component deltas are shown alongside every result.
- Reference-only and comparison-only counts make unmatched data explicit.

## User flow

1. Open **NMR DATA**, then **Analyze shifts**.
2. Select two different spectra containing stored chemical shifts.
3. Run **Shift deltas** to inspect atom-level reference, comparison, and delta
   values.
4. Select **CSP**, review the nucleus weights, and calculate the residue-level
   perturbation.

## Verification

- Production frontend build passes.
- Playwright creates two spectra with stored `1H` and `15N` shifts, verifies
  deltas of `0.100` and `1.000` ppm, and verifies CSP `0.1836` ppm from the
  backend service.

## Manual merge

Require frontend and NMR-domain review. Confirm all displayed values originate
from API results. Squash merge as `feat: add NMR shift analysis UI`.
