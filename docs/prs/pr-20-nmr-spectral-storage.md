# PR 20: NMR spectral storage

Adds lab-scoped Spectrum records and owner-controlled Peak, Assignment, and ChemicalShift storage. Spectra link to Samples and optional Experiments. Peak dimensionality must match the spectrum nuclei. Assignments link peaks to residues with atom names and confidence. Chemical shifts link a spectrum/residue/atom and optionally its source peak, rejecting duplicates.

All routes delegate to `services.nmr_spectral`; no agent adapter or scientific calculation is introduced yet. Endpoints live under `/api/v1/nmr/{spectra|peaks|assignments|chemical-shifts}`.
