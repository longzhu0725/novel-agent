"""Pydantic 模型测试。"""
from datetime import datetime

from app.storage.models import (
    Chapter,
    ChapterStatus,
    Character,
    CharacterRelationship,
    ChatMessage,
    OutlineNode,
    Phase,
    Project,
    ProjectContext,
    WorldDoc,
)


def test_project_round_trip() -> None:
    p = Project(
        id="p1",
        name="记忆贩子",
        logline="未来都市的记忆交易黑市",
        genre="赛博朋克",
        style_notes="硬冷、碎片化",
        current_phase=Phase.INIT,
        storage_dir="p1",
        created_at=datetime(2026, 6, 9),
        updated_at=datetime(2026, 6, 9),
    )
    j = p.model_dump_json()
    p2 = Project.model_validate_json(j)
    assert p2.id == "p1"
    assert p2.current_phase == Phase.INIT


def test_world_doc_default_version() -> None:
    w = WorldDoc(project_id="p1", content_md="")
    assert w.version == 0


def test_character_fields() -> None:
    c = Character(
        id="c1",
        project_id="p1",
        name="林夕",
        role="主角",
        profile_md="...",
        updated_at=datetime(2026, 6, 9),
    )
    assert c.role == "主角"


def test_relationship_fields() -> None:
    r = CharacterRelationship(
        id="r1",
        project_id="p1",
        source_id="c1",
        target_id="c2",
        type="师父",
        note="教过主角记忆编织术",
    )
    assert r.type == "师父"


def test_outline_node_root_and_child() -> None:
    root = OutlineNode(
        id="n1",
        project_id="p1",
        parent_id=None,
        order=0,
        title="卷一",
        summary_md="",
    )
    child = OutlineNode(
        id="n2",
        project_id="p1",
        parent_id="n1",
        order=0,
        title="第一章",
        summary_md="",
    )
    assert root.parent_id is None
    assert child.parent_id == "n1"


def test_chapter_status_enum() -> None:
    c = Chapter(
        id="ch1",
        project_id="p1",
        outline_node_id=None,
        order=1,
        title="第一章",
        content_md="",
        word_count=0,
        status=ChapterStatus.DRAFT,
        created_at=datetime(2026, 6, 9),
        updated_at=datetime(2026, 6, 9),
    )
    assert c.status == ChapterStatus.DRAFT


def test_chat_message_persists_tool_calls() -> None:
    m = ChatMessage(
        id="m1",
        session_id="s1",
        project_id="p1",
        role="assistant",
        content="",
        tool_calls_json='[{"name": "x"}]',
        created_at=datetime(2026, 6, 9),
    )
    assert m.tool_calls_json.startswith("[")


def test_project_context_default_summary() -> None:
    c = ProjectContext(project_id="p1")
    assert c.rolling_summary == ""
    assert c.phase == Phase.INIT
