"""系统提示模板单元测试。"""
from __future__ import annotations

from datetime import datetime

from app.agent.prompts import build_system_prompt
from app.core.state_machine import Phase
from app.storage.models import Project


def test_foundation_phase_prompt_mentions_world_characters_and_tools():
    p = Project(
        id="p1", name="X", genre="玄幻", style_notes="简洁",
        logline="一句话", current_phase=Phase.FOUNDATION,
        storage_dir="p1", created_at=datetime.now(), updated_at=datetime.now(),
    )
    s = build_system_prompt(p, Phase.FOUNDATION, tool_names=["upsert_world_doc"])
    assert "世界观" in s
    assert "人物" in s
    assert "upsert_world_doc" in s


def test_summary_appended_when_present():
    p = Project(
        id="p1", name="X", storage_dir="p1", current_phase=Phase.FOUNDATION,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    s = build_system_prompt(p, Phase.FOUNDATION, rolling_summary="上一段摘要", tool_names=[])
    assert "上一段摘要" in s
