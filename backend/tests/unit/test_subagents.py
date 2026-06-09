"""Sub-agents 单元测试。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator

import pytest

from app.agent.subagents import (
    ProjectContext,
    build_project_context,
    consult_outline_expert,
    consult_reviewer,
    consult_style_expert,
)
from app.core.llm import LLMClient
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import (
    Chapter,
    ChapterStatus,
    Character,
    OutlineNode,
    Project,
    WorldDoc,
)
from app.storage.sqlite_repo import SqliteRepo


class FakeTransport:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    async def stream(self, url, headers, body):
        self.calls.append(body)
        yield {"choices": [{"delta": {"content": self.text}}]}
        yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}


def _make_client(text: str = "好的建议：\n- 第一条\n- 第二条") -> tuple[LLMClient, FakeTransport]:
    t = FakeTransport(text)
    return LLMClient("https://x", "sk", "m", _transport=t), t


@pytest.fixture
def env(tmp_path):
    sq = SqliteRepo(tmp_path / "test.db")
    sq.init_schema()
    fr = FileRepo(tmp_path / "projects")
    now = datetime.now()
    p = Project(
        id="p1", name="测试", logline="一句话", genre="玄幻",
        style_notes="简洁有力", current_phase=Phase.WRITING,
        storage_dir="p1", created_at=now, updated_at=now,
    )
    sq.insert_project(p)
    fr.create_project("p1")
    sq.upsert_world_doc(WorldDoc(project_id="p1", content_md="# 世界一"))
    sq.insert_character(Character(
        id="c1", project_id="p1", name="林夕", role="主角",
        profile_md="剑客", updated_at=now,
    ))
    sq.insert_outline_node(OutlineNode(
        id="n1", project_id="p1", parent_id=None, order=1,
        title="卷一", summary_md="开始",
    ))
    sq.insert_chapter(Chapter(
        id="ch1", project_id="p1", outline_node_id="n1", order=1,
        title="楔子", content_md="夜色压山。", word_count=4,
        status=ChapterStatus.DRAFT, created_at=now, updated_at=now,
    ))
    return sq, fr, p


def test_build_project_context_includes_all_sections(env):
    sq, fr, p = env
    ctx = build_project_context(p, sq, fr)
    block = ctx.to_prompt_block()
    assert "测试" in block
    assert "林夕" in block
    assert "卷一" in block
    assert "楔子" in block
    assert "简洁有力" in block
    assert "世界一" in block


@pytest.mark.asyncio
async def test_consult_outline_expert_returns_advice(env):
    sq, fr, p = env
    c, t = _make_client("伏笔建议：在第一章埋一个剑穗")
    result = await consult_outline_expert(
        llm=c, sq=sq, fr=fr, project=p, question="如何在前 3 章埋伏笔？"
    )
    assert result.advisor == "outline_expert"
    assert "伏笔建议" in result.advice
    # 验证 LLM 真的被调用
    assert len(t.calls) == 1
    body = t.calls[0]
    assert body["model"] == "m"
    user_msg = body["messages"][-1]["content"]
    assert "前 3 章" in user_msg and "林夕" in user_msg


@pytest.mark.asyncio
async def test_consult_style_expert_includes_style_notes_and_text(env):
    sq, fr, p = env
    c, t = _make_client("风格建议：短句更有力")
    result = await consult_style_expert(
        llm=c, sq=sq, fr=fr, project=p,
        text="夜色压山。剑鸣如哭。", focus="节奏",
    )
    assert result.advisor == "style_expert"
    assert "短句" in result.advice
    body = t.calls[0]
    user_msg = body["messages"][-1]["content"]
    assert "简洁有力" in user_msg  # 风格说明注入
    assert "夜色压山" in user_msg    # 待审文本注入
    assert "节奏" in user_msg        # focus 注入


@pytest.mark.asyncio
async def test_consult_reviewer_appends_chapter_when_content_id_given(env):
    sq, fr, p = env
    c, t = _make_client("问题：第 1 句节奏过慢")
    result = await consult_reviewer(
        llm=c, sq=sq, fr=fr, project=p,
        target="检查开头节奏", content_id="ch1",
    )
    assert result.advisor == "reviewer"
    body = t.calls[0]
    user_msg = body["messages"][-1]["content"]
    assert "开头节奏" in user_msg
    assert "夜色压山" in user_msg   # ch1 内容被附加


@pytest.mark.asyncio
async def test_consult_reviewer_works_without_content_id(env):
    sq, fr, p = env
    c, t = _make_client("总体OK，但人物动机要补充")
    result = await consult_reviewer(
        llm=c, sq=sq, fr=fr, project=p,
        target="检查人物动机",
    )
    assert result.advisor == "reviewer"
    body = t.calls[0]
    user_msg = body["messages"][-1]["content"]
    assert "人物动机" in user_msg


@pytest.mark.asyncio
async def test_consult_returns_empty_string_gracefully(env):
    sq, fr, p = env
    c, _ = _make_client("")
    result = await consult_outline_expert(
        llm=c, sq=sq, fr=fr, project=p, question="x"
    )
    assert result.advice == "(无输出)"


def test_project_context_to_prompt_block_handles_empty_lists(tmp_path):
    sq = SqliteRepo(tmp_path / "test.db")
    sq.init_schema()
    fr = FileRepo(tmp_path / "projects")
    p = Project(
        id="empty", name="空", storage_dir="empty", current_phase=Phase.INIT,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    sq.insert_project(p)
    ctx = build_project_context(p, sq, fr)
    block = ctx.to_prompt_block()
    assert "(无)" in block  # 人物/大纲/章节空时占位
