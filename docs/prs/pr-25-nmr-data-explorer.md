# PR 25: NMR data explorer

## Summary

Expands **NMR DATA** into a complete workspace with separate **Browse records**
and **Import CSV** views. The explorer reads the same lab-scoped APIs used by
the research assistant, allowing a researcher to verify exactly which records
are available for retrieval.

## Browse behavior

- Summary cards show protein, sample, ligand, and spectrum counts.
- Selecting a protein loads its ordered residue records.
- Selecting a spectrum loads its nuclei, status, peaks, and chemical shifts.
- Selecting a peak loads its assignments, atom names, confidence, and status.
- Samples show type, concentration, and pH; ligands show their identifier or
  molecular formula.
- Empty states distinguish missing data from loading and request failures.
- Refresh preserves valid selections and reloads the current lab inventory.

The existing import workflow remains available under **Import CSV**, and
changing files still invalidates the previous preview.

## Reliability

Application startup now creates and commits the singleton local sync-state row
before requests are served. This prevents simultaneous first writes from
racing to create the same sync record in a fresh SQLite database.

## Verification

- Production frontend build passes.
- All 78 backend tests pass.
- Three Playwright tests cover linked protein/residue/spectrum/peak/assignment/
  shift browsing and both successful and invalid CSV imports.

## Manual merge

Require frontend and NMR-domain review. Confirm that the explorer is read-only
and remains lab-scoped through existing APIs. Squash merge as
`feat: add NMR data explorer`.
