"""WS 会话注册表 + 项目级事件总线。"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable


class Session:
    def __init__(self, project_id: str, session_id: str) -> None:
        self.project_id = project_id
        self.session_id = session_id
        self._send_fn: Callable[[dict[str, Any]], Awaitable[None]] | None = None

    def bind(self, fn: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._send_fn = fn

    async def send(self, msg: dict[str, Any]) -> None:
        if self._send_fn is not None:
            await self._send_fn(msg)


class SessionRegistry:
    def __init__(self) -> None:
        self._by_s: dict[str, Session] = {}
        self._by_p: dict[str, set[str]] = {}

    def register(self, project_id: str, session_id: str) -> Session:
        s = Session(project_id, session_id)
        self._by_s[session_id] = s
        self._by_p.setdefault(project_id, set()).add(session_id)
        return s

    def get(self, session_id: str) -> Session | None:
        return self._by_s.get(session_id)

    def unregister(self, session_id: str) -> None:
        s = self._by_s.pop(session_id, None)
        if s is None:
            return
        self._by_p.get(s.project_id, set()).discard(session_id)

    async def broadcast(self, project_id: str, msg: dict[str, Any]) -> None:
        ids = [i for i in self._by_p.get(project_id, set()) if i in self._by_s]
        await asyncio.gather(*(self._by_s[i].send(msg) for i in ids))
