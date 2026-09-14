# PR 12: NMR Domain Entity Audit

## Summary

Adds the first verified inventory of the application's persisted entities,
relationships, storage representation, and existing CRUD surface. It introduces
no application code, schema, API, agent runtime, or NMR-domain record.

## Review focus

- Verify that `docs/architecture/nmr-domain-entity-inventory.md` accurately
  distinguishes existing workflow-notebook entities from requested NMR entities
  that are not implemented.
- Confirm that future work treats `Note` as currently embedded text and
  `Analysis` as a non-persistent placeholder rather than as established models.
- Confirm that no planned agent tool claims access to absent sample/spectrum/
  assignment data.

## Automated verification

- `git diff --check`
- `.venv/bin/python -m pytest backend/tests/test_foundation.py backend/tests/test_ai_api.py`

## Manual test

1. Review the entity inventory beside `backend/app/models.py` and confirm every
   SQLAlchemy table is either documented as a domain entity or classified as
   operational state.
2. Inspect `backend/app/ai_routes.py`; confirm the NMR readiness entry is a
   static placeholder and has no persisted result model.
3. Inspect the listed router paths and confirm that no route offers CRUD for
   Sample, Protein, Spectrum, Peak, Residue, Ligand, or Assignment.

## Manual merge

1. Confirm the PR contains documentation only and has no migration, model,
   route, or frontend changes.
2. Require review from the lab-domain owner for the entity terminology and from
   the backend owner for the API/relationship inventory.
3. Merge with a squash commit titled `docs: audit current NMR domain entities`.
