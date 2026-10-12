# PR 19: NMR domain foundation

This PR introduces the first real NMR data entities: Sample, Protein, Ligand, and Residue.

Samples belong to a lab and optional project, have scientific preparation fields, and reference proteins and ligands through explicit association records. Proteins store constructs, sequences, isotope labels, and residues. Ligands store identifiers and chemical descriptors. Residues have protein-scoped sequence positions and reject duplicates.

All CRUD routes use `backend.app.services.nmr_domain`; routes and future agent tools do not implement database logic themselves. Reads are scoped to the authenticated user's lab, and only the record owner may modify an entity. Inputs validate pH, non-negative concentrations and volumes, positive molecular weights, and residue codes.

Endpoints are under `/api/v1/nmr/{samples|proteins|ligands|residues}`. Spectrum, Peak, Assignment, chemical shifts, and calculations remain intentionally out of scope for the next PRs.
