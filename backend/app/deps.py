from sqlalchemy.orm import Session
from .auth import get_auth_provider
from .models import User


def get_or_create_mock_user(db: Session) -> User:
    return get_auth_provider().get_current_user(db)


def get_current_user(db: Session) -> User:
    return get_auth_provider().get_current_user(db)
