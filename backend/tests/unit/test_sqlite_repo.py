"""SqliteRepo 单元测试。"""
from __future__ import annotations

from datetime import datetime

import pytest

from app.core.state_machine import Phase
from app.storage.models import (
    Chapter,
    ChapterStatus,
    Character,
    CharacterRelationship,
    ChatMessage,
    OutlineNode,
    Project,
    ProjectContext,
    WorldDoc,
)
from app.storage.sqlite_repo import SqliteRepo


@pytest.fixture
def repo(tmp_path):
    r = SqliteRepo(tmp_path / "test.db")
    r.init_schema()
    return r


def test_init_schema_idempotent(repo):
    repo.init_schema()
    repo.init_schema()  # 不应抛错


def test_insert_and_get_project(repo):
    p = Project(
        id="p1",
        name="测试项目",
        logline="一句话",
        genre="玄幻",
        style_notes="简洁",
        current_phase=Phase.INIT,
        storage_dir="p1",
        created_at=datetime(2026, 6, 9, 12, 0, 0),
        updated_at=datetime(2026, 6, 9, 12, 0, 0),
    )
    repo.insert_project(p)
    got = repo.get_project("p1")
    assert got is not None
    assert got.name == "测试项目"
    assert got.logline == "一句话"
    assert got.current_phase == Phase.INIT


def test_list_projects_empty(repo):
    assert repo.list_projects() == []


def test_list_projects_orders_by_updated_at_desc(repo):
    p1 = Project(id="p1", name="a", storage_dir="p1", current_phase=Phase.INIT,
                 created_at=datetime(2026, 6, 1), updated_at=datetime(2026, 6, 1))
    p2 = Project(id="p2", name="b", storage_dir="p2", current_phase=Phase.INIT,
                 created_at=datetime(2026, 6, 2), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p1)
    repo.insert_project(p2)
    rows = repo.list_projects()
    assert [r.id for r in rows] == ["p2", "p1"]


def test_update_project_phase(repo):
    p = Project(id="p1", name="x", storage_dir="p1", current_phase=Phase.INIT,
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p)
    repo.update_project_phase("p1", Phase.WORLD, datetime(2026, 6, 10))
    assert repo.get_project("p1").current_phase == Phase.WORLD  # type: ignore[union-attr]


def test_delete_project(repo):
    p = Project(id="p1", name="x", storage_dir="p1", current_phase=Phase.INIT,
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p)
    repo.delete_project("p1")
    assert repo.get_project("p1") is None


def test_world_doc_upsert_increments_version(repo):
    repo.upsert_world_doc(WorldDoc(project_id="p1", content_md="# 世界一", version=0))
    first = repo.get_world_doc("p1")
    assert first is not None and first.content_md == "# 世界一" and first.version == 1
    repo.upsert_world_doc(WorldDoc(project_id="p1", content_md="# 世界二", version=0))
    second = repo.get_world_doc("p1")
    assert second is not None and second.content_md == "# 世界二" and second.version == 2


def test_character_crud(repo):
    ch = Character(id="c1", project_id="p1", name="林夕", role="主角",
                   profile_md="剑客", updated_at=datetime(2026, 6, 9))
    repo.insert_character(ch)
    assert repo.get_character("c1") is not None
    assert len(repo.list_characters("p1")) == 1
    ch.profile_md = "剑客 + 复仇者"
    ch.updated_at = datetime(2026, 6, 10)
    repo.update_character(ch)
    assert repo.get_character("c1").profile_md == "剑客 + 复仇者"  # type: ignore[union-attr]
    repo.delete_character("c1")
    assert repo.get_character("c1") is None


def test_relationships(repo):
    rel = CharacterRelationship(id="r1", project_id="p1", source_id="c1",
                                target_id="c2", type="师徒", note="传授")
    repo.add_relationship(rel)
    rows = repo.list_relationships("p1")
    assert len(rows) == 1 and rows[0].type == "师徒"


def test_outline_tree(repo):
    root = OutlineNode(id="n1", project_id="p1", parent_id=None, order=1,
                       title="卷一", summary_md="总纲")
    child = OutlineNode(id="n2", project_id="p1", parent_id="n1", order=1,
                        title="第一章", summary_md="开始")
    repo.insert_outline_node(root)
    repo.insert_outline_node(child)
    rows = repo.list_outline("p1")
    assert len(rows) == 2
    child.title = "第一章改"
    repo.update_outline_node(child)
    assert repo.list_outline("p1")[1].title == "第一章改"
    repo.delete_outline_node("n2")
    assert len(repo.list_outline("p1")) == 1


def test_chapter_crud_and_status(repo):
    ch = Chapter(id="ch1", project_id="p1", outline_node_id="n1", order=1,
                 title="楔子", content_md="正文一", word_count=3,
                 status=ChapterStatus.DRAFT,
                 created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_chapter(ch)
    got = repo.get_chapter("ch1")
    assert got is not None and got.status == ChapterStatus.DRAFT
    ch.status = ChapterStatus.DRAFT_PARTIAL
    ch.content_md = "正文二（流式）"
    ch.updated_at = datetime(2026, 6, 10)
    repo.update_chapter(ch)
    assert repo.get_chapter("ch1").status == ChapterStatus.DRAFT_PARTIAL  # type: ignore[union-attr]
    rows = repo.list_chapters("p1")
    assert len(rows) == 1 and rows[0].order == 1


def test_chat_message_history(repo):
    p = Project(id="p1", name="x", storage_dir="p1", current_phase=Phase.INIT,
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p)
    msgs = [
        ChatMessage(id=f"m{i}", session_id="s1", project_id="p1", role="user",
                    content=f"msg{i}", tool_calls_json="[]",
                    created_at=datetime(2026, 6, 9, 10, i))
        for i in range(3)
    ]
    for m in msgs:
        repo.insert_chat_message(m)
    history = repo.list_chat_messages("p1", "s1", limit=10)
    # 倒序：最新在前
    assert [m.id for m in history] == ["m2", "m1", "m0"]


def test_project_context_upsert(repo):
    ctx = ProjectContext(project_id="p1", phase=Phase.WORLD,
                         rolling_summary="已生成设定", last_active_at=datetime(2026, 6, 9))
    repo.upsert_project_context(ctx)
    got = repo.get_project_context("p1")
    assert got is not None and got.phase == Phase.WORLD
    ctx.phase = Phase.CHARACTERS
    repo.upsert_project_context(ctx)
    assert repo.get_project_context("p1").phase == Phase.CHARACTERS  # type: ignore[union-attr]
