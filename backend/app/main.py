from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from .ai_routes import router as ai_router
from .attachment_routes import router as attachment_router
from .chat_routes import router as chat_router
from .config import get_settings
from . import database
from .database import get_db, init_db
from .deps import get_or_create_mock_user
from .docs_routes import router as docs_router
from .experiment_routes import router as experiment_router
from .project_routes import router as project_router
from .schemas import HealthResponse, UserRead
from .summary_routes import router as summary_router
from .sync_routes import router as sync_router
from .workflow_routes import router as workflow_router


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local-first API for the NMR lab notebook.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(workflow_router)
app.include_router(experiment_router)
app.include_router(attachment_router)
app.include_router(chat_router)
app.include_router(project_router)
app.include_router(docs_router)
app.include_router(summary_router)
app.include_router(sync_router)
app.include_router(ai_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    init_db()
    with database.engine.connect() as conn:
        conn.execute(text("select 1"))
    return HealthResponse(status="ok", app=settings.app_name, database="reachable")


@app.get(f"{settings.api_prefix}/me", response_model=UserRead, tags=["users"])
def read_me(db: Session = Depends(get_db)) -> UserRead:
    init_db()
    return get_or_create_mock_user(db)
