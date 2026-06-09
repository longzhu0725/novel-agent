"""Chat history REST 路由。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_sqlite_repo
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/chat", tags=["chat"])


@router.get("/history")
def history(
    pid: str,
    session_id: str = Query("default"),
    limit: int = Query(50, ge=1, le=500),
    repo: SqliteRepo = Depends(get_sqlite_repo),
) -> list[dict[str, Any]]:
    rows = repo.list_chat_messages(pid, session_id, limit=limit)
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "project_id": m.project_id,
            "role": m.role,
            "content": m.content,
            "tool_calls_json": m.tool_calls_json,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]
