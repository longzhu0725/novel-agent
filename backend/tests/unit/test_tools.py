"""工具注册表单元测试。"""
from __future__ import annotations

from datetime import datetime

import pytest

from app.agent.tools import (
    ToolContext,
    execute_tool,
    get_tool_def,
    get_tools_for_phase,
)
from app.core.llm import LLMTool
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo


@pytest.fixture
def env(tmp_path):
    sq = SqliteRepo(tmp_path / "test.db")
    sq.init_schema()
    fr = FileRepo(tmp_path / "projects")
    p = Project(
        id="p1",
        name="x",
        storage_dir="p1",
        current_phase=Phase.FOUNDATION,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    sq.insert_project(p)
    fr.create_project("p1")
    return sq, fr, p


def _ctx(sq, fr, phase: Phase) -> ToolContext:
    return ToolContext(project_id="p1", sqlite=sq, file=fr, project_phase=phase)


def test_get_tools_for_phase_filters_by_phase():
    tools = get_tools_for_phase(Phase.FOUNDATION)
    names = {t.name for t in tools}
    assert "upsert_world_doc" in names
    assert "create_character" in names
    assert "begin_chapter" not in names


def test_execute_tool_validates_required_args(env):
    sq, fr, _ = env
    tool = LLMTool(name="create_character", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {})
    assert not result.ok and "缺少必填" in (result.error or "")


def test_execute_tool_rejects_wrong_phase(env):
    sq, fr, _ = env
    tool = LLMTool(name="begin_chapter", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {"title": "X", "order": 1})
    assert not result.ok and "不可用" in (result.error or "")


def test_execute_tool_unknown_tool(env):
    sq, fr, _ = env
    tool = LLMTool(name="nope", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {})
    assert not result.ok and "未知工具" in (result.error or "")


def test_execute_tool_args_must_be_dict(env):
    sq, fr, _ = env
    tool = LLMTool(name="read_world_doc", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), "not a dict")  # type: ignore[arg-type]
    assert not result.ok


def test_create_character_works(env):
    sq, fr, _ = env
    tool = LLMTool(name="create_character", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {"name": "林夕"})
    assert result.ok and result.data and "id" in result.data
    assert len(sq.list_characters("p1")) == 1


def test_advance_phase_legal_transition(env):
    sq, fr, p = env
    tool = LLMTool(name="advance_phase", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {"to": "WRITING"})
    assert result.ok
    assert sq.get_project("p1").current_phase == Phase.WRITING  # type: ignore[union-attr]


def test_advance_phase_illegal_transition(env):
    sq, fr, _ = env
    tool = LLMTool(name="advance_phase", description="", parameters={})
    # 当前 FOUNDATION, 试图直接到 DONE (跳级)
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {"to": "DONE"})
    assert not result.ok


def test_get_tool_def_known():
    defn = get_tool_def("create_character")
    assert defn is not None and defn.name == "create_character"


def test_read_project_summary(env):
    sq, fr, _ = env
    tool = LLMTool(name="read_project_summary", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.FOUNDATION), {})
    assert result.ok
    assert result.data["current_phase"] == "FOUNDATION"


def test_begin_chapter_creates_empty_partial_chapter(env):
    sq, fr, _ = env
    tool = LLMTool(name="begin_chapter", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.WRITING),
                          {"title": "楔子", "order": 1})
    assert result.ok
    chid = result.data["id"]
    assert result.data["stream"] is True
    ch = sq.get_chapter(chid)
    assert ch is not None
    assert ch.content_md == ""
    assert ch.status.value == "draft_partial"
    # 文件也写了
    assert (fr.project_dir("p1") / "chapters" / "0001_楔子.md").is_file()


def test_append_then_finalize_chapter(env):
    sq, fr, _ = env
    ctx = _ctx(sq, fr, Phase.WRITING)
    begin = execute_tool(LLMTool(name="begin_chapter", description="", parameters={}),
                         ctx, {"title": "楔子", "order": 1})
    chid = begin.data["id"]
    for delta in ["夜色", "压山。", "剑", "鸣。"]:
        execute_tool(LLMTool(name="append_to_chapter", description="", parameters={}),
                     ctx, {"chapter_id": chid, "delta": delta})
    ch = sq.get_chapter(chid)
    assert ch.content_md == "夜色压山。剑鸣。"
    assert ch.word_count == 8  # 夜色压山。剑鸣。= 8 非空白
    assert ch.status.value == "draft_partial"
    # 落盘
    fpath = fr.project_dir("p1") / "chapters" / "0001_楔子.md"
    assert fpath.read_text(encoding="utf-8") == "夜色压山。剑鸣。"
    # finalize
    res = execute_tool(LLMTool(name="finalize_chapter", description="", parameters={}),
                       ctx, {"chapter_id": chid})
    assert res.ok
    assert sq.get_chapter(chid).status.value == "draft"


def test_finalize_chapter_unknown_id(env):
    sq, fr, _ = env
    tool = LLMTool(name="finalize_chapter", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.WRITING), {"chapter_id": "nope"})
    assert not result.ok
