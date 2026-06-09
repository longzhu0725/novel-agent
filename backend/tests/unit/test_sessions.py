"""SessionRegistry 单元测试。"""
from __future__ import annotations

import pytest

from app.agent.sessions import Session, SessionRegistry


@pytest.mark.asyncio
async def test_register_and_get():
    reg = SessionRegistry()
    s = reg.register("p1", "s1")
    assert isinstance(s, Session)
    assert reg.get("s1") is s


@pytest.mark.asyncio
async def test_unregister_removes_session():
    reg = SessionRegistry()
    reg.register("p1", "s1")
    reg.unregister("s1")
    assert reg.get("s1") is None
    assert reg._by_p.get("p1", set()) == set()  # noqa: SLF001


@pytest.mark.asyncio
async def test_broadcast_only_to_same_project():
    reg = SessionRegistry()
    s1 = reg.register("p1", "s1")
    s2 = reg.register("p1", "s2")
    s_other = reg.register("p2", "s3")
    received: list[dict] = []
    s1.bind(lambda m: _r(received, m))
    s2.bind(lambda m: _r(received, m))
    s_other.bind(lambda m: _r(received, m))
    await reg.broadcast("p1", {"type": "delta", "text": "x"})
    assert len(received) == 2


async def _r(bucket: list[dict], msg: dict) -> None:
    bucket.append(msg)
