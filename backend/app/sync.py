from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .config import get_settings
from .models import SyncState
from .schemas import SyncStatusRead


SYNC_STATE_ID = "local-sync"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_sync_state(db: Session) -> SyncState:
    sync_state = db.get(SyncState, SYNC_STATE_ID)
    if sync_state is not None:
        return sync_state

    sync_state = SyncState(id=SYNC_STATE_ID)
    db.add(sync_state)
    db.flush()
    return sync_state


def record_local_change(db: Session, operation: str) -> SyncState:
    sync_state = ensure_sync_state(db)
    sync_state.pending_changes += 1
    sync_state.last_local_write_at = utcnow()
    sync_state.last_operation = operation
    sync_state.last_error = None
    return sync_state


def record_sync_attempt(db: Session, *, success: bool, message: str) -> SyncState:
    sync_state = ensure_sync_state(db)
    sync_state.last_sync_attempt_at = utcnow()
    sync_state.last_error = None if success else message
    if success:
        sync_state.last_sync_success_at = sync_state.last_sync_attempt_at
        sync_state.pending_changes = 0
    return sync_state


def serialize_sync_status(db: Session) -> SyncStatusRead:
    settings = get_settings()
    sync_state = ensure_sync_state(db)
    hosted_sync_ready = (
        settings.app_mode == "hosted"
        and settings.database_backend == "postgres"
        and settings.auth_backend == "supabase"
        and settings.storage_backend == "tigris"
    )
    if sync_state.pending_changes > 0:
        local_status = "saved_locally"
        message = "Changes are saved locally and waiting for hosted sync."
    else:
        local_status = "idle"
        message = "No pending local changes."

    if settings.app_mode == "local":
        message = f"{message} Hosted sync is not configured in local mode."
    elif not hosted_sync_ready:
        message = f"{message} Hosted sync configuration is incomplete."

    return SyncStatusRead(
        app_mode=settings.app_mode,
        database_backend=settings.database_backend,
        auth_backend=settings.auth_backend,
        storage_backend=settings.storage_backend,
        local_status=local_status,
        pending_changes=sync_state.pending_changes,
        last_local_write_at=sync_state.last_local_write_at,
        last_sync_attempt_at=sync_state.last_sync_attempt_at,
        last_sync_success_at=sync_state.last_sync_success_at,
        last_error=sync_state.last_error,
        last_operation=sync_state.last_operation,
        hosted_sync_ready=hosted_sync_ready,
        message=message,
    )
