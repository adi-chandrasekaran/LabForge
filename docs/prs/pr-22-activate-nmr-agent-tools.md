# PR 22: Activate NMR agent tools

Activates read-only, lab-scoped agent tools for samples, proteins, ligands, residues, spectra, peaks, assignments, chemical shifts, spectrum comparison, and CSP. Each handler delegates to the same NMR services used by the HTTP API; no handler queries models or calculates scientific values independently.

The provider function catalog now includes these tools. Structured calculation results always include stored components, formula, weights, and source spectrum IDs. All write operations remain excluded except the existing confirmation-gated workflow proposal mechanism.
