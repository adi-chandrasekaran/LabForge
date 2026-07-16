from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, status
from .config import get_settings
from .models import Attachment
from .schemas import AttachmentRead


ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}


def new_attachment_id() -> str:
    return f"attachment-{uuid4().hex[:10]}"


def assert_allowed_image_type(content_type: str | None) -> str:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are supported for step attachments",
        )
    return content_type


def stored_extension(filename: str | None, content_type: str) -> str:
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix:
            return suffix
    return ALLOWED_IMAGE_TYPES[content_type]


def attachment_storage_path(owner_type: str, owner_id: str, attachment_id: str, filename: str | None, content_type: str) -> Path:
    settings = get_settings()
    suffix = stored_extension(filename, content_type)
    owner_dir = settings.uploads_dir / owner_type / owner_id
    owner_dir.mkdir(parents=True, exist_ok=True)
    return owner_dir / f"{attachment_id}{suffix}"


def attachment_download_url(attachment_id: str) -> str:
    settings = get_settings()
    return f"{settings.api_prefix}/attachments/{attachment_id}/content"


def serialize_attachment(attachment: Attachment) -> AttachmentRead:
    return AttachmentRead(
        id=attachment.id,
        owner_type=attachment.owner_type,
        owner_id=attachment.owner_id,
        filename=attachment.filename,
        content_type=attachment.content_type,
        storage_backend=attachment.storage_backend,
        local_path=attachment.local_path,
        remote_url=attachment.remote_url,
        download_url=attachment.remote_url or attachment_download_url(attachment.id),
        created_at=attachment.created_at,
    )
