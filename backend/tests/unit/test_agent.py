"""Agent 主循环集成测试（流式章节落库）。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from app.agent.agent import Agent
from app.agent.tools import ToolContext
from app.core.llm import LLMClient
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo


class _SeqTransport:
    """每次 stream() 返回下一段预制 chunk 序列。"""

    def __init__(self, seq: list[list[dict[str, Any]]]) -> None:
        self.seq = list(seq)
        self.calls: list[dict[str, Any]] = []

    async def stream(self, url, headers, body):
        self.calls.append(body)
        chunks = self.seq.pop(0) if self.seq else []
        for c in chunks:
            yield c


def _chunks_tool_call(
    tool_id: str, name: str, args: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "id": tool_id,
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(args, ensure_ascii=False),
                                },
                            }
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
    ]


def _chunks_text(*chunks_text: str) -> list[dict[str, Any]]:
    """一段 LLM 输出：连续 N 个文本 delta 后 stop。"""
    out: list[dict[str, Any]] = [
        {"choices": [{"delta": {"content": t}}]} for t in chunks_text
    ]
    out.append({"choices": [{"delta": {}, "finish_reason": "stop"}]})
    return out


@pytest.fixture
def env(tmp_path: Path):
    sq = SqliteRepo(str(tmp_path / "test.db"))
    sq.init_schema()
    fr = FileRepo(tmp_path / "projects")
    now = datetime.now()
    p = Project(
        id="p1",
        name="测试",
        logline="一句话",
        genre="玄幻",
        style_notes="简洁",
        current_phase=Phase.WRITING,
        storage_dir="p1",
        created_at=now,
        updated_at=now,
    )
    sq.insert_project(p)
    fr.create_project("p1")
    return sq, fr, p


@pytest.mark.asyncio
async def test_streaming_chapter_appends_deltas_and_finalizes(env):
    """一次 LLM 调用：begin_chapter → 多个 delta → finalize_chapter。

    真实 LLM 场景下，所有正文会在一个流里输出完，
    之后 LLM 再发 tool_call(finalize_chapter)。
    """
    sq, fr, _p = env
    seq = [
        # 1. LLM 决定开始写：先调用 begin_chapter
        _chunks_tool_call("t1", "begin_chapter", {"title": "楔子", "order": 1}),
        # 2. LLM 一次性输出所有正文 + 收尾 finalize_chapter
        (
            _chunks_text("夜色", "压山。", "剑鸣。")
            + _chunks_tool_call("t2", "finalize_chapter", {"chapter_id": "__placeholder__"})
        ),
    ]
    transport = _SeqTransport(seq)
    llm = LLMClient("https://x", "sk", "gpt-4o", _transport=transport)
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    ctx = ToolContext(project_id="p1", sqlite=sq, file=fr, project_phase=Phase.WRITING)

    events: list[dict[str, Any]] = []
    async for ev in agent.handle(ctx, "请开始写楔子"):
        events.append(ev)

    # 1. 收到 begin_chapter + finalize 的 tool_call
    tool_names = [e["name"] for e in events if e.get("type") == "tool_call"]
    assert "begin_chapter" in tool_names
    assert "finalize_chapter" in tool_names

    # 2. 拿到章节 id
    begin_res = next(
        e for e in events
        if e.get("type") == "tool_result"
        and e["result"].get("data", {}).get("id")
    )
    chapter_id = begin_res["result"]["data"]["id"]

    # 3. DB 里的章节正文是三段 delta 累加
    ch = sq.get_chapter(chapter_id)
    assert ch is not None
    assert ch.content_md == "夜色压山。剑鸣。"
    assert ch.word_count == 8

    # 4. 文件也写入了
    fpath = fr.project_dir("p1") / "chapters" / "0001_楔子.md"
    assert fpath.is_file()
    assert fpath.read_text(encoding="utf-8") == "夜色压山。剑鸣。"


@pytest.mark.asyncio
async def test_streaming_chapter_status_partial_before_finalize(env):
    """在 LLM 决定调用 finalize_chapter 之前，章节状态应为 DRAFT_PARTIAL。

    真实 LLM 流程：round 1 = tool_call(begin_chapter)，
                  round 2 = 文本 delta（streaming_chapter_id 此时已设置）。
    """
    sq, fr, _p = env
    seq = [
        # round 1：开新章节
        _chunks_tool_call("t1", "begin_chapter", {"title": "楔子", "order": 1}),
        # round 2：只输出文本，不 finalize
        _chunks_text("夜色", "压山。"),
    ]
    transport = _SeqTransport(seq)
    llm = LLMClient("https://x", "sk", "gpt-4o", _transport=transport)
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    ctx = ToolContext(project_id="p1", sqlite=sq, file=fr, project_phase=Phase.WRITING)

    chapter_id: str | None = None
    async for ev in agent.handle(ctx, "请开始写"):
        if (
            ev.get("type") == "tool_result"
            and ev["result"].get("data", {}).get("id")
        ):
            chapter_id = ev["result"]["data"]["id"]

    assert chapter_id is not None
    ch = sq.get_chapter(chapter_id)
    assert ch is not None
    assert ch.content_md == "夜色压山。"
    assert ch.status.value == "draft_partial"


@pytest.mark.asyncio
async def test_no_active_streaming_chapter_deltas_do_not_create_chapter(env):
    """未进入流式模式时，文本 delta 不应自动创建章节。"""
    sq, fr, _p = env
    seq = [_chunks_text("普通回答。")]
    transport = _SeqTransport(seq)
    llm = LLMClient("https://x", "sk", "gpt-4o", _transport=transport)
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    ctx = ToolContext(project_id="p1", sqlite=sq, file=fr, project_phase=Phase.WRITING)

    events: list[dict[str, Any]] = []
    async for ev in agent.handle(ctx, "你好"):
        events.append(ev)

    assert any(e["type"] == "delta" for e in events)
    # 没有任何章节被创建
    assert sq.list_chapters("p1") == []
