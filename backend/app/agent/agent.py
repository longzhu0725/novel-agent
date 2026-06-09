"""Agent 主循环。"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from app.agent.prompts import build_system_prompt
from app.agent.tools import ToolContext, execute_tool, get_tools_for_phase
from app.core.compression import compress_messages, should_compress
from app.core.llm import LLMClient, LLMMessage
from app.storage.file_repo import FileRepo
from app.storage.models import ChapterStatus, ChatMessage, ProjectContext
from app.storage.sqlite_repo import SqliteRepo


MAX_TOOL_ROUNDS = 10
DEFAULT_MODEL_WINDOW = 100_000
COMPRESS_THRESHOLD = 0.8
KEEP_RATIO = 0.7
HISTORY_LIMIT = 8


AgentEvent = dict[str, Any]


class Agent:
    def __init__(
        self,
        llm: LLMClient,
        sqlite: SqliteRepo,
        file: FileRepo,
        *,
        model_window: int = DEFAULT_MODEL_WINDOW,
    ) -> None:
        self.llm = llm
        self.sqlite = sqlite
        self.file = file
        self.model_window = model_window

    def _append_delta(self, project_id: str, chapter_id: str, delta: str) -> None:
        """流式追加一段正文到章节（DB + 文件）。"""
        if not delta:
            return
        ch = self.sqlite.get_chapter(chapter_id)
        if ch is None or ch.project_id != project_id:
            return
        ch.content_md += delta
        ch.word_count = sum(1 for c in ch.content_md if not c.isspace())
        ch.status = ChapterStatus.DRAFT_PARTIAL
        ch.updated_at = datetime.now()
        self.sqlite.update_chapter(ch)
        self.file.write_chapter(project_id, ch.order, ch.title, ch.content_md)

    def _build_context(
        self,
        project,
        phase,
        history: list[ChatMessage],
        user_text: str,
        summary: str,
    ) -> list[LLMMessage]:
        tool_names = [t.name for t in get_tools_for_phase(phase)]
        sys = build_system_prompt(
            project, phase, rolling_summary=summary, tool_names=tool_names
        )
        msgs: list[LLMMessage] = [LLMMessage(role="system", content=sys)]
        for m in history:
            msgs.append(LLMMessage(role=m.role, content=m.content))
        msgs.append(LLMMessage(role="user", content=user_text))
        return msgs

    async def _maybe_compress(
        self,
        project_id: str,
        phase,
        messages: list[LLMMessage],
        summary: str,
    ) -> tuple[list[LLMMessage], str]:
        if not should_compress(
            messages, model_window=self.model_window, threshold=COMPRESS_THRESHOLD
        ):
            return messages, summary

        class _OneShot:
            def __init__(self, llm: LLMClient, sys_text: str) -> None:
                self.llm = llm
                self.sys = sys_text

            async def summarize(self, text: str) -> str:
                msgs = [
                    LLMMessage("system", self.sys),
                    LLMMessage(
                        "user", "请把以下对话压缩为 500 字以内摘要：\n" + text
                    ),
                ]
                out: list[str] = []
                async for ev in self.llm.stream_chat_events(msgs, tools=[]):
                    if ev["type"] == "delta":
                        out.append(ev["text"])
                return "".join(out)[:2000]

        sys_c = (
            (messages[0].content or "")
            if messages and messages[0].role == "system"
            else ""
        )
        result = await compress_messages(
            messages,
            llm=_OneShot(self.llm, sys_c),  # type: ignore[arg-type]
            existing_summary=summary,
            keep_ratio=KEEP_RATIO,
        )
        new_sys = sys_c + ("\n跨会话摘要：" + result.summary if result.summary else "")
        new_messages = [LLMMessage("system", new_sys)] + result.tail
        ctx = self.sqlite.get_project_context(project_id) or ProjectContext(
            project_id=project_id
        )
        ctx.phase = phase
        ctx.rolling_summary = result.summary
        ctx.last_active_at = datetime.now()
        self.sqlite.upsert_project_context(ctx)
        return new_messages, result.summary

    async def handle(
        self,
        ctx: ToolContext,
        user_text: str,
        *,
        session_id: str = "default",
    ) -> AsyncIterator[AgentEvent]:
        project = self.sqlite.get_project(ctx.project_id)
        if project is None:
            yield {"type": "error", "code": "INTERNAL", "message": "项目不存在"}
            return
        phase = ctx.project_phase
        history = self.sqlite.list_chat_messages(
            ctx.project_id, session_id, limit=HISTORY_LIMIT
        )
        history.reverse()
        proj_ctx = self.sqlite.get_project_context(ctx.project_id)
        summary = proj_ctx.rolling_summary if proj_ctx else ""
        messages = self._build_context(project, phase, history, user_text, summary)

        # 持久化用户消息
        self.sqlite.insert_chat_message(
            ChatMessage(
                id=uuid.uuid4().hex,
                session_id=session_id,
                project_id=ctx.project_id,
                role="user",
                content=user_text,
                created_at=datetime.now(),
            )
        )
        messages, _ = await self._maybe_compress(ctx.project_id, phase, messages, summary)

        llm_tools = get_tools_for_phase(phase)
        # 流式追加模式：begin_chapter 后每个 delta 自动 append
        streaming_chapter_id: str | None = None
        for _ in range(MAX_TOOL_ROUNDS):
            text_parts: list[str] = []
            tool_evt: dict[str, Any] | None = None
            try:
                async for ev in self.llm.stream_chat_events(messages, tools=llm_tools):
                    if ev["type"] == "delta":
                        text_parts.append(ev["text"])
                        # 流式追加到章节
                        if streaming_chapter_id is not None:
                            self._append_delta(
                                ctx.project_id, streaming_chapter_id, ev["text"]
                            )
                        yield {"type": "delta", "text": ev["text"]}
                    elif ev["type"] == "tool_call":
                        tool_evt = ev
                        yield {
                            "type": "tool_call",
                            "id": ev["id"],
                            "name": ev["name"],
                            "args": ev["arguments"],
                        }
            except Exception as e:  # noqa: BLE001
                yield {
                    "type": "error",
                    "code": "LLM_TIMEOUT",
                    "message": f"{type(e).__name__}: {e}",
                }
                return
            # 持久化助手消息
            self.sqlite.insert_chat_message(
                ChatMessage(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    project_id=ctx.project_id,
                    role="assistant",
                    content="".join(text_parts),
                    tool_calls_json=json.dumps(
                        [tool_evt] if tool_evt else [], ensure_ascii=False
                    ),
                    created_at=datetime.now(),
                )
            )
            if tool_evt is None:
                break
            from app.core.llm import LLMTool

            # 注入 LLM 让 consult_* 工具可用
            ctx.llm = self.llm
            result = execute_tool(
                LLMTool(name=tool_evt["name"], description="", parameters={}),
                ctx,
                tool_evt["arguments"],
            )
            payload = {"ok": result.ok, "data": result.data, "error": result.error}
            # 跟踪流式章节
            if result.ok and isinstance(result.data, dict):
                if tool_evt["name"] == "begin_chapter" and result.data.get("stream"):
                    streaming_chapter_id = result.data["id"]
                elif tool_evt["name"] == "finalize_chapter" and streaming_chapter_id == (
                    result.data or {}
                ).get("id"):
                    streaming_chapter_id = None
                    # 章节已完成，结束本轮循环
                    yield {"type": "tool_result", "id": tool_evt["id"], "result": payload}
                    break
            yield {"type": "tool_result", "id": tool_evt["id"], "result": payload}
            messages.append(
                LLMMessage(
                    role="tool",
                    content=json.dumps(payload, ensure_ascii=False),
                    tool_call_id=tool_evt["id"],
                    name=tool_evt["name"],
                )
            )
        yield {"type": "done"}
