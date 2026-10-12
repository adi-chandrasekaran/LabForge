from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user
from .models import Ligand, Protein, Residue, Sample, User
from .schemas import LigandCreate, LigandRead, ProteinCreate, ProteinRead, ResidueCreate, ResidueRead, SampleCreate, SampleRead
from .services import nmr_domain as service

router = APIRouter(prefix="/api/v1/nmr", tags=["nmr-domain"])


def _protein(db: Session, value: Protein) -> ProteinRead:
    return ProteinRead(**{column.name: getattr(value, column.name) for column in value.__table__.columns}, residue_count=service.residue_count(db, value.id))


def _ligand(value: Ligand) -> LigandRead:
    return LigandRead(**{column.name: getattr(value, column.name) for column in value.__table__.columns})


def _residue(value: Residue) -> ResidueRead:
    return ResidueRead(**{column.name: getattr(value, column.name) for column in value.__table__.columns})


def _sample(db: Session, value: Sample) -> SampleRead:
    protein_ids, ligand_ids = service.sample_component_ids(db, value.id)
    return SampleRead(**{column.name: getattr(value, column.name) for column in value.__table__.columns}, protein_ids=protein_ids, ligand_ids=ligand_ids)


@router.get("/samples", response_model=list[SampleRead])
def list_samples(project_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> list[SampleRead]:
    user = get_current_user(db); return [_sample(db, item) for item in service.list_samples(db, user, project_id)]


@router.post("/samples", response_model=SampleRead, status_code=201)
def create_sample(payload: SampleCreate, db: Session = Depends(get_db)) -> SampleRead:
    return _sample(db, service.create_sample(db, get_current_user(db), payload))


@router.get("/samples/{sample_id}", response_model=SampleRead)
def get_sample(sample_id: str, db: Session = Depends(get_db)) -> SampleRead:
    return _sample(db, service.get_sample(db, get_current_user(db), sample_id))


@router.put("/samples/{sample_id}", response_model=SampleRead)
def update_sample(sample_id: str, payload: SampleCreate, db: Session = Depends(get_db)) -> SampleRead:
    return _sample(db, service.update_sample(db, get_current_user(db), sample_id, payload))


@router.delete("/samples/{sample_id}", status_code=204, response_class=Response)
def delete_sample(sample_id: str, db: Session = Depends(get_db)) -> Response:
    service.delete_sample(db, get_current_user(db), sample_id); return Response(status_code=204)


@router.get("/proteins", response_model=list[ProteinRead])
def list_proteins(project_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> list[ProteinRead]:
    user = get_current_user(db); return [_protein(db, item) for item in service.list_proteins(db, user, project_id)]


@router.post("/proteins", response_model=ProteinRead, status_code=201)
def create_protein(payload: ProteinCreate, db: Session = Depends(get_db)) -> ProteinRead:
    return _protein(db, service.create_protein(db, get_current_user(db), payload))


@router.get("/proteins/{protein_id}", response_model=ProteinRead)
def get_protein(protein_id: str, db: Session = Depends(get_db)) -> ProteinRead:
    return _protein(db, service.get_protein(db, get_current_user(db), protein_id))


@router.put("/proteins/{protein_id}", response_model=ProteinRead)
def update_protein(protein_id: str, payload: ProteinCreate, db: Session = Depends(get_db)) -> ProteinRead:
    return _protein(db, service.update_protein(db, get_current_user(db), protein_id, payload))


@router.delete("/proteins/{protein_id}", status_code=204, response_class=Response)
def delete_protein(protein_id: str, db: Session = Depends(get_db)) -> Response:
    service.delete_protein(db, get_current_user(db), protein_id); return Response(status_code=204)


@router.get("/ligands", response_model=list[LigandRead])
def list_ligands(project_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)) -> list[LigandRead]:
    user = get_current_user(db); return [_ligand(item) for item in service.list_ligands(db, user, project_id)]


@router.post("/ligands", response_model=LigandRead, status_code=201)
def create_ligand(payload: LigandCreate, db: Session = Depends(get_db)) -> LigandRead:
    return _ligand(service.create_ligand(db, get_current_user(db), payload))


@router.get("/ligands/{ligand_id}", response_model=LigandRead)
def get_ligand(ligand_id: str, db: Session = Depends(get_db)) -> LigandRead:
    return _ligand(service.get_ligand(db, get_current_user(db), ligand_id))


@router.put("/ligands/{ligand_id}", response_model=LigandRead)
def update_ligand(ligand_id: str, payload: LigandCreate, db: Session = Depends(get_db)) -> LigandRead:
    return _ligand(service.update_ligand(db, get_current_user(db), ligand_id, payload))


@router.delete("/ligands/{ligand_id}", status_code=204, response_class=Response)
def delete_ligand(ligand_id: str, db: Session = Depends(get_db)) -> Response:
    service.delete_ligand(db, get_current_user(db), ligand_id); return Response(status_code=204)


@router.get("/residues", response_model=list[ResidueRead])
def list_residues(protein_id: str = Query(min_length=1), db: Session = Depends(get_db)) -> list[ResidueRead]:
    user = get_current_user(db); return [_residue(item) for item in service.list_residues(db, user, protein_id)]


@router.post("/residues", response_model=ResidueRead, status_code=201)
def create_residue(payload: ResidueCreate, db: Session = Depends(get_db)) -> ResidueRead:
    return _residue(service.create_residue(db, get_current_user(db), payload))


@router.get("/residues/{residue_id}", response_model=ResidueRead)
def get_residue(residue_id: str, db: Session = Depends(get_db)) -> ResidueRead:
    return _residue(service.get_residue(db, get_current_user(db), residue_id))


@router.put("/residues/{residue_id}", response_model=ResidueRead)
def update_residue(residue_id: str, payload: ResidueCreate, db: Session = Depends(get_db)) -> ResidueRead:
    return _residue(service.update_residue(db, get_current_user(db), residue_id, payload))


@router.delete("/residues/{residue_id}", status_code=204, response_class=Response)
def delete_residue(residue_id: str, db: Session = Depends(get_db)) -> Response:
    service.delete_residue(db, get_current_user(db), residue_id); return Response(status_code=204)
