"""World REST 路由。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_file_repo, get_sqlite_repo
from app.storage.file_repo import FileRepo
from app.storage.models import WorldDoc
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/world", tags=["world"])


@router.get("")
def get_world(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> dict[str, Any]:
    doc = repo.get_world_doc(pid)
    if doc is None:
        return {"content_md": "", "version": 0}
    return {"content_md": doc.content_md, "version": doc.version}


@router.put("")
def put_world(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    if repo.get_project(pid) is None:
        raise HTTPException(404, "Project not found")
    content = body.get("content_md", "")
    repo.upsert_world_doc(WorldDoc(project_id=pid, content_md=content, version=0))
    # 同步落盘
    fr.create_project(pid) if not fr.project_dir(pid).exists() else None  # 幂等兜底
    fr.write_world(pid, content)
    doc = repo.get_world_doc(pid)
    return {"content_md": doc.content_md, "version": doc.version}  # type: ignore[union-attr]
