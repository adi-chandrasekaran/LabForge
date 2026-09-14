from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    app_name: str = "NMR Lab Notebook API"
    api_prefix: str = "/api/v1"
    app_mode: str = "local"
    database_backend: str = "sqlite"
    auth_backend: str = "mock"
    storage_backend: str = "local"
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    mock_user_id: str = "user-dev-chen"
    mock_user_role: str = "professor"
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4174",
            "http://localhost:4174",
        ]
    )
    allowed_origin_regex: str = r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$"
    supabase_url: Optional[str] = None
    supabase_project_ref: Optional[str] = None
    tigris_bucket: Optional[str] = None
    openai_api_key: Optional[str] = None
    agent_model: str = "gpt-5.5"

    @property
    def data_dir(self) -> Path:
        configured = os.getenv("NMR_LAB_DATA_DIR")
        if configured:
            return Path(configured)
        return self.project_root / "data"

    @property
    def uploads_dir(self) -> Path:
        configured = os.getenv("NMR_LAB_UPLOADS_DIR")
        if configured:
            return Path(configured)
        return self.data_dir / "uploads"

    @property
    def database_url(self) -> str:
        return os.getenv("NMR_LAB_DATABASE_URL", f"sqlite:///{self.data_dir / 'nmr_lab.sqlite3'}")


@lru_cache
def get_settings() -> Settings:
    allowed_origins = os.getenv("NMR_LAB_ALLOWED_ORIGINS")
    return Settings(
        app_mode=os.getenv("NMR_LAB_APP_MODE", "local"),
        database_backend=os.getenv("NMR_LAB_DATABASE_BACKEND", "sqlite"),
        auth_backend=os.getenv("NMR_LAB_AUTH_BACKEND", "mock"),
        storage_backend=os.getenv("NMR_LAB_STORAGE_BACKEND", "local"),
        mock_user_id=os.getenv("NMR_LAB_MOCK_USER_ID", "user-dev-chen"),
        mock_user_role=os.getenv("NMR_LAB_MOCK_USER_ROLE", "professor"),
        allowed_origins=[
            origin.strip()
            for origin in allowed_origins.split(",")
            if origin.strip()
        ]
        if allowed_origins
        else [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4174",
            "http://localhost:4174",
        ],
        allowed_origin_regex=os.getenv(
            "NMR_LAB_ALLOWED_ORIGIN_REGEX",
            r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
        ),
        supabase_url=os.getenv("NMR_LAB_SUPABASE_URL"),
        supabase_project_ref=os.getenv("NMR_LAB_SUPABASE_PROJECT_REF"),
        tigris_bucket=os.getenv("NMR_LAB_TIGRIS_BUCKET"),
        openai_api_key=os.getenv("NMR_LAB_OPENAI_API_KEY"),
        agent_model=os.getenv("NMR_LAB_AGENT_MODEL", "gpt-5.5"),
    )
