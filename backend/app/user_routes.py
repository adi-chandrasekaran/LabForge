from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .deps import get_current_user
from .models import User
from .schemas import LabMemberRead


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/lab-members", response_model=list[LabMemberRead])
def list_lab_members(db: Session = Depends(get_db)) -> list[LabMemberRead]:
    current_user = get_current_user(db)
    members = db.scalars(
        select(User)
        .where(User.lab_id == current_user.lab_id)
        .order_by(User.display_name, User.created_at)
    ).all()
    return [
        LabMemberRead(
            id=member.id,
            email=member.email,
            display_name=member.display_name,
            role=member.role,
            lab_id=member.lab_id,
            created_at=member.created_at,
        )
        for member in members
    ]
