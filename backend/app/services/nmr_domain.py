from __future__ import annotations

from typing import Optional, TypeVar
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import Ligand, Project, Protein, Residue, Sample, SampleLigand, SampleProtein, User
from ..schemas import LigandCreate, ProteinCreate, ResidueCreate, SampleCreate
from ..sync import record_local_change

Entity = TypeVar("Entity", Sample, Protein, Ligand)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _validate_project(db: Session, project_id: Optional[str]) -> None:
    if project_id and db.get(Project, project_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project does not exist")


def _owned(entity: Optional[Entity], user: User, label: str) -> Entity:
    if entity is None or entity.lab_id != user.lab_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} not found")
    return entity


def _assert_owner(entity: Entity, user: User) -> None:
    if entity.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the record owner can modify it")


def list_samples(db: Session, user: User, project_id: Optional[str] = None) -> list[Sample]:
    query = select(Sample).where(Sample.lab_id == user.lab_id).order_by(Sample.updated_at.desc())
    if project_id: query = query.where(Sample.project_id == project_id)
    return list(db.scalars(query))


def get_sample(db: Session, user: User, sample_id: str) -> Sample:
    return _owned(db.get(Sample, sample_id), user, "Sample")


def _validate_components(db: Session, user: User, protein_ids: list[str], ligand_ids: list[str]) -> None:
    for protein_id in dict.fromkeys(protein_ids): get_protein(db, user, protein_id)
    for ligand_id in dict.fromkeys(ligand_ids): get_ligand(db, user, ligand_id)


def _replace_components(db: Session, sample: Sample, protein_ids: list[str], ligand_ids: list[str]) -> None:
    db.execute(delete(SampleProtein).where(SampleProtein.sample_id == sample.id))
    db.execute(delete(SampleLigand).where(SampleLigand.sample_id == sample.id))
    for protein_id in dict.fromkeys(protein_ids): db.add(SampleProtein(id=_id("sample-protein"), sample_id=sample.id, protein_id=protein_id))
    for ligand_id in dict.fromkeys(ligand_ids): db.add(SampleLigand(id=_id("sample-ligand"), sample_id=sample.id, ligand_id=ligand_id))


def create_sample(db: Session, user: User, payload: SampleCreate) -> Sample:
    _validate_project(db, payload.project_id); _validate_components(db, user, payload.protein_ids, payload.ligand_ids)
    values = payload.model_dump(exclude={"protein_ids", "ligand_ids"})
    sample = Sample(id=_id("sample"), lab_id=user.lab_id, owner_id=user.id, **values)
    db.add(sample); db.flush(); _replace_components(db, sample, payload.protein_ids, payload.ligand_ids)
    record_local_change(db, "nmr.sample.create"); db.commit(); db.refresh(sample); return sample


def update_sample(db: Session, user: User, sample_id: str, payload: SampleCreate) -> Sample:
    sample = get_sample(db, user, sample_id); _assert_owner(sample, user); _validate_project(db, payload.project_id); _validate_components(db, user, payload.protein_ids, payload.ligand_ids)
    for key, value in payload.model_dump(exclude={"protein_ids", "ligand_ids"}).items(): setattr(sample, key, value)
    _replace_components(db, sample, payload.protein_ids, payload.ligand_ids)
    record_local_change(db, "nmr.sample.update"); db.commit(); db.refresh(sample); return sample


def delete_sample(db: Session, user: User, sample_id: str) -> None:
    sample = get_sample(db, user, sample_id); _assert_owner(sample, user); db.delete(sample)
    record_local_change(db, "nmr.sample.delete"); db.commit()


def sample_component_ids(db: Session, sample_id: str) -> tuple[list[str], list[str]]:
    return (list(db.scalars(select(SampleProtein.protein_id).where(SampleProtein.sample_id == sample_id))), list(db.scalars(select(SampleLigand.ligand_id).where(SampleLigand.sample_id == sample_id))))


def list_proteins(db: Session, user: User, project_id: Optional[str] = None) -> list[Protein]:
    query = select(Protein).where(Protein.lab_id == user.lab_id).order_by(Protein.name)
    if project_id: query = query.where(Protein.project_id == project_id)
    return list(db.scalars(query))


def get_protein(db: Session, user: User, protein_id: str) -> Protein:
    return _owned(db.get(Protein, protein_id), user, "Protein")


def create_protein(db: Session, user: User, payload: ProteinCreate) -> Protein:
    _validate_project(db, payload.project_id); protein = Protein(id=_id("protein"), lab_id=user.lab_id, owner_id=user.id, **payload.model_dump())
    db.add(protein); record_local_change(db, "nmr.protein.create"); db.commit(); db.refresh(protein); return protein


def update_protein(db: Session, user: User, protein_id: str, payload: ProteinCreate) -> Protein:
    protein = get_protein(db, user, protein_id); _assert_owner(protein, user); _validate_project(db, payload.project_id)
    for key, value in payload.model_dump().items(): setattr(protein, key, value)
    record_local_change(db, "nmr.protein.update"); db.commit(); db.refresh(protein); return protein


def delete_protein(db: Session, user: User, protein_id: str) -> None:
    protein = get_protein(db, user, protein_id); _assert_owner(protein, user)
    db.execute(delete(SampleProtein).where(SampleProtein.protein_id == protein.id)); db.delete(protein)
    record_local_change(db, "nmr.protein.delete"); db.commit()


def residue_count(db: Session, protein_id: str) -> int:
    return int(db.scalar(select(func.count()).select_from(Residue).where(Residue.protein_id == protein_id)) or 0)


def list_ligands(db: Session, user: User, project_id: Optional[str] = None) -> list[Ligand]:
    query = select(Ligand).where(Ligand.lab_id == user.lab_id).order_by(Ligand.name)
    if project_id: query = query.where(Ligand.project_id == project_id)
    return list(db.scalars(query))


def get_ligand(db: Session, user: User, ligand_id: str) -> Ligand:
    return _owned(db.get(Ligand, ligand_id), user, "Ligand")


def create_ligand(db: Session, user: User, payload: LigandCreate) -> Ligand:
    _validate_project(db, payload.project_id); ligand = Ligand(id=_id("ligand"), lab_id=user.lab_id, owner_id=user.id, **payload.model_dump())
    db.add(ligand); record_local_change(db, "nmr.ligand.create"); db.commit(); db.refresh(ligand); return ligand


def update_ligand(db: Session, user: User, ligand_id: str, payload: LigandCreate) -> Ligand:
    ligand = get_ligand(db, user, ligand_id); _assert_owner(ligand, user); _validate_project(db, payload.project_id)
    for key, value in payload.model_dump().items(): setattr(ligand, key, value)
    record_local_change(db, "nmr.ligand.update"); db.commit(); db.refresh(ligand); return ligand


def delete_ligand(db: Session, user: User, ligand_id: str) -> None:
    ligand = get_ligand(db, user, ligand_id); _assert_owner(ligand, user)
    db.execute(delete(SampleLigand).where(SampleLigand.ligand_id == ligand.id)); db.delete(ligand)
    record_local_change(db, "nmr.ligand.delete"); db.commit()


def list_residues(db: Session, user: User, protein_id: str) -> list[Residue]:
    get_protein(db, user, protein_id)
    return list(db.scalars(select(Residue).where(Residue.protein_id == protein_id).order_by(Residue.sequence_number, Residue.insertion_code)))


def get_residue(db: Session, user: User, residue_id: str) -> Residue:
    residue = db.get(Residue, residue_id)
    if residue is None: raise HTTPException(status.HTTP_404_NOT_FOUND, "Residue not found")
    get_protein(db, user, residue.protein_id); return residue


def _assert_unique_residue(db: Session, payload: ResidueCreate, exclude_id: Optional[str] = None) -> None:
    existing = db.scalar(select(Residue).where(Residue.protein_id == payload.protein_id, Residue.sequence_number == payload.sequence_number, Residue.insertion_code == payload.insertion_code))
    if existing and existing.id != exclude_id: raise HTTPException(status.HTTP_409_CONFLICT, "Residue position already exists for this protein")


def create_residue(db: Session, user: User, payload: ResidueCreate) -> Residue:
    protein = get_protein(db, user, payload.protein_id); _assert_owner(protein, user); _assert_unique_residue(db, payload)
    residue = Residue(id=_id("residue"), **payload.model_dump()); db.add(residue)
    record_local_change(db, "nmr.residue.create"); db.commit(); db.refresh(residue); return residue


def update_residue(db: Session, user: User, residue_id: str, payload: ResidueCreate) -> Residue:
    residue = get_residue(db, user, residue_id); old_protein = get_protein(db, user, residue.protein_id); new_protein = get_protein(db, user, payload.protein_id); _assert_owner(old_protein, user); _assert_owner(new_protein, user); _assert_unique_residue(db, payload, residue.id)
    for key, value in payload.model_dump().items(): setattr(residue, key, value)
    record_local_change(db, "nmr.residue.update"); db.commit(); db.refresh(residue); return residue


def delete_residue(db: Session, user: User, residue_id: str) -> None:
    residue = get_residue(db, user, residue_id); protein = get_protein(db, user, residue.protein_id); _assert_owner(protein, user); db.delete(residue)
    record_local_change(db, "nmr.residue.delete"); db.commit()
