from __future__ import annotations

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .attachments import assert_allowed_image_type, new_attachment_id, serialize_attachment
from .database import get_db
from .deps import get_current_user
from .models import Attachment, ChatChannel, ChatMessage, Experiment, User, Workflow
from .schemas import (
    AttachmentRead,
    ChatChannelCreate,
    ChatChannelRead,
    ChatChannelUpdate,
    ChatMessageCreate,
    ChatMessageRead,
    ChatMessageUpdate,
)
from .storage import get_storage_backend
from .sync import record_local_change


router = APIRouter(prefix="/api/v1/channels", tags=["chat"])


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def _serialize_channel(db: Session, channel: ChatChannel) -> ChatChannelRead:
    message_count = db.scalar(
        select(func.count(ChatMessage.id)).where(ChatMessage.channel_id == channel.id)
    ) or 0
    latest_message = db.scalar(
        select(ChatMessage)
        .where(ChatMessage.channel_id == channel.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    return ChatChannelRead(
        id=channel.id,
        lab_id=channel.lab_id,
        name=channel.name,
        topic=channel.topic,
        created_by_id=channel.created_by_id,
        message_count=message_count,
        last_message_preview=(latest_message.body[:120] if latest_message else None),
        last_message_at=(latest_message.created_at if latest_message else None),
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


def _serialize_message(db: Session, message: ChatMessage) -> ChatMessageRead:
    author = db.get(User, message.author_id) if message.author_id else None
    workflow = db.get(Workflow, message.referenced_workflow_id) if message.referenced_workflow_id else None
    experiment = db.get(Experiment, message.referenced_experiment_id) if message.referenced_experiment_id else None
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.owner_type == "chat_message", Attachment.owner_id == message.id)
        .order_by(Attachment.created_at)
    ).all()
    return ChatMessageRead(
        id=message.id,
        channel_id=message.channel_id,
        lab_id=message.lab_id,
        author_id=message.author_id,
        author_display_name=author.display_name if author else None,
        body=message.body,
        referenced_workflow_id=message.referenced_workflow_id,
        referenced_workflow_title=workflow.title if workflow else None,
        referenced_experiment_id=message.referenced_experiment_id,
        referenced_experiment_title=experiment.title if experiment else None,
        attachments=[serialize_attachment(attachment) for attachment in attachments],
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


def _get_channel_for_user(db: Session, current_user: User, channel_id: str) -> ChatChannel:
    channel = db.get(ChatChannel, channel_id)
    if channel is None or channel.lab_id != current_user.lab_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


def _get_message_for_user(db: Session, current_user: User, channel_id: str, message_id: str) -> ChatMessage:
    message = db.get(ChatMessage, message_id)
    if message is None or message.channel_id != channel_id or message.lab_id != current_user.lab_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


def _validate_references(db: Session, referenced_workflow_id: Optional[str], referenced_experiment_id: Optional[str]) -> None:
    if referenced_workflow_id and db.get(Workflow, referenced_workflow_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced workflow does not exist")
    if referenced_experiment_id and db.get(Experiment, referenced_experiment_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced experiment does not exist")


def _store_message_attachment(db: Session, message_id: str, upload: UploadFile) -> AttachmentRead:
    content_type = assert_allowed_image_type(upload.content_type)
    attachment_id = new_attachment_id()
    stored_ref = get_storage_backend().save_attachment(
        owner_type="chat_message",
        owner_id=message_id,
        attachment_id=attachment_id,
        filename=upload.filename,
        content_type=content_type,
        fileobj=upload.file,
    )
    attachment = Attachment(
        id=attachment_id,
        owner_type="chat_message",
        owner_id=message_id,
        filename=upload.filename or attachment_id,
        content_type=content_type,
        storage_backend=stored_ref.storage_backend,
        local_path=stored_ref.local_path,
        remote_url=stored_ref.remote_url,
    )
    db.add(attachment)
    record_local_change(db, "chat.message_attachment.upload")
    db.commit()
    db.refresh(attachment)
    return serialize_attachment(attachment)


@router.get("", response_model=list[ChatChannelRead])
def list_channels(db: Session = Depends(get_db)) -> list[ChatChannelRead]:
    current_user = get_current_user(db)
    channels = db.scalars(
        select(ChatChannel)
        .where(ChatChannel.lab_id == current_user.lab_id)
        .order_by(ChatChannel.name, ChatChannel.created_at)
    ).all()
    return [_serialize_channel(db, channel) for channel in channels]


@router.post("", response_model=ChatChannelRead, status_code=status.HTTP_201_CREATED)
def create_channel(payload: ChatChannelCreate, db: Session = Depends(get_db)) -> ChatChannelRead:
    current_user = get_current_user(db)
    existing = db.scalar(
        select(ChatChannel).where(
            ChatChannel.lab_id == current_user.lab_id,
            func.lower(ChatChannel.name) == payload.name.lower(),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel name already exists in this lab")
    channel = ChatChannel(
        id=_new_id("channel"),
        lab_id=current_user.lab_id,
        name=payload.name,
        topic=payload.topic,
        created_by_id=current_user.id,
    )
    db.add(channel)
    record_local_change(db, "chat.channel.create")
    db.commit()
    db.refresh(channel)
    return _serialize_channel(db, channel)


@router.get("/{channel_id}", response_model=ChatChannelRead)
def read_channel(channel_id: str, db: Session = Depends(get_db)) -> ChatChannelRead:
    current_user = get_current_user(db)
    channel = _get_channel_for_user(db, current_user, channel_id)
    return _serialize_channel(db, channel)


@router.patch("/{channel_id}", response_model=ChatChannelRead)
def update_channel(channel_id: str, payload: ChatChannelUpdate, db: Session = Depends(get_db)) -> ChatChannelRead:
    current_user = get_current_user(db)
    channel = _get_channel_for_user(db, current_user, channel_id)
    if payload.name is not None and payload.name.lower() != channel.name.lower():
        existing = db.scalar(
            select(ChatChannel).where(
                ChatChannel.lab_id == current_user.lab_id,
                func.lower(ChatChannel.name) == payload.name.lower(),
                ChatChannel.id != channel.id,
            )
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel name already exists in this lab")
        channel.name = payload.name
    if payload.topic is not None:
        channel.topic = payload.topic
    record_local_change(db, "chat.channel.update")
    db.commit()
    db.refresh(channel)
    return _serialize_channel(db, channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: str, db: Session = Depends(get_db)) -> Response:
    current_user = get_current_user(db)
    channel = _get_channel_for_user(db, current_user, channel_id)
    db.delete(channel)
    record_local_change(db, "chat.channel.delete")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{channel_id}/messages", response_model=list[ChatMessageRead])
def list_messages(channel_id: str, limit: int = Query(default=200, ge=1, le=500), db: Session = Depends(get_db)) -> list[ChatMessageRead]:
    current_user = get_current_user(db)
    _get_channel_for_user(db, current_user, channel_id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.channel_id == channel_id, ChatMessage.lab_id == current_user.lab_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    ).all()
    return [_serialize_message(db, message) for message in messages]


@router.post("/{channel_id}/messages", response_model=ChatMessageRead, status_code=status.HTTP_201_CREATED)
def create_message(channel_id: str, payload: ChatMessageCreate, db: Session = Depends(get_db)) -> ChatMessageRead:
    current_user = get_current_user(db)
    channel = _get_channel_for_user(db, current_user, channel_id)
    _validate_references(db, payload.referenced_workflow_id, payload.referenced_experiment_id)
    message = ChatMessage(
        id=_new_id("message"),
        channel_id=channel.id,
        lab_id=current_user.lab_id,
        author_id=current_user.id,
        body=payload.body,
        referenced_workflow_id=payload.referenced_workflow_id,
        referenced_experiment_id=payload.referenced_experiment_id,
    )
    db.add(message)
    record_local_change(db, "chat.message.create")
    db.commit()
    db.refresh(message)
    return _serialize_message(db, message)


@router.patch("/{channel_id}/messages/{message_id}", response_model=ChatMessageRead)
def update_message(channel_id: str, message_id: str, payload: ChatMessageUpdate, db: Session = Depends(get_db)) -> ChatMessageRead:
    current_user = get_current_user(db)
    _get_channel_for_user(db, current_user, channel_id)
    message = _get_message_for_user(db, current_user, channel_id, message_id)
    if message.author_id != current_user.id and current_user.role != "professor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user cannot edit this message")
    _validate_references(db, payload.referenced_workflow_id, payload.referenced_experiment_id)
    message.body = payload.body
    message.referenced_workflow_id = payload.referenced_workflow_id
    message.referenced_experiment_id = payload.referenced_experiment_id
    record_local_change(db, "chat.message.update")
    db.commit()
    db.refresh(message)
    return _serialize_message(db, message)


@router.delete("/{channel_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(channel_id: str, message_id: str, db: Session = Depends(get_db)) -> Response:
    current_user = get_current_user(db)
    _get_channel_for_user(db, current_user, channel_id)
    message = _get_message_for_user(db, current_user, channel_id, message_id)
    if message.author_id != current_user.id and current_user.role != "professor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user cannot delete this message")
    db.delete(message)
    record_local_change(db, "chat.message.delete")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{channel_id}/messages/{message_id}/attachments", response_model=list[AttachmentRead])
def list_message_attachments(channel_id: str, message_id: str, db: Session = Depends(get_db)) -> list[AttachmentRead]:
    current_user = get_current_user(db)
    _get_channel_for_user(db, current_user, channel_id)
    _get_message_for_user(db, current_user, channel_id, message_id)
    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.owner_type == "chat_message", Attachment.owner_id == message_id)
        .order_by(Attachment.created_at)
    ).all()
    return [serialize_attachment(attachment) for attachment in attachments]


@router.post("/{channel_id}/messages/{message_id}/attachments", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
def upload_message_attachment(
    channel_id: str,
    message_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AttachmentRead:
    current_user = get_current_user(db)
    _get_channel_for_user(db, current_user, channel_id)
    _get_message_for_user(db, current_user, channel_id, message_id)
    return _store_message_attachment(db, message_id, file)
