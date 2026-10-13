from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import (
    AssignmentCreate,
    ChemicalShiftCreate,
    NMRImportError,
    NMRImportFormat,
    NMRImportResult,
    PeakCreate,
    ResidueCreate,
)
from . import nmr_domain, nmr_spectral


MAX_IMPORT_BYTES = 1_000_000
SUPPORTED_ENTITY_TYPES = {"residues", "peaks", "assignments", "chemical_shifts"}

IMPORT_FORMATS = [
    NMRImportFormat(entity_type="residues", required_columns=["protein_id", "sequence_number", "residue_name", "one_letter_code"], optional_columns=["insertion_code", "notes"]),
    NMRImportFormat(entity_type="peaks", required_columns=["spectrum_id", "position_1_ppm"], optional_columns=["label", "position_2_ppm", "position_3_ppm", "position_4_ppm", "intensity", "volume", "linewidth_1_hz", "linewidth_2_hz", "linewidth_3_hz", "linewidth_4_hz"]),
    NMRImportFormat(entity_type="assignments", required_columns=["peak_id", "residue_id", "atom_names"], optional_columns=["confidence", "status", "notes"], list_separator=";"),
    NMRImportFormat(entity_type="chemical_shifts", required_columns=["spectrum_id", "residue_id", "atom_name", "nucleus", "value_ppm"], optional_columns=["peak_id", "uncertainty_ppm"]),
]


@dataclass(frozen=True)
class ImportDefinition:
    model: type[BaseModel]
    transform: Callable[[dict[str, str]], dict]
    validate: Callable
    create: Callable


def _optional_float(value: str | None) -> float | None:
    return None if value is None or not value.strip() else float(value)


def _list_values(row: dict[str, str], prefix: str, suffix: str) -> list[float]:
    result: list[float] = []
    for index in range(1, 5):
        value = row.get(f"{prefix}_{index}_{suffix}", "").strip()
        if value:
            result.append(float(value))
    return result


def _residue(row: dict[str, str]) -> dict:
    return {
        "protein_id": row.get("protein_id", ""),
        "sequence_number": row.get("sequence_number", ""),
        "insertion_code": row.get("insertion_code", ""),
        "residue_name": row.get("residue_name", ""),
        "one_letter_code": row.get("one_letter_code", ""),
        "notes": row.get("notes", ""),
    }


def _peak(row: dict[str, str]) -> dict:
    return {
        "spectrum_id": row.get("spectrum_id", ""),
        "label": row.get("label", ""),
        "positions_ppm": _list_values(row, "position", "ppm"),
        "intensity": _optional_float(row.get("intensity")),
        "volume": _optional_float(row.get("volume")),
        "linewidths_hz": _list_values(row, "linewidth", "hz"),
    }


def _assignment(row: dict[str, str]) -> dict:
    return {
        "peak_id": row.get("peak_id", ""),
        "residue_id": row.get("residue_id", ""),
        "atom_names": [value.strip() for value in row.get("atom_names", "").split(";") if value.strip()],
        "confidence": _optional_float(row.get("confidence")),
        "status": row.get("status", "tentative") or "tentative",
        "notes": row.get("notes", ""),
    }


def _chemical_shift(row: dict[str, str]) -> dict:
    return {
        "spectrum_id": row.get("spectrum_id", ""),
        "residue_id": row.get("residue_id", ""),
        "peak_id": row.get("peak_id", "").strip() or None,
        "atom_name": row.get("atom_name", ""),
        "nucleus": row.get("nucleus", ""),
        "value_ppm": row.get("value_ppm", ""),
        "uncertainty_ppm": _optional_float(row.get("uncertainty_ppm")),
    }


def _validate_residue(db: Session, user: User, payload: ResidueCreate) -> None:
    nmr_domain.validate_residue_create(db, user, payload)


def _validate_peak(db: Session, user: User, payload: PeakCreate) -> None:
    nmr_spectral.validate_peak_create(db, user, payload)


def _validate_assignment(db: Session, user: User, payload: AssignmentCreate) -> None:
    nmr_spectral.validate_assignment_create(db, user, payload)


def _validate_shift(db: Session, user: User, payload: ChemicalShiftCreate) -> None:
    nmr_spectral.validate_shift_create(db, user, payload)


DEFINITIONS = {
    "residues": ImportDefinition(ResidueCreate, _residue, _validate_residue, nmr_domain.create_residue),
    "peaks": ImportDefinition(PeakCreate, _peak, _validate_peak, nmr_spectral.create_peak),
    "assignments": ImportDefinition(AssignmentCreate, _assignment, _validate_assignment, nmr_spectral.create_assignment),
    "chemical_shifts": ImportDefinition(ChemicalShiftCreate, _chemical_shift, _validate_shift, nmr_spectral.create_shift),
}


def _decode(content: bytes) -> str:
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "CSV import exceeds the 1 MB limit")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(422, "CSV import must use UTF-8 encoding") from exc


def _validation_error(row_number: int, exc: Exception) -> NMRImportError:
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first["loc"])
        return NMRImportError(row=row_number, field=field, message=first["msg"])
    if isinstance(exc, ValueError):
        return NMRImportError(row=row_number, message=str(exc))
    if isinstance(exc, HTTPException):
        return NMRImportError(row=row_number, message=str(exc.detail))
    raise exc


def import_csv(
    db: Session,
    user: User,
    entity_type: str,
    content: bytes,
    *,
    dry_run: bool,
) -> NMRImportResult:
    definition = DEFINITIONS.get(entity_type)
    if definition is None:
        raise HTTPException(404, f"Unsupported NMR import type: {entity_type}")

    try:
        reader = csv.DictReader(io.StringIO(_decode(content), newline=""))
        if not reader.fieldnames:
            raise HTTPException(422, "CSV import requires a header row")
        import_format = next(value for value in IMPORT_FORMATS if value.entity_type == entity_type)
        missing_columns = [column for column in import_format.required_columns if column not in reader.fieldnames]
        if missing_columns:
            raise HTTPException(422, f"CSV import is missing required columns: {', '.join(missing_columns)}")
        rows = list(reader)
    except csv.Error as exc:
        raise HTTPException(422, f"Invalid CSV: {exc}") from exc

    if not rows:
        raise HTTPException(422, "CSV import requires at least one data row")

    parsed: list[BaseModel] = []
    errors: list[NMRImportError] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            parsed.append(definition.model.model_validate(definition.transform(row)))
        except (ValidationError, ValueError) as exc:
            errors.append(_validation_error(row_number, exc))

    if not errors:
        seen: set[tuple] = set()
        for offset, payload in enumerate(parsed, start=2):
            try:
                definition.validate(db, user, payload)
                if entity_type == "residues":
                    key = (payload.protein_id, payload.sequence_number, payload.insertion_code)
                elif entity_type == "chemical_shifts":
                    key = (payload.spectrum_id, payload.residue_id, payload.atom_name)
                else:
                    key = ()
                if key and key in seen:
                    raise ValueError("Duplicate row in this import")
                seen.add(key)
            except (HTTPException, ValueError) as exc:
                errors.append(_validation_error(offset, exc))

    if errors or dry_run:
        return NMRImportResult(
            entity_type=entity_type,
            dry_run=dry_run,
            total_rows=len(rows),
            valid_rows=len(rows) - len(errors),
            imported_count=0,
            errors=errors,
        )

    imported_ids: list[str] = []
    for payload in parsed:
        imported_ids.append(definition.create(db, user, payload).id)
    return NMRImportResult(
        entity_type=entity_type,
        dry_run=False,
        total_rows=len(rows),
        valid_rows=len(parsed),
        imported_count=len(imported_ids),
        imported_ids=imported_ids,
    )
