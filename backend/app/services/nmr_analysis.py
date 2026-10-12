from __future__ import annotations

from collections import defaultdict
from math import sqrt

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ChemicalShift, Residue, User
from ..schemas import ChemicalShiftPerturbationRead, ChemicalShiftPerturbationRequest, ResiduePerturbationRead, ShiftDeltaRead, SpectrumComparisonRead, SpectrumComparisonRequest
from . import nmr_spectral


def _spectra(db: Session, user: User, reference_id: str, comparison_id: str):
    if reference_id == comparison_id: raise HTTPException(422, "Reference and comparison spectra must be different")
    return nmr_spectral.get_spectrum(db,user,reference_id), nmr_spectral.get_spectrum(db,user,comparison_id)


def _shift_map(db: Session, spectrum_id: str, nuclei: list[str] | None) -> dict[tuple[str,str,str], ChemicalShift]:
    query=select(ChemicalShift).where(ChemicalShift.spectrum_id==spectrum_id)
    if nuclei: query=query.where(ChemicalShift.nucleus.in_(nuclei))
    return {(item.residue_id,item.nucleus,item.atom_name):item for item in db.scalars(query)}


def compare_spectra(db: Session, user: User, payload: SpectrumComparisonRequest) -> SpectrumComparisonRead:
    _spectra(db,user,payload.reference_spectrum_id,payload.comparison_spectrum_id)
    reference=_shift_map(db,payload.reference_spectrum_id,payload.nuclei); comparison=_shift_map(db,payload.comparison_spectrum_id,payload.nuclei)
    common=sorted(set(reference)&set(comparison)); deltas=[]
    for key in common:
        ref,comp=reference[key],comparison[key]; residue=db.get(Residue,key[0])
        deltas.append(ShiftDeltaRead(residue_id=key[0],sequence_number=residue.sequence_number,residue_name=residue.residue_name,atom_name=key[2],nucleus=key[1],reference_ppm=ref.value_ppm,comparison_ppm=comp.value_ppm,delta_ppm=comp.value_ppm-ref.value_ppm))
    return SpectrumComparisonRead(reference_spectrum_id=payload.reference_spectrum_id,comparison_spectrum_id=payload.comparison_spectrum_id,matched_shift_count=len(common),reference_only_count=len(set(reference)-set(comparison)),comparison_only_count=len(set(comparison)-set(reference)),deltas=deltas)


def calculate_csp(db: Session, user: User, payload: ChemicalShiftPerturbationRequest) -> ChemicalShiftPerturbationRead:
    if not payload.nucleus_weights or any(weight <= 0 for weight in payload.nucleus_weights.values()): raise HTTPException(422,"Nucleus weights must be positive")
    comparison=compare_spectra(db,user,SpectrumComparisonRequest(reference_spectrum_id=payload.reference_spectrum_id,comparison_spectrum_id=payload.comparison_spectrum_id,nuclei=payload.nuclei))
    grouped: dict[str,list[ShiftDeltaRead]]=defaultdict(list)
    for delta in comparison.deltas:
        if delta.nucleus in payload.nucleus_weights: grouped[delta.residue_id].append(delta)
    residues=[]
    for residue_id,components in grouped.items():
        first=components[0]; component_values={f"{item.nucleus}:{item.atom_name}":item.delta_ppm for item in components}
        value=sqrt(sum((payload.nucleus_weights[item.nucleus]*item.delta_ppm)**2 for item in components))
        residues.append(ResiduePerturbationRead(residue_id=residue_id,sequence_number=first.sequence_number,residue_name=first.residue_name,matched_atoms=sorted(component_values),component_deltas_ppm=component_values,perturbation_ppm=value))
    residues.sort(key=lambda item:(item.sequence_number,item.residue_id))
    return ChemicalShiftPerturbationRead(reference_spectrum_id=payload.reference_spectrum_id,comparison_spectrum_id=payload.comparison_spectrum_id,formula="sqrt(sum((nucleus_weight * delta_ppm)^2))",nucleus_weights=payload.nucleus_weights,residue_count=len(residues),residues=residues)
