"""Outline REST 路由。"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_sqlite_repo
from app.storage.models import OutlineNode
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/outline", tags=["outline"])


def _to_dict(n: OutlineNode) -> dict[str, Any]:
    return {
        "id": n.id,
        "project_id": n.project_id,
        "parent_id": n.parent_id,
        "order": n.order,
        "title": n.title,
        "summary_md": n.summary_md,
        "chapter_id": n.chapter_id,
    }


@router.get("")
def list_outline(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> list[dict[str, Any]]:
    return [_to_dict(n) for n in repo.list_outline(pid)]


@router.post("", status_code=201)
def create_outline_node(
    pid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, Any]:
    if repo.get_project(pid) is None:
        raise HTTPException(404, "Project not found")
    n = OutlineNode(
        id=uuid.uuid4().hex,
        project_id=pid,
        parent_id=body.get("parent_id"),
        order=int(body.get("order", 0)),
        title=body.get("title", "未命名"),
        summary_md=body.get("summary_md", ""),
        chapter_id=body.get("chapter_id"),
    )
    repo.insert_outline_node(n)
    return _to_dict(n)


@router.patch("/{nid}")
def update_outline_node(
    pid: str,
    nid: str,
    body: dict[str, Any],
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, Any]:
    nodes = repo.list_outline(pid)
    target = next((n for n in nodes if n.id == nid), None)
    if target is None:
        raise HTTPException(404, "OutlineNode not found")
    if "parent_id" in body:
        target.parent_id = body["parent_id"]
    if "order" in body:
        target.order = int(body["order"])
    if "title" in body:
        target.title = body["title"]
    if "summary_md" in body:
        target.summary_md = body["summary_md"]
    if "chapter_id" in body:
        target.chapter_id = body["chapter_id"]
    repo.update_outline_node(target)
    return _to_dict(target)


@router.delete("/{nid}", status_code=204)
def delete_outline_node(
    pid: str, nid: str, repo: SqliteRepo = Depends(get_sqlite_repo)
) -> None:
    repo.delete_outline_node(nid)
