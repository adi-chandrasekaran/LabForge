from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app import database
from backend.app.config import get_settings
from backend.app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database_path = tmp_path / "nmr_lab_test.sqlite3"
    uploads_path = tmp_path / "uploads"
    monkeypatch.setenv("NMR_LAB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("NMR_LAB_UPLOADS_DIR", str(uploads_path))
    get_settings.cache_clear()
    database.configure_database(f"sqlite:///{database_path}")
    database.init_db()

    with TestClient(app) as test_client:
        yield test_client

    if database.engine is not None:
        database.engine.dispose()
    get_settings.cache_clear()
    database.configure_database()
