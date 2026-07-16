from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .schemas import SyncStatusRead
from .sync import record_sync_attempt, serialize_sync_status


router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatusRead)
def read_sync_status(db: Session = Depends(get_db)) -> SyncStatusRead:
    return serialize_sync_status(db)


@router.post("/push", response_model=SyncStatusRead)
def push_sync_status(db: Session = Depends(get_db)) -> SyncStatusRead:
    record_sync_attempt(
        db,
        success=False,
        message="Hosted sync is not implemented yet. Local changes remain stored in SQLite.",
    )
    db.commit()
    return serialize_sync_status(db)
