"""Agent 工具：按阶段授权 + JSON Schema。"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from app.core.llm import LLMClient, LLMTool
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
    llm: LLMClient | None = None  # 供 consult_* sub-agent 使用


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
    return ToolResult(ok=True, data={"id": ch.id, "stream": False})


def _impl_begin_chapter(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """创建空章节（流式追加模式）。Agent 拿到 id 后，每个 delta 会自动 append。"""
    now = datetime.now()
    title = args.get("title", "未命名")
    ch = Chapter(
        id=uuid.uuid4().hex,
        project_id=ctx.project_id,
        outline_node_id=args.get("outline_node_id"),
        order=int(args.get("order", 0)),
        title=title,
        content_md="",
        word_count=0,
        status=ChapterStatus.DRAFT_PARTIAL,
        created_at=now,
        updated_at=now,
    )
    ctx.sqlite.insert_chapter(ch)
    ctx.file.write_chapter(ctx.project_id, ch.order, title, "")
    return ToolResult(
        ok=True,
        data={"id": ch.id, "stream": True, "hint": "后续你的每个 delta 都会自动追加到该章节"},
    )


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
    # 同步落盘
    ctx.file.write_chapter(ctx.project_id, ch.order, ch.title, ch.content_md)
    return ToolResult(ok=True, data={"id": chid, "word_count": ch.word_count})


def _impl_finalize_chapter(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """把章节状态从 DRAFT_PARTIAL 切回 DRAFT（流式完成）。"""
    chid = args.get("chapter_id")
    ch = ctx.sqlite.get_chapter(chid) if chid else None
    if ch is None:
        return ToolResult(ok=False, error="章节不存在")
    ch.status = ChapterStatus.DRAFT
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


# ---- sub-agent consult tools (advisory only) ----
def _impl_consult_outline_expert(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    if ctx.llm is None:
        return ToolResult(ok=False, error="LLM 不可用，无法咨询专家")
    from app.agent.subagents import consult_outline_expert_sync

    p = ctx.sqlite.get_project(ctx.project_id)
    if p is None:
        return ToolResult(ok=False, error="项目不存在")
    question = args.get("question", "")
    if not question:
        return ToolResult(ok=False, error="缺少必填参数：question")
    result = consult_outline_expert_sync(
        llm=ctx.llm, sq=ctx.sqlite, fr=ctx.file,
        project=p, question=question,
    )
    return ToolResult(ok=True, data={"advisor": result.advisor, "advice": result.advice})


def _impl_consult_style_expert(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    if ctx.llm is None:
        return ToolResult(ok=False, error="LLM 不可用，无法咨询专家")
    from app.agent.subagents import consult_style_expert_sync

    p = ctx.sqlite.get_project(ctx.project_id)
    if p is None:
        return ToolResult(ok=False, error="项目不存在")
    text = args.get("text", "")
    if not text:
        return ToolResult(ok=False, error="缺少必填参数：text")
    result = consult_style_expert_sync(
        llm=ctx.llm, sq=ctx.sqlite, fr=ctx.file,
        project=p, text=text, focus=args.get("focus", ""),
    )
    return ToolResult(ok=True, data={"advisor": result.advisor, "advice": result.advice})


def _impl_consult_reviewer(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    if ctx.llm is None:
        return ToolResult(ok=False, error="LLM 不可用，无法咨询专家")
    from app.agent.subagents import consult_reviewer_sync

    p = ctx.sqlite.get_project(ctx.project_id)
    if p is None:
        return ToolResult(ok=False, error="项目不存在")
    target = args.get("target", "")
    if not target:
        return ToolResult(ok=False, error="缺少必填参数：target")
    result = consult_reviewer_sync(
        llm=ctx.llm, sq=ctx.sqlite, fr=ctx.file,
        project=p, target=target, content_id=args.get("content_id", ""),
    )
    return ToolResult(ok=True, data={"advisor": result.advisor, "advice": result.advice})


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
        "建章节（一次性写入全部正文）。如需边写边落库，请改用 begin_chapter。",
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
        "begin_chapter",
        "建空章节并进入流式追加模式：拿到 chapter_id 后，你的每个文本 delta 都会自动追加到该章节（带 DRAFT_PARTIAL 状态），最后调用 finalize_chapter 标记完成。",
        _schema(
            {
                "title": {"type": "string"},
                "order": {"type": "integer"},
                "outline_node_id": {"type": ["string", "null"]},
            },
            ["title", "order"],
        ),
        {Phase.WRITING},
        _impl_begin_chapter,
    ),
    ToolDef(
        "append_to_chapter",
        "显式追加章节正文（通常由系统自动处理，不需调用）",
        _schema(
            {"chapter_id": {"type": "string"}, "delta": {"type": "string"}},
            ["chapter_id", "delta"],
        ),
        {Phase.WRITING},
        _impl_append_to_chapter,
    ),
    ToolDef(
        "finalize_chapter",
        "流式追加完成后，调用此工具把章节状态从 DRAFT_PARTIAL 切回 DRAFT。",
        _schema({"chapter_id": {"type": "string"}}, ["chapter_id"]),
        {Phase.WRITING},
        _impl_finalize_chapter,
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
    ToolDef(
        "consult_outline_expert",
        "咨询大纲专家（advisory only）：根据项目当前的大纲/人物/章节，针对你提出的问题给出情节结构、伏笔、节奏方面的建议。",
        _schema(
            {"question": {"type": "string", "description": "你想问的具体问题"}},
            ["question"],
        ),
        {Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_consult_outline_expert,
    ),
    ToolDef(
        "consult_style_expert",
        "咨询风格专家（advisory only）：针对一段正文，结合项目的风格说明，给出口吻/节奏/用词的改进建议与可复用改写。",
        _schema(
            {
                "text": {"type": "string", "description": "要评审的正文片段"},
                "focus": {"type": "string", "description": "想重点关注的方面，可选"},
            },
            ["text"],
        ),
        {Phase.WRITING, Phase.DONE},
        _impl_consult_style_expert,
    ),
    ToolDef(
        "consult_reviewer",
        "咨询评审专家（advisory only）：针对你指定的目标（人物一致性/世界观自洽/伏笔/节奏等），逐条列出问题与改进建议。",
        _schema(
            {
                "target": {"type": "string", "description": "评审目标，如'检查林夕的动机是否一致'"},
                "content_id": {"type": "string", "description": "指定章节 id，可选"},
            },
            ["target"],
        ),
        {Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_consult_reviewer,
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
