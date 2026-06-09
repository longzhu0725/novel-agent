"""Projects REST 路由。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_file_repo, get_sqlite_repo
from app.core.errors import ProtocolError
from app.core.state_machine import Phase, assert_legal_transition
from app.storage.file_repo import FileRepo
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_dict(p: Project) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "logline": p.logline,
        "genre": p.genre,
        "style_notes": p.style_notes,
        "current_phase": p.current_phase.value,
        "storage_dir": p.storage_dir,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.get("")
def list_projects(repo: SqliteRepo = Depends(get_sqlite_repo)) -> list[dict[str, Any]]:
    return [_to_dict(p) for p in repo.list_projects()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    body: dict[str, Any],
    sq: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    now = datetime.now()
    pid = uuid.uuid4().hex
    p = Project(
        id=pid,
        name=body.get("name", "未命名"),
        logline=body.get("logline", ""),
        genre=body.get("genre", ""),
        style_notes=body.get("style_notes", ""),
        current_phase=Phase.INIT,
        storage_dir=pid,
        created_at=now,
        updated_at=now,
    )
    sq.insert_project(p)
    fr.create_project(pid)
    return _to_dict(p)


@router.get("/{pid}")
def get_project(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    return _to_dict(p)


@router.patch("/{pid}")
def update_project(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    repo.update_project_meta(
        pid,
        name=body.get("name", p.name),
        logline=body.get("logline", p.logline),
        genre=body.get("genre", p.genre),
        style_notes=body.get("style_notes", p.style_notes),
        updated_at=datetime.now(),
    )
    updated = repo.get_project(pid)
    return _to_dict(updated)  # type: ignore[arg-type]


@router.delete("/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    pid: str,
    sq: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> None:
    sq.delete_project(pid)
    fr.delete_project(pid)


@router.post("/{pid}/phase")
def advance_phase(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    try:
        to = Phase(body["to"])
        assert_legal_transition(p.current_phase, to)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e)) from e
    except ProtocolError as e:
        raise HTTPException(400, {"code": e.code.value, "message": e.message}) from e
    repo.update_project_phase(pid, to, datetime.now())
    updated = repo.get_project(pid)
    return _to_dict(updated)  # type: ignore[arg-type]
