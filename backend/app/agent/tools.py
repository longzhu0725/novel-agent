"""Agent 工具：按阶段授权 + JSON Schema。"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from app.core.llm import LLMTool
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import (
    Character,
    Chapter,
    ChapterStatus,
    OutlineNode,
    ProjectContext,
    WorldDoc,
)
from app.storage.sqlite_repo import SqliteRepo


@dataclass
class ToolContext:
    project_id: str
    sqlite: SqliteRepo
    file: FileRepo
    project_phase: Phase


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None


# ---------------- impls ----------------
def _impl_upsert_world_doc(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    content = args.get("content_md", "")
    ctx.sqlite.upsert_world_doc(WorldDoc(project_id=ctx.project_id, content_md=content, version=0))
    if not ctx.file.project_dir(ctx.project_id).exists():
        ctx.file.create_project(ctx.project_id)
    ctx.file.write_world(ctx.project_id, content)
    doc = ctx.sqlite.get_world_doc(ctx.project_id)
    return ToolResult(ok=True, data={"version": doc.version if doc else 0})


def _impl_read_world_doc(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    doc = ctx.sqlite.get_world_doc(ctx.project_id)
    return ToolResult(ok=True, data={"content_md": doc.content_md if doc else ""})


def _impl_create_character(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    cid = uuid.uuid4().hex
    ch = Character(
        id=cid,
        project_id=ctx.project_id,
        name=args.get("name", "未命名"),
        role=args.get("role", "配角"),
        profile_md=args.get("profile_md", ""),
        updated_at=datetime.now(),
    )
    ctx.sqlite.insert_character(ch)
    ctx.file.write_character(
        ctx.project_id,
        cid,
        {
            "id": ch.id,
            "project_id": ch.project_id,
            "name": ch.name,
            "role": ch.role,
            "profile_md": ch.profile_md,
            "updated_at": ch.updated_at.isoformat(),
        },
    )
    return ToolResult(ok=True, data={"id": cid})


def _impl_update_character(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    cid = args.get("id")
    ch = ctx.sqlite.get_character(cid) if cid else None
    if ch is None:
        return ToolResult(ok=False, error="人物不存在")
    ch.name = args.get("name", ch.name)
    ch.role = args.get("role", ch.role)
    ch.profile_md = args.get("profile_md", ch.profile_md)
    ch.updated_at = datetime.now()
    ctx.sqlite.update_character(ch)
    return ToolResult(ok=True, data={"id": cid})


def _impl_list_characters(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    rows = ctx.sqlite.list_characters(ctx.project_id)
    return ToolResult(
        ok=True,
        data=[{"id": c.id, "name": c.name, "role": c.role, "profile_md": c.profile_md} for c in rows],
    )


def _impl_create_outline_node(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    n = OutlineNode(
        id=uuid.uuid4().hex,
        project_id=ctx.project_id,
        parent_id=args.get("parent_id"),
        order=int(args.get("order", 0)),
        title=args.get("title", "未命名"),
        summary_md=args.get("summary_md", ""),
        chapter_id=args.get("chapter_id"),
    )
    ctx.sqlite.insert_outline_node(n)
    return ToolResult(ok=True, data={"id": n.id})


def _impl_update_outline_node(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    nid = args.get("id")
    nodes = ctx.sqlite.list_outline(ctx.project_id)
    target = next((n for n in nodes if n.id == nid), None)
    if target is None:
        return ToolResult(ok=False, error="大纲节点不存在")
    if "parent_id" in args:
        target.parent_id = args["parent_id"]
    if "order" in args:
        target.order = int(args["order"])
    if "title" in args:
        target.title = args["title"]
    if "summary_md" in args:
        target.summary_md = args["summary_md"]
    if "chapter_id" in args:
        target.chapter_id = args["chapter_id"]
    ctx.sqlite.update_outline_node(target)
    return ToolResult(ok=True, data={"id": nid})


def _impl_list_outline(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    rows = ctx.sqlite.list_outline(ctx.project_id)
    return ToolResult(
        ok=True,
        data=[{"id": n.id, "title": n.title, "summary_md": n.summary_md} for n in rows],
    )


def _impl_create_chapter(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    now = datetime.now()
    content = args.get("content_md", "")
    ch = Chapter(
        id=uuid.uuid4().hex,
        project_id=ctx.project_id,
        outline_node_id=args.get("outline_node_id"),
        order=int(args.get("order", 0)),
        title=args.get("title", "未命名"),
        content_md=content,
        word_count=sum(1 for c in content if not c.isspace()),
        status=ChapterStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    ctx.sqlite.insert_chapter(ch)
    ctx.file.write_chapter(ctx.project_id, ch.order, ch.title, content)
    return ToolResult(ok=True, data={"id": ch.id})


def _impl_append_to_chapter(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    chid = args.get("chapter_id")
    delta = args.get("delta", "")
    ch = ctx.sqlite.get_chapter(chid) if chid else None
    if ch is None:
        return ToolResult(ok=False, error="章节不存在")
    ch.content_md += delta
    ch.word_count = sum(1 for c in ch.content_md if not c.isspace())
    ch.status = ChapterStatus.DRAFT_PARTIAL
    ch.updated_at = datetime.now()
    ctx.sqlite.update_chapter(ch)
    return ToolResult(ok=True, data={"id": chid, "word_count": ch.word_count})


def _impl_read_chapter(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    chid = args.get("chapter_id")
    ch = ctx.sqlite.get_chapter(chid) if chid else None
    if ch is None:
        return ToolResult(ok=False, error="章节不存在")
    return ToolResult(ok=True, data={"id": chid, "content_md": ch.content_md})


def _impl_advance_phase(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    from app.core.state_machine import assert_legal_transition

    target_str = args.get("to")
    try:
        target = Phase(target_str)
    except ValueError:
        return ToolResult(ok=False, error=f"未知阶段：{target_str}")
    try:
        assert_legal_transition(ctx.project_phase, target)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))
    ctx.sqlite.update_project_phase(ctx.project_id, target, datetime.now())
    return ToolResult(ok=True, data={"phase": target.value})


def _impl_read_project_summary(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    p = ctx.sqlite.get_project(ctx.project_id)
    proj_ctx: ProjectContext | None = ctx.sqlite.get_project_context(ctx.project_id)
    return ToolResult(
        ok=True,
        data={
            "name": p.name if p else "",
            "logline": p.logline if p else "",
            "genre": p.genre if p else "",
            "current_phase": p.current_phase.value if p else "",
            "rolling_summary": proj_ctx.rolling_summary if proj_ctx else "",
        },
    )


# ---------------- registry ----------------
@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]
    allowed_phases: set[Phase]
    impl: Callable[[ToolContext, dict[str, Any]], ToolResult]


def _schema(props: dict, required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required}


_REGISTRY: list[ToolDef] = [
    ToolDef(
        "upsert_world_doc",
        "整体覆盖世界观 markdown",
        _schema({"content_md": {"type": "string"}}, ["content_md"]),
        {Phase.WORLD},
        _impl_upsert_world_doc,
    ),
    ToolDef(
        "read_world_doc",
        "读取世界观",
        _schema({}, []),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING},
        _impl_read_world_doc,
    ),
    ToolDef(
        "create_character",
        "创建人物卡",
        _schema(
            {
                "name": {"type": "string"},
                "role": {"type": "string"},
                "profile_md": {"type": "string"},
            },
            ["name"],
        ),
        {Phase.CHARACTERS},
        _impl_create_character,
    ),
    ToolDef(
        "update_character",
        "更新人物卡",
        _schema(
            {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "role": {"type": "string"},
                "profile_md": {"type": "string"},
            },
            ["id"],
        ),
        {Phase.CHARACTERS},
        _impl_update_character,
    ),
    ToolDef(
        "list_characters",
        "列人物",
        _schema({}, []),
        {Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING},
        _impl_list_characters,
    ),
    ToolDef(
        "create_outline_node",
        "建大纲节点",
        _schema(
            {
                "parent_id": {"type": ["string", "null"]},
                "order": {"type": "integer"},
                "title": {"type": "string"},
                "summary_md": {"type": "string"},
            },
            ["title"],
        ),
        {Phase.OUTLINE},
        _impl_create_outline_node,
    ),
    ToolDef(
        "update_outline_node",
        "改大纲节点",
        _schema(
            {
                "id": {"type": "string"},
                "parent_id": {"type": ["string", "null"]},
                "order": {"type": "integer"},
                "title": {"type": "string"},
                "summary_md": {"type": "string"},
                "chapter_id": {"type": ["string", "null"]},
            },
            ["id"],
        ),
        {Phase.OUTLINE, Phase.WRITING},
        _impl_update_outline_node,
    ),
    ToolDef(
        "list_outline",
        "列大纲",
        _schema({}, []),
        {Phase.OUTLINE, Phase.WRITING},
        _impl_list_outline,
    ),
    ToolDef(
        "create_chapter",
        "建章节",
        _schema(
            {
                "title": {"type": "string"},
                "order": {"type": "integer"},
                "content_md": {"type": "string"},
                "outline_node_id": {"type": ["string", "null"]},
            },
            ["title", "order"],
        ),
        {Phase.WRITING},
        _impl_create_chapter,
    ),
    ToolDef(
        "append_to_chapter",
        "追加章节正文",
        _schema(
            {"chapter_id": {"type": "string"}, "delta": {"type": "string"}},
            ["chapter_id", "delta"],
        ),
        {Phase.WRITING},
        _impl_append_to_chapter,
    ),
    ToolDef(
        "read_chapter",
        "读章节",
        _schema({"chapter_id": {"type": "string"}}, ["chapter_id"]),
        {Phase.WRITING},
        _impl_read_chapter,
    ),
    ToolDef(
        "advance_phase",
        "切换阶段",
        _schema({"to": {"type": "string"}}, ["to"]),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_advance_phase,
    ),
    ToolDef(
        "read_project_summary",
        "读项目摘要",
        _schema({}, []),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_read_project_summary,
    ),
]


def get_tools_for_phase(phase: Phase) -> list[LLMTool]:
    return [
        LLMTool(name=t.name, description=t.description, parameters=t.parameters)
        for t in _REGISTRY
        if phase in t.allowed_phases
    ]


def get_tool_def(name: str) -> ToolDef | None:
    return next((t for t in _REGISTRY if t.name == name), None)


def execute_tool(
    tool: LLMTool, ctx: ToolContext, args: dict[str, Any]
) -> ToolResult:
    defn = get_tool_def(tool.name)
    if defn is None:
        return ToolResult(ok=False, error=f"未知工具：{tool.name}")
    if ctx.project_phase not in defn.allowed_phases:
        return ToolResult(
            ok=False,
            error=f"工具 {tool.name} 在当前阶段 {ctx.project_phase.value} 不可用",
        )
    if not isinstance(args, dict):
        return ToolResult(ok=False, error="参数必须是对象")
    for k in defn.parameters.get("required", []):
        if k not in args:
            return ToolResult(ok=False, error=f"缺少必填参数：{k}")
    try:
        return defn.impl(ctx, args)
    except Exception as e:  # noqa: BLE001
        return ToolResult(ok=False, error=f"{type(e).__name__}: {e}")
