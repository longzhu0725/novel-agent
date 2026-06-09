"""WebSocket /ws/chat 端点。"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agent.agent import Agent
from app.agent.sessions import SessionRegistry
from app.agent.tools import ToolContext
from app.api.deps import get_file_repo, get_sqlite_repo
from app.core.config import get_settings
from app.core.llm import LLMClient
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.sqlite_repo import SqliteRepo

router = APIRouter()
REGISTRY = SessionRegistry()


def _make_llm() -> LLMClient:
    s = get_settings()
    return LLMClient(
        base_url=s.llm_base_url,
        api_key=s.llm_api_key.get_secret_value(),
        model=s.llm_model,
    )


@router.websocket("/ws/chat")
async def ws_chat(
    ws: WebSocket,
    session_id: str,
    project_id: str,
    sq: SqliteRepo = Depends(get_sqlite_repo),
    fr: FileRepo = Depends(get_file_repo),
) -> None:
    await ws.accept()
    project = sq.get_project(project_id)
    if project is None:
        await ws.send_json(
            {"type": "error", "code": "INTERNAL", "message": "项目不存在"}
        )
        await ws.close()
        return
    session = REGISTRY.register(project_id, session_id)

    async def _send(msg: dict) -> None:
        await ws.send_json(msg)

    session.bind(_send)
    llm = _make_llm()
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json(
                    {"type": "error", "code": "LLM_BAD_RESPONSE", "message": "非 JSON"}
                )
                continue
            kind = msg.get("type")
            if kind == "ping":
                await ws.send_json({"type": "pong"})
            elif kind == "chat.message":
                text = msg.get("text", "")
                ctx = ToolContext(
                    project_id=project_id,
                    sqlite=sq,
                    file=fr,
                    project_phase=Phase(project.current_phase.value),
                )
                correlation_id = msg.get("correlation_id") or uuid.uuid4().hex
                async for ev in agent.handle(
                    ctx, user_text=text, session_id=session_id
                ):
                    payload = dict(ev)
                    payload["correlation_id"] = correlation_id
                    await ws.send_json(payload)
            elif kind == "chat.stop":
                # 简化：忽略 stop（agent 内部会自然结束单次响应）
                pass
    except WebSocketDisconnect:
        REGISTRY.unregister(session_id)
