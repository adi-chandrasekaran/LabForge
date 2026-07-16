from __future__ import annotations

from typing import Protocol
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .config import get_settings
from .models import User


class AuthProvider(Protocol):
    backend_name: str

    def get_current_user(self, db: Session) -> User:
        ...


class MockAuthProvider:
    backend_name = "mock"

    def get_current_user(self, db: Session) -> User:
        settings = get_settings()
        user = db.get(User, settings.mock_user_id)
        if user:
            return user

        user = User(
            id=settings.mock_user_id,
            email="chen@nmr-lab.local",
            display_name="Chen, Y.",
            role=settings.mock_user_role,
            lab_id="local-lab",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class SupabaseAuthProvider:
    backend_name = "supabase"

    def get_current_user(self, db: Session) -> User:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Supabase auth is not implemented yet. Use local mock auth for now.",
        )


def get_auth_provider() -> AuthProvider:
    settings = get_settings()
    if settings.auth_backend == "supabase":
        return SupabaseAuthProvider()
    return MockAuthProvider()
