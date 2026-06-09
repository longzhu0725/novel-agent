"""系统提示模板（按阶段）。"""
from __future__ import annotations

from typing import Iterable

from app.core.state_machine import Phase
from app.storage.models import Project


_PHASE_HINT = {
    Phase.INIT: "你正在与作者初次交流，了解他想写什么。",
    Phase.WORLD: "请协助作者搭建世界观：地理、势力、规则、历史。",
    Phase.CHARACTERS: "请协助作者设计人物卡：姓名、身份、动机、关系。",
    Phase.OUTLINE: "请协助作者搭建大纲：分卷→分章→节点摘要。",
    Phase.WRITING: (
        "请按大纲撰写章节正文，保持风格一致。"
        "**撰写新章节时**：先调用 begin_chapter(title, order, [outline_node_id]) 创建空章节并拿到 chapter_id，"
        "之后你输出的每个文本 delta 会被系统自动追加到该章节（边写边落库）。"
        "**写完后**：调用 finalize_chapter(chapter_id) 标记完成。"
        "**不要**用 create_chapter 一次性塞入完整正文。"
    ),
    Phase.DONE: "项目已完成，可以协助润色或回顾。",
}


def build_system_prompt(
    project: Project,
    phase: Phase,
    *,
    rolling_summary: str = "",
    tool_names: Iterable[str] = (),
) -> str:
    tool_list = "\n".join(f"- {n}" for n in tool_names) or "- (无)"
    parts = [
        f"你是一位专业的小说创作助手。项目名：{project.name}",
        f"类型：{project.genre or '未指定'}  风格：{project.style_notes or '未指定'}",
        f"一句话简介：{project.logline or '（暂无）'}",
        f"当前阶段：{phase.value}",
        _PHASE_HINT.get(phase, ""),
        f"可调用工具：\n{tool_list}",
        "工具调用：发出 tool_call 后等待 tool_result 反馈再继续。",
        "请用中文，保持简洁、具体。",
    ]
    if rolling_summary:
        parts.append(f"跨会话摘要：{rolling_summary}")
    return "\n\n".join(parts)
