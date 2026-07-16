from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO, Protocol
from .attachments import attachment_storage_path
from .config import get_settings
from .models import Attachment


@dataclass
class StoredAttachmentRef:
    storage_backend: str
    local_path: str | None = None
    remote_url: str | None = None


class StorageBackend(Protocol):
    backend_name: str

    def save_attachment(
        self,
        owner_type: str,
        owner_id: str,
        attachment_id: str,
        filename: str | None,
        content_type: str,
        fileobj: BinaryIO,
    ) -> StoredAttachmentRef:
        ...

    def delete_attachment(self, attachment: Attachment) -> None:
        ...

    def resolve_local_path(self, attachment: Attachment) -> Path | None:
        ...


class LocalStorageBackend:
    backend_name = "local"

    def save_attachment(
        self,
        owner_type: str,
        owner_id: str,
        attachment_id: str,
        filename: str | None,
        content_type: str,
        fileobj: BinaryIO,
    ) -> StoredAttachmentRef:
        storage_path = attachment_storage_path(owner_type, owner_id, attachment_id, filename, content_type)
        with storage_path.open("wb") as output_file:
            copyfileobj(fileobj, output_file)
        return StoredAttachmentRef(
            storage_backend=self.backend_name,
            local_path=str(storage_path),
        )

    def delete_attachment(self, attachment: Attachment) -> None:
        if not attachment.local_path:
            return
        path = Path(attachment.local_path)
        if path.exists():
            path.unlink()

    def resolve_local_path(self, attachment: Attachment) -> Path | None:
        if not attachment.local_path:
            return None
        return Path(attachment.local_path)


class TigrisStorageBackend:
    backend_name = "tigris"

    def save_attachment(
        self,
        owner_type: str,
        owner_id: str,
        attachment_id: str,
        filename: str | None,
        content_type: str,
        fileobj: BinaryIO,
    ) -> StoredAttachmentRef:
        raise NotImplementedError("Tigris storage is not implemented yet")

    def delete_attachment(self, attachment: Attachment) -> None:
        raise NotImplementedError("Tigris storage is not implemented yet")

    def resolve_local_path(self, attachment: Attachment) -> Path | None:
        return None


def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "tigris":
        return TigrisStorageBackend()
    return LocalStorageBackend()
