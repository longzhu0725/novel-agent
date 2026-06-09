"""Advisor REST 路由：手动调用 sub-agent。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from app.agent.subagents import (
    consult_outline_expert_sync,
    consult_reviewer_sync,
    consult_style_expert_sync,
)
from app.api.deps import get_sqlite_repo
from app.core.config import get_settings
from app.core.llm import LLMClient
from app.storage.file_repo import FileRepo
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter(prefix="/api/projects/{pid}/advisors", tags=["advisors"])


def _llm() -> LLMClient:
    s = get_settings()
    return LLMClient(
        base_url=s.llm_base_url,
        api_key=s.llm_api_key.get_secret_value(),
        model=s.llm_model,
    )


def _fr() -> FileRepo:
    from app.api.deps import get_file_repo

    return get_file_repo()


@router.post("/outline")
def ask_outline(
    pid: str,
    body: dict[str, Any],
    sq: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, str]:
    p = sq.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    question = (body or {}).get("question", "").strip()
    if not question:
        raise HTTPException(400, "question 必填")
    r = consult_outline_expert_sync(
        llm=_llm(), sq=sq, fr=_fr(), project=p, question=question
    )
    return {"advisor": r.advisor, "advice": r.advice}


@router.post("/style")
def ask_style(
    pid: str,
    body: dict[str, Any] = Body(default_factory=dict),
    sq: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, str]:
    p = sq.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    text = (body or {}).get("text", "").strip()
    if not text:
        raise HTTPException(400, "text 必填")
    r = consult_style_expert_sync(
        llm=_llm(), sq=sq, fr=_fr(), project=p,
        text=text, focus=(body or {}).get("focus", ""),
    )
    return {"advisor": r.advisor, "advice": r.advice}


@router.post("/reviewer")
def ask_reviewer(
    pid: str,
    body: dict[str, Any],
    sq: SqliteRepo = Depends(get_sqlite_repo),
) -> dict[str, str]:
    p = sq.get_project(pid)
    if p is None:
        raise HTTPException(404, "Project not found")
    target = (body or {}).get("target", "").strip()
    if not target:
        raise HTTPException(400, "target 必填")
    r = consult_reviewer_sync(
        llm=_llm(), sq=sq, fr=_fr(), project=p,
        target=target, content_id=(body or {}).get("content_id", ""),
    )
    return {"advisor": r.advisor, "advice": r.advice}
