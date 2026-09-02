from collections.abc import Generator
from typing import Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)

engine = None
SessionLocal = None


def configure_database(database_url: Optional[str] = None) -> None:
    global engine, SessionLocal

    url = database_url or settings.database_url
    if engine is not None:
        engine.dispose()
    engine = create_engine(url, connect_args=_connect_args(url))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _apply_schema_updates() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "workflow_steps" in tables:
        columns = {column["name"] for column in inspector.get_columns("workflow_steps")}
        if "workflow_branch_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE workflow_steps ADD COLUMN workflow_branch_id VARCHAR"))

    if "workflows" in tables:
        columns = {column["name"] for column in inspector.get_columns("workflows")}
        if "project_id" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE workflows ADD COLUMN project_id VARCHAR"))


configure_database()


def init_db() -> None:
    from . import models  # noqa: F401
    from .seed import seed_reference_data

    Base.metadata.create_all(bind=engine)
    _apply_schema_updates()
    with SessionLocal() as db:
        seed_reference_data(db)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        configure_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
