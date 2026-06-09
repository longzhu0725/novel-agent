"""Characters REST 路由。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_file_repo, get_sqlite_repo
from app.storage.file_repo import FileRepo
from app.storage.models import Character
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/characters", tags=["characters"])


def _to_dict(c: Character) -> dict[str, Any]:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "name": c.name,
        "role": c.role,
        "profile_md": c.profile_md,
        "updated_at": c.updated_at.isoformat(),
    }


@router.get("")
def list_characters(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> list[dict[str, Any]]:
    return [_to_dict(c) for c in repo.list_characters(pid)]


@router.post("", status_code=201)
def create_character(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    if repo.get_project(pid) is None:
        raise HTTPException(404, "Project not found")
    cid = uuid.uuid4().hex
    ch = Character(
        id=cid,
        project_id=pid,
        name=body.get("name", "未命名"),
        role=body.get("role", "配角"),
        profile_md=body.get("profile_md", ""),
        updated_at=datetime.now(),
    )
    repo.insert_character(ch)
    fr.write_character(pid, cid, _to_dict(ch))
    return _to_dict(ch)


@router.get("/{cid}")
def get_character(
    pid: str, cid: str, repo: SqliteRepo = Depends(get_sqlite_repo)
) -> dict[str, Any]:
    c = repo.get_character(cid)
    if c is None or c.project_id != pid:
        raise HTTPException(404, "Character not found")
    return _to_dict(c)


@router.patch("/{cid}")
def update_character(
    pid: str,
    cid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    c = repo.get_character(cid)
    if c is None or c.project_id != pid:
        raise HTTPException(404, "Character not found")
    c.name = body.get("name", c.name)
    c.role = body.get("role", c.role)
    c.profile_md = body.get("profile_md", c.profile_md)
    c.updated_at = datetime.now()
    repo.update_character(c)
    fr.write_character(pid, cid, _to_dict(c))
    return _to_dict(c)


@router.delete("/{cid}", status_code=204)
def delete_character(
    pid: str,
    cid: str,
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> None:
    c = repo.get_character(cid)
    if c is None or c.project_id != pid:
        return
    repo.delete_character(cid)
