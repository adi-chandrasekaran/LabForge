from __future__ import annotations

from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from .config import get_settings
from .schemas import ExternalDocRead, ExternalDocSummaryRead


router = APIRouter(prefix="/api/v1/docs", tags=["docs"])
settings = get_settings()
docs_root = (settings.project_root / "external-docs").resolve()


def _all_doc_paths() -> list[Path]:
    return sorted(docs_root.glob("*.md"))


def _slug_from_path(path: Path) -> str:
    return path.stem


def _title_from_content(path: Path) -> str:
    try:
        first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
    except IndexError:
        return path.stem.replace("-", " ").title()
    if first_line.startswith("# "):
        return first_line[2:].strip()
    return path.stem.replace("-", " ").title()


def _doc_summary(path: Path) -> ExternalDocSummaryRead:
    stat = path.stat()
    return ExternalDocSummaryRead(
        slug=_slug_from_path(path),
        title=_title_from_content(path),
        updated_at=datetime.fromtimestamp(stat.st_mtime),
    )


def _resolve_doc_path(slug: str) -> Path:
    candidate = (docs_root / f"{slug}.md").resolve()
    if docs_root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return candidate


@router.get("", response_model=list[ExternalDocSummaryRead])
def list_external_docs() -> list[ExternalDocSummaryRead]:
    return [_doc_summary(path) for path in _all_doc_paths()]


@router.get("/{slug}", response_model=ExternalDocRead)
def read_external_doc(slug: str) -> ExternalDocRead:
    path = _resolve_doc_path(slug)
    summary = _doc_summary(path)
    return ExternalDocRead(
        slug=summary.slug,
        title=summary.title,
        updated_at=summary.updated_at,
        content=path.read_text(encoding="utf-8"),
    )
