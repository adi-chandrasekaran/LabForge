# PR 23: NMR data import

## Summary

Adds preview-first CSV imports so researchers can load residue, peak,
assignment, and chemical-shift datasets without issuing one request per row.
The import boundary uses the existing NMR domain services and preserves their
lab scope, ownership, relationship, dimensionality, and uniqueness rules.

## API

- `GET /api/v1/nmr/imports` lists supported formats and columns.
- `POST /api/v1/nmr/imports/{entity_type}?dry_run=true` validates a UTF-8 CSV
  without writing.
- Repeat with `dry_run=false` to persist a clean dataset.
- Supported types: `residues`, `peaks`, `assignments`, and `chemical_shifts`.
- Files are limited to 1 MB. Errors include the CSV row, field when available,
  and a stable human-readable explanation.

Assignment `atom_names` use a semicolon inside one CSV cell, for example
`H;N`. Peak positions use `position_1_ppm` through `position_4_ppm`; the number
of populated positions must match the referenced spectrum's nuclei.

## Automated verification

- Preview performs no writes.
- All four supported entity types import through existing services.
- Bad numeric values and missing parents produce row-level errors.
- A file containing any invalid row writes nothing.
- Unsupported, empty, missing-column, and oversized files are rejected.
- Full backend regression suite passes.

## Manual test

1. Create or reuse a protein, sample, and spectrum.
2. Inspect `GET /api/v1/nmr/imports` for the residue format.
3. Preview a two-row residue CSV and confirm `imported_count` is zero.
4. Submit the same file with `dry_run=false` and confirm two IDs are returned.
5. List the protein's residues and confirm both records are present.
6. Submit a file containing an invalid numeric value and confirm no rows from
   that file are created.

## Manual merge

Require backend and NMR-domain review. Confirm that import handlers do not
duplicate persistence logic or bypass lab scope. Squash merge as
`feat: add NMR data import`.
