"""Chapters REST 路由。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_file_repo, get_sqlite_repo
from app.storage.file_repo import FileRepo
from app.storage.models import Chapter, ChapterStatus
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/chapters", tags=["chapters"])


def _to_dict(ch: Chapter) -> dict[str, Any]:
    return {
        "id": ch.id,
        "project_id": ch.project_id,
        "outline_node_id": ch.outline_node_id,
        "order": ch.order,
        "title": ch.title,
        "content_md": ch.content_md,
        "word_count": ch.word_count,
        "status": ch.status.value,
        "created_at": ch.created_at.isoformat(),
        "updated_at": ch.updated_at.isoformat(),
    }


@router.get("")
def list_chapters(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> list[dict[str, Any]]:
    return [_to_dict(c) for c in repo.list_chapters(pid)]


@router.post("", status_code=201)
def create_chapter(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    if repo.get_project(pid) is None:
        raise HTTPException(404, "Project not found")
    now = datetime.now()
    content = body.get("content_md", "")
    ch = Chapter(
        id=uuid.uuid4().hex,
        project_id=pid,
        outline_node_id=body.get("outline_node_id"),
        order=int(body.get("order", 0)),
        title=body.get("title", "未命名"),
        content_md=content,
        word_count=_count_words(content),
        status=ChapterStatus(body.get("status", "draft")),
        created_at=now,
        updated_at=now,
    )
    repo.insert_chapter(ch)
    fr.write_chapter(pid, ch.order, ch.title, content)
    return _to_dict(ch)


@router.patch("/{chid}")
def update_chapter(
    pid: str,
    chid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> dict[str, Any]:
    ch = repo.get_chapter(chid)
    if ch is None or ch.project_id != pid:
        raise HTTPException(404, "Chapter not found")
    if "title" in body:
        ch.title = body["title"]
    if "content_md" in body:
        ch.content_md = body["content_md"]
        ch.word_count = _count_words(ch.content_md)
    if "order" in body:
        ch.order = int(body["order"])
    if "status" in body:
        ch.status = ChapterStatus(body["status"])
    if "outline_node_id" in body:
        ch.outline_node_id = body["outline_node_id"]
    ch.updated_at = datetime.now()
    repo.update_chapter(ch)
    fr.write_chapter(pid, ch.order, ch.title, ch.content_md)
    return _to_dict(ch)


@router.get("/{chid}")
def get_chapter(
    pid: str, chid: str, repo: SqliteRepo = Depends(get_sqlite_repo)
) -> dict[str, Any]:
    ch = repo.get_chapter(chid)
    if ch is None or ch.project_id != pid:
        raise HTTPException(404, "Chapter not found")
    return _to_dict(ch)


def _count_words(s: str) -> int:
    # 中英文混合按字符计，空白不计
    return sum(1 for c in s if not c.isspace())
