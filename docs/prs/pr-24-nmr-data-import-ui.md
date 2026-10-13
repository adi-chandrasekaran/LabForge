# PR 24: NMR data import UI

## Summary

Adds an **NMR DATA** workspace that matches the existing LabForge navigation,
typography, colors, panels, and confirmation patterns. Researchers can select
one of the four supported CSV formats, download its empty template, preview a
file against the backend validation contract, correct row-level errors, and
explicitly confirm a clean import.

## User flow

1. Open **NMR DATA** from the sidebar.
2. Select residues, peaks, assignments, or chemical shifts.
3. Review required and optional columns or download a template.
4. Choose a UTF-8 CSV file up to 1 MB.
5. Select **Preview validation**. This step does not write records.
6. Review total, valid, and error counts plus row-level error details.
7. Select **Import N rows**, then confirm the write in the dialog.
8. Review the success message containing the persisted row count.

Changing the dataset type or selected file clears the prior preview so a stale
validation result can never authorize a different file.

## Verification

- Production frontend build passes.
- Playwright confirms a two-row residue file previews, requires confirmation,
  imports successfully, and is visible through the backend API.
- Playwright confirms an invalid file displays its row error and cannot be
  imported.

## Manual merge

Require frontend and NMR-domain review. Confirm that the UI always previews
before enabling import and that changing the file invalidates the preview.
Squash merge as `feat: add NMR data import UI`.
