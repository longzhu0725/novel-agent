"""Sub-agent 工具注册 + 授权测试。"""
from __future__ import annotations

from datetime import datetime

import pytest

from app.agent.tools import execute_tool, get_tools_for_phase
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
        id="p1", name="x", storage_dir="p1", current_phase=Phase.WRITING,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    sq.insert_project(p)
    fr.create_project("p1")
    return sq, fr, p


def _ctx(sq, fr, phase, llm=None):
    from app.agent.tools import ToolContext
    return ToolContext(project_id="p1", sqlite=sq, file=fr, project_phase=phase, llm=llm)


def test_three_consult_tools_registered():
    for phase in (Phase.WRITING, Phase.DONE):
        names = {t.name for t in get_tools_for_phase(phase)}
        # style 仅在 WRITING/DONE 注册（不需在 FOUNDATION）
        assert "consult_style_expert" in names
        # outline 在 WRITING/DONE
        assert "consult_outline_expert" in names
        # reviewer 在 FOUNDATION/WRITING/DONE
        assert "consult_reviewer" in names
    # INIT 不应注册
    init_names = {t.name for t in get_tools_for_phase(Phase.INIT)}
    assert "consult_style_expert" not in init_names
    assert "consult_outline_expert" not in init_names
    assert "consult_reviewer" not in init_names


def test_consult_tools_rejected_in_init_phase():
    from app.core.llm import LLMTool
    from app.agent.tools import ToolContext, execute_tool
    names = ["consult_outline_expert", "consult_style_expert", "consult_reviewer"]
    for n in names:
        tool = LLMTool(name=n, description="", parameters={})
        result = execute_tool(
            tool,
            ToolContext("p1", None, None, Phase.INIT, llm=None),  # type: ignore[arg-type]
            {"question": "x", "text": "x", "target": "x"},
        )
        assert not result.ok and "不可用" in (result.error or "")


def test_consult_outline_missing_llm(env):
    sq, fr, _ = env
    tool = LLMTool(name="consult_outline_expert", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.WRITING, llm=None), {"question": "x"})
    assert not result.ok and "LLM 不可用" in (result.error or "")


def test_consult_outline_missing_question(env):
    sq, fr, _ = env
    from app.core.llm import LLMClient

    c = LLMClient("https://x", "sk", "m")
    tool = LLMTool(name="consult_outline_expert", description="", parameters={})
    result = execute_tool(tool, _ctx(sq, fr, Phase.WRITING, llm=c), {})
    assert not result.ok and "question" in (result.error or "")
