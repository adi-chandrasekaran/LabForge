from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user
from .schemas import NMRImportFormat, NMRImportResult
from .services import nmr_import


router = APIRouter(prefix="/api/v1/nmr/imports", tags=["nmr-imports"])


@router.get("", response_model=list[NMRImportFormat])
def list_import_formats() -> list[NMRImportFormat]:
    return nmr_import.IMPORT_FORMATS


@router.post("/{entity_type}", response_model=NMRImportResult)
async def import_nmr_csv(
    entity_type: str,
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> NMRImportResult:
    return nmr_import.import_csv(
        db,
        get_current_user(db),
        entity_type,
        await file.read(nmr_import.MAX_IMPORT_BYTES + 1),
        dry_run=dry_run,
    )
