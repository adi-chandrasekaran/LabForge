from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import Assignment, ChemicalShift, Experiment, Peak, Residue, Sample, Spectrum, User
from ..schemas import AssignmentCreate, ChemicalShiftCreate, PeakCreate, SpectrumCreate
from ..sync import record_local_change
from . import nmr_domain


def _id(prefix: str) -> str: return f"{prefix}-{uuid4().hex[:12]}"


def get_spectrum(db: Session, user: User, spectrum_id: str) -> Spectrum:
    spectrum = db.get(Spectrum, spectrum_id)
    if spectrum is None or spectrum.lab_id != user.lab_id: raise HTTPException(404, "Spectrum not found")
    return spectrum


def _owner(spectrum: Spectrum, user: User) -> None:
    if spectrum.owner_id != user.id: raise HTTPException(403, "Only the spectrum owner can modify spectral data")


def _validate_spectrum_refs(db: Session, user: User, payload: SpectrumCreate) -> None:
    if payload.sample_id: nmr_domain.get_sample(db, user, payload.sample_id)
    if payload.experiment_id and db.get(Experiment, payload.experiment_id) is None: raise HTTPException(400, "Experiment does not exist")


def list_spectra(db: Session, user: User, sample_id: Optional[str] = None) -> list[Spectrum]:
    query = select(Spectrum).where(Spectrum.lab_id == user.lab_id).order_by(Spectrum.updated_at.desc())
    if sample_id: query = query.where(Spectrum.sample_id == sample_id)
    return list(db.scalars(query))


def create_spectrum(db: Session, user: User, payload: SpectrumCreate) -> Spectrum:
    _validate_spectrum_refs(db, user, payload)
    spectrum = Spectrum(id=_id("spectrum"), lab_id=user.lab_id, owner_id=user.id, **payload.model_dump())
    db.add(spectrum); record_local_change(db, "nmr.spectrum.create"); db.commit(); db.refresh(spectrum); return spectrum


def update_spectrum(db: Session, user: User, spectrum_id: str, payload: SpectrumCreate) -> Spectrum:
    spectrum = get_spectrum(db, user, spectrum_id); _owner(spectrum, user); _validate_spectrum_refs(db, user, payload)
    for key, value in payload.model_dump().items(): setattr(spectrum, key, value)
    record_local_change(db, "nmr.spectrum.update"); db.commit(); db.refresh(spectrum); return spectrum


def delete_spectrum(db: Session, user: User, spectrum_id: str) -> None:
    spectrum = get_spectrum(db, user, spectrum_id); _owner(spectrum, user)
    peak_ids = list(db.scalars(select(Peak.id).where(Peak.spectrum_id == spectrum.id)))
    db.execute(delete(ChemicalShift).where(ChemicalShift.spectrum_id == spectrum.id))
    if peak_ids: db.execute(delete(Assignment).where(Assignment.peak_id.in_(peak_ids)))
    db.delete(spectrum); record_local_change(db, "nmr.spectrum.delete"); db.commit()


def peak_count(db: Session, spectrum_id: str) -> int:
    return int(db.scalar(select(func.count()).select_from(Peak).where(Peak.spectrum_id == spectrum_id)) or 0)


def get_peak(db: Session, user: User, peak_id: str) -> Peak:
    peak = db.get(Peak, peak_id)
    if peak is None: raise HTTPException(404, "Peak not found")
    get_spectrum(db, user, peak.spectrum_id); return peak


def list_peaks(db: Session, user: User, spectrum_id: str) -> list[Peak]:
    get_spectrum(db, user, spectrum_id)
    return list(db.scalars(select(Peak).where(Peak.spectrum_id == spectrum_id).order_by(Peak.created_at)))


def validate_peak_create(db: Session, user: User, payload: PeakCreate) -> Spectrum:
    spectrum = get_spectrum(db, user, payload.spectrum_id); _owner(spectrum, user)
    if len(payload.positions_ppm) != len(spectrum.nuclei): raise HTTPException(422, "Peak position count must match spectrum dimensions")
    if payload.linewidths_hz and len(payload.linewidths_hz) != len(spectrum.nuclei): raise HTTPException(422, "Peak linewidth count must match spectrum dimensions")
    return spectrum


def create_peak(db: Session, user: User, payload: PeakCreate) -> Peak:
    validate_peak_create(db, user, payload); peak = Peak(id=_id("peak"), **payload.model_dump()); db.add(peak)
    record_local_change(db, "nmr.peak.create"); db.commit(); db.refresh(peak); return peak


def update_peak(db: Session, user: User, peak_id: str, payload: PeakCreate) -> Peak:
    peak = get_peak(db, user, peak_id); validate_peak_create(db, user, payload)
    for key, value in payload.model_dump().items(): setattr(peak, key, value)
    record_local_change(db, "nmr.peak.update"); db.commit(); db.refresh(peak); return peak


def delete_peak(db: Session, user: User, peak_id: str) -> None:
    peak = get_peak(db, user, peak_id); _owner(get_spectrum(db, user, peak.spectrum_id), user)
    db.execute(delete(ChemicalShift).where(ChemicalShift.peak_id == peak.id)); db.delete(peak)
    record_local_change(db, "nmr.peak.delete"); db.commit()


def assignment_count(db: Session, peak_id: str) -> int:
    return int(db.scalar(select(func.count()).select_from(Assignment).where(Assignment.peak_id == peak_id)) or 0)


def get_assignment(db: Session, user: User, assignment_id: str) -> Assignment:
    item = db.get(Assignment, assignment_id)
    if item is None: raise HTTPException(404, "Assignment not found")
    get_peak(db, user, item.peak_id); return item


def list_assignments(db: Session, user: User, peak_id: str) -> list[Assignment]:
    get_peak(db, user, peak_id); return list(db.scalars(select(Assignment).where(Assignment.peak_id == peak_id).order_by(Assignment.created_at)))


def validate_assignment_create(db: Session, user: User, payload: AssignmentCreate) -> None:
    peak = get_peak(db, user, payload.peak_id); _owner(get_spectrum(db, user, peak.spectrum_id), user); nmr_domain.get_residue(db, user, payload.residue_id)


def create_assignment(db: Session, user: User, payload: AssignmentCreate) -> Assignment:
    validate_assignment_create(db, user, payload); item = Assignment(id=_id("assignment"), **payload.model_dump()); db.add(item)
    record_local_change(db, "nmr.assignment.create"); db.commit(); db.refresh(item); return item


def update_assignment(db: Session, user: User, assignment_id: str, payload: AssignmentCreate) -> Assignment:
    item = get_assignment(db, user, assignment_id); validate_assignment_create(db, user, payload)
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    record_local_change(db, "nmr.assignment.update"); db.commit(); db.refresh(item); return item


def delete_assignment(db: Session, user: User, assignment_id: str) -> None:
    item = get_assignment(db, user, assignment_id); peak = get_peak(db, user, item.peak_id); _owner(get_spectrum(db, user, peak.spectrum_id), user); db.delete(item)
    record_local_change(db, "nmr.assignment.delete"); db.commit()


def get_shift(db: Session, user: User, shift_id: str) -> ChemicalShift:
    item = db.get(ChemicalShift, shift_id)
    if item is None: raise HTTPException(404, "Chemical shift not found")
    get_spectrum(db, user, item.spectrum_id); return item


def list_shifts(db: Session, user: User, spectrum_id: Optional[str] = None, residue_id: Optional[str] = None) -> list[ChemicalShift]:
    query = select(ChemicalShift).join(Spectrum).where(Spectrum.lab_id == user.lab_id)
    if spectrum_id: query = query.where(ChemicalShift.spectrum_id == spectrum_id)
    if residue_id: query = query.where(ChemicalShift.residue_id == residue_id)
    return list(db.scalars(query.order_by(ChemicalShift.residue_id, ChemicalShift.atom_name)))


def validate_shift_create(db: Session, user: User, payload: ChemicalShiftCreate, exclude_id: Optional[str] = None) -> None:
    spectrum = get_spectrum(db, user, payload.spectrum_id); _owner(spectrum, user); nmr_domain.get_residue(db, user, payload.residue_id)
    if payload.peak_id and get_peak(db, user, payload.peak_id).spectrum_id != spectrum.id: raise HTTPException(400, "Chemical-shift peak must belong to the same spectrum")
    duplicate = db.scalar(select(ChemicalShift).where(ChemicalShift.spectrum_id == payload.spectrum_id, ChemicalShift.residue_id == payload.residue_id, ChemicalShift.atom_name == payload.atom_name))
    if duplicate and duplicate.id != exclude_id: raise HTTPException(409, "Chemical shift already exists for this spectrum, residue, and atom")


def create_shift(db: Session, user: User, payload: ChemicalShiftCreate) -> ChemicalShift:
    validate_shift_create(db, user, payload); item = ChemicalShift(id=_id("shift"), **payload.model_dump()); db.add(item)
    record_local_change(db, "nmr.chemical_shift.create"); db.commit(); db.refresh(item); return item


def update_shift(db: Session, user: User, shift_id: str, payload: ChemicalShiftCreate) -> ChemicalShift:
    item = get_shift(db, user, shift_id); validate_shift_create(db, user, payload, item.id)
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    record_local_change(db, "nmr.chemical_shift.update"); db.commit(); db.refresh(item); return item


def delete_shift(db: Session, user: User, shift_id: str) -> None:
    item = get_shift(db, user, shift_id); _owner(get_spectrum(db, user, item.spectrum_id), user); db.delete(item)
    record_local_change(db, "nmr.chemical_shift.delete"); db.commit()
