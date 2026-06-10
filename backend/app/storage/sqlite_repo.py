"""SQLite 仓储（同步）。"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

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


_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL,
    logline TEXT NOT NULL DEFAULT '', genre TEXT NOT NULL DEFAULT '',
    style_notes TEXT NOT NULL DEFAULT '',
    current_phase TEXT NOT NULL, storage_dir TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS world_docs (
    project_id TEXT PRIMARY KEY,
    content_md TEXT NOT NULL DEFAULT '', version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    name TEXT NOT NULL, role TEXT NOT NULL DEFAULT '配角',
    profile_md TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
CREATE TABLE IF NOT EXISTS character_relationships (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    source_id TEXT NOT NULL, target_id TEXT NOT NULL,
    type TEXT NOT NULL, note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rel_project ON character_relationships(project_id);
CREATE TABLE IF NOT EXISTS outline_nodes (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, parent_id TEXT,
    "order" INTEGER NOT NULL, title TEXT NOT NULL,
    summary_md TEXT NOT NULL DEFAULT '', chapter_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_outline_project ON outline_nodes(project_id);
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, outline_node_id TEXT,
    "order" INTEGER NOT NULL, title TEXT NOT NULL,
    content_md TEXT NOT NULL DEFAULT '', word_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id);
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, project_id TEXT NOT NULL,
    role TEXT NOT NULL, content TEXT NOT NULL DEFAULT '',
    tool_calls_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_ps ON chat_messages(project_id, session_id, created_at);
CREATE TABLE IF NOT EXISTS project_context (
    project_id TEXT PRIMARY KEY, phase TEXT NOT NULL,
    rolling_summary TEXT NOT NULL DEFAULT '', last_active_at TEXT
);
"""


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SqliteRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA journal_mode = WAL")
        return c

    def init_schema(self) -> None:
        with self._conn() as c:
            c.executescript(_SCHEMA)
            self._migrate_legacy_phases(c)

    def _migrate_legacy_phases(self, c: sqlite3.Connection) -> None:
        """老 phase 字符串（WORLD/CHARACTERS/OUTLINE）→ 新 phase（FOUNDATION/WRITING）。"""
        from app.core.state_machine import migrate_legacy_phase
        rows = c.execute("SELECT id, current_phase FROM projects").fetchall()
        for r in rows:
            new_phase = migrate_legacy_phase(r["current_phase"])
            if new_phase.value != r["current_phase"]:
                c.execute(
                    "UPDATE projects SET current_phase = ? WHERE id = ?",
                    (new_phase.value, r["id"]),
                )
    # ---------- Project ----------
    def insert_project(self, p: Project) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    p.id, p.name, p.logline, p.genre, p.style_notes,
                    p.current_phase.value, p.storage_dir,
                    _iso(p.created_at), _iso(p.updated_at),
                ),
            )

    def get_project(self, pid: str) -> Project | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        return self._row_to_project(r) if r else None

    def list_projects(self) -> list[Project]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [self._row_to_project(r) for r in rows]

    def update_project_phase(self, pid: str, phase: Phase, updated_at: datetime) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE projects SET current_phase=?, updated_at=? WHERE id=?",
                (phase.value, _iso(updated_at), pid),
            )

    def update_project_meta(
        self,
        pid: str,
        *,
        name: str,
        logline: str,
        genre: str,
        style_notes: str,
        updated_at: datetime,
    ) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE projects SET name=?, logline=?, genre=?, style_notes=?, "
                "updated_at=? WHERE id=?",
                (name, logline, genre, style_notes, _iso(updated_at), pid),
            )

    def delete_project(self, pid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM projects WHERE id=?", (pid,))

    # ---------- WorldDoc ----------
    def upsert_world_doc(self, w: WorldDoc) -> None:
        # 每次 upsert 都让 version 自增（首次插入为 1），便于前端判断是否需要重新拉取
        with self._conn() as c:
            c.execute(
                "INSERT INTO world_docs (project_id, content_md, version) VALUES (?, ?, 1) "
                "ON CONFLICT(project_id) DO UPDATE SET "
                "content_md=excluded.content_md, version=world_docs.version+1",
                (w.project_id, w.content_md),
            )

    def get_world_doc(self, pid: str) -> WorldDoc | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM world_docs WHERE project_id=?", (pid,)).fetchone()
        if r is None:
            return None
        return WorldDoc(project_id=r["project_id"], content_md=r["content_md"], version=r["version"])

    # ---------- Character ----------
    def insert_character(self, ch: Character) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO characters VALUES (?,?,?,?,?,?)",
                (ch.id, ch.project_id, ch.name, ch.role, ch.profile_md, _iso(ch.updated_at)),
            )

    def get_character(self, cid: str) -> Character | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
        if r is None:
            return None
        return Character(
            id=r["id"], project_id=r["project_id"], name=r["name"],
            role=r["role"], profile_md=r["profile_md"],
            updated_at=_parse(r["updated_at"]),  # type: ignore[arg-type]
        )

    def list_characters(self, pid: str) -> list[Character]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM characters WHERE project_id=? ORDER BY name", (pid,)
            ).fetchall()
        return [
            Character(
                id=r["id"], project_id=r["project_id"], name=r["name"],
                role=r["role"], profile_md=r["profile_md"],
                updated_at=_parse(r["updated_at"]),  # type: ignore[arg-type]
            )
            for r in rows
        ]

    def update_character(self, ch: Character) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE characters SET name=?, role=?, profile_md=?, updated_at=? WHERE id=?",
                (ch.name, ch.role, ch.profile_md, _iso(ch.updated_at), ch.id),
            )

    def delete_character(self, cid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM characters WHERE id=?", (cid,))

    def add_relationship(self, r: CharacterRelationship) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO character_relationships VALUES (?,?,?,?,?,?)",
                (r.id, r.project_id, r.source_id, r.target_id, r.type, r.note),
            )

    def list_relationships(self, pid: str) -> list[CharacterRelationship]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM character_relationships WHERE project_id=?", (pid,)
            ).fetchall()
        return [
            CharacterRelationship(
                id=r["id"], project_id=r["project_id"],
                source_id=r["source_id"], target_id=r["target_id"],
                type=r["type"], note=r["note"],
            )
            for r in rows
        ]

    # ---------- Outline ----------
    def insert_outline_node(self, n: OutlineNode) -> None:
        with self._conn() as c:
            c.execute(
                'INSERT INTO outline_nodes VALUES (?,?,?,?,?,?,?)',
                (n.id, n.project_id, n.parent_id, n.order, n.title, n.summary_md, n.chapter_id),
            )

    def update_outline_node(self, n: OutlineNode) -> None:
        with self._conn() as c:
            c.execute(
                'UPDATE outline_nodes SET parent_id=?, "order"=?, title=?, '
                'summary_md=?, chapter_id=? WHERE id=?',
                (n.parent_id, n.order, n.title, n.summary_md, n.chapter_id, n.id),
            )

    def delete_outline_node(self, nid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM outline_nodes WHERE id=?", (nid,))

    def list_outline(self, pid: str) -> list[OutlineNode]:
        with self._conn() as c:
            rows = c.execute(
                'SELECT * FROM outline_nodes WHERE project_id=? ORDER BY "order"', (pid,)
            ).fetchall()
        return [
            OutlineNode(
                id=r["id"], project_id=r["project_id"], parent_id=r["parent_id"],
                order=r["order"], title=r["title"], summary_md=r["summary_md"],
                chapter_id=r["chapter_id"],
            )
            for r in rows
        ]

    # ---------- Chapter ----------
    def insert_chapter(self, ch: Chapter) -> None:
        with self._conn() as c:
            c.execute(
                'INSERT INTO chapters VALUES (?,?,?,?,?,?,?,?,?,?)',
                (
                    ch.id, ch.project_id, ch.outline_node_id, ch.order, ch.title,
                    ch.content_md, ch.word_count, ch.status.value,
                    _iso(ch.created_at), _iso(ch.updated_at),
                ),
            )

    def update_chapter(self, ch: Chapter) -> None:
        with self._conn() as c:
            c.execute(
                'UPDATE chapters SET outline_node_id=?, "order"=?, title=?, '
                'content_md=?, word_count=?, status=?, updated_at=? WHERE id=?',
                (
                    ch.outline_node_id, ch.order, ch.title, ch.content_md,
                    ch.word_count, ch.status.value, _iso(ch.updated_at), ch.id,
                ),
            )

    def get_chapter(self, chid: str) -> Chapter | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM chapters WHERE id=?", (chid,)).fetchone()
        return self._row_to_chapter(r) if r else None

    def list_chapters(self, pid: str) -> list[Chapter]:
        with self._conn() as c:
            rows = c.execute(
                'SELECT * FROM chapters WHERE project_id=? ORDER BY "order"', (pid,)
            ).fetchall()
        return [self._row_to_chapter(r) for r in rows]

    def delete_chapter(self, chid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM chapters WHERE id=?", (chid,))

    # ---------- ChatMessage ----------
    def insert_chat_message(self, m: ChatMessage) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO chat_messages VALUES (?,?,?,?,?,?,?)",
                (
                    m.id, m.session_id, m.project_id, m.role, m.content,
                    m.tool_calls_json, _iso(m.created_at),
                ),
            )

    def list_chat_messages(self, pid: str, sid: str, limit: int = 50) -> list[ChatMessage]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM chat_messages WHERE project_id=? AND session_id=? "
                "ORDER BY created_at DESC LIMIT ?",
                (pid, sid, limit),
            ).fetchall()
        return [
            ChatMessage(
                id=r["id"], session_id=r["session_id"], project_id=r["project_id"],
                role=r["role"], content=r["content"],
                tool_calls_json=r["tool_calls_json"],
                created_at=_parse(r["created_at"]),  # type: ignore[arg-type]
            )
            for r in rows
        ]

    # ---------- ProjectContext ----------
    def get_project_context(self, pid: str) -> ProjectContext | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM project_context WHERE project_id=?", (pid,)).fetchone()
        if r is None:
            return None
        return ProjectContext(
            project_id=r["project_id"], phase=Phase(r["phase"]),
            rolling_summary=r["rolling_summary"],
            last_active_at=_parse(r["last_active_at"]),
        )

    def upsert_project_context(self, ctx: ProjectContext) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO project_context VALUES (?,?,?,?) "
                "ON CONFLICT(project_id) DO UPDATE SET "
                "phase=excluded.phase, rolling_summary=excluded.rolling_summary, "
                "last_active_at=excluded.last_active_at",
                (ctx.project_id, ctx.phase.value, ctx.rolling_summary, _iso(ctx.last_active_at)),
            )

    # ---------- 私有 ----------
    @staticmethod
    def _row_to_project(r: sqlite3.Row) -> Project:
        return Project(
            id=r["id"], name=r["name"], logline=r["logline"],
            genre=r["genre"], style_notes=r["style_notes"],
            current_phase=Phase(r["current_phase"]), storage_dir=r["storage_dir"],
            created_at=_parse(r["created_at"]),  # type: ignore[arg-type]
            updated_at=_parse(r["updated_at"]),  # type: ignore[arg-type]
        )

    @staticmethod
    def _row_to_chapter(r: sqlite3.Row) -> Chapter:
        return Chapter(
            id=r["id"], project_id=r["project_id"], outline_node_id=r["outline_node_id"],
            order=r["order"], title=r["title"], content_md=r["content_md"],
            word_count=r["word_count"], status=ChapterStatus(r["status"]),
            created_at=_parse(r["created_at"]),  # type: ignore[arg-type]
            updated_at=_parse(r["updated_at"]),  # type: ignore[arg-type]
        )
