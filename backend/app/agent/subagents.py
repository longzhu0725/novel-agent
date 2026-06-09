"""Sub-agents：评审 / 风格 / 大纲 三位专家。

MVP 设计：advisory only（只读不写），由主 Coordinator 决定采纳/落库。

双调用方式：
- async：用于外部直接 await（无事件循环上下文时）
- sync：  用于 Agent 工具层（事件循环已运行，asyncio.run() 不可用）
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.llm import LLMClient, LLMMessage
from app.storage.file_repo import FileRepo
from app.storage.models import Chapter, Character, OutlineNode, Project
from app.storage.sqlite_repo import SqliteRepo


# ---------------- System Prompts ----------------

OUTLINE_SYSTEM = """你是一位资深的故事结构顾问，擅长长篇小说的情节架构、伏笔与节奏。
你的任务：根据用户提出的问题，结合我提供的【项目上下文】，给出具体、可操作的建议。
只输出建议正文，不要解释你的方法，不要寒暄。"""

STYLE_SYSTEM = """你是一位资深的文学风格顾问，擅长把控叙事口吻、用词节奏与读者体验。
你的任务：针对用户提交的文本片段，根据项目的【风格说明】，指出问题并给出改写建议。
回复结构：1) 总体评价（一句话）2) 具体问题 3) 改写建议（可直接复用的句子）。
不要复述原文。"""

REVIEWER_SYSTEM = """你是一位严谨的小说评审专家，擅长发现人物弧光断裂、世界观自相矛盾、伏笔未回收、节奏失控等问题。
你的任务：根据【项目上下文】和用户指定的【评审目标】，逐条列出问题与改进建议。
回复结构：1) 总体评价 2) 问题清单（按严重性排序）3) 优先修复建议。
语气直接但专业，不要给赞美铺垫。"""


@dataclass
class ProjectContext:
    """自动从 DB 抓取的最小上下文，传给 sub-agent。"""
    project: Project
    characters: list[Character]
    outline: list[OutlineNode]
    chapters: list[Chapter]
    style_notes: str
    world_md: str

    def to_prompt_block(self) -> str:
        chars = "\n".join(f"- {c.name}（{c.role}）: {c.profile_md[:200]}" for c in self.characters) or "- (无)"
        nodes = "\n".join(f"- [{n.order}] {n.title}: {n.summary_md[:200]}" for n in self.outline) or "- (无)"
        chs = "\n".join(f"- [{c.order}] {c.title} ({c.word_count}字, {c.status}): {c.content_md[:200]}" for c in self.chapters) or "- (无)"
        return (
            f"## 项目：{self.project.name}\n"
            f"类型：{self.project.genre}  风格：{self.style_notes or '（未指定）'}\n"
            f"一句话：{self.project.logline or '（无）'}\n\n"
            f"## 世界观\n{self.world_md or '（暂无）'}\n\n"
            f"## 人物\n{chars}\n\n"
            f"## 大纲\n{nodes}\n\n"
            f"## 章节\n{chs}\n"
        )


def build_project_context(
    project: Project, sq: SqliteRepo, fr: FileRepo
) -> ProjectContext:
    world = sq.get_world_doc(project.id)
    return ProjectContext(
        project=project,
        characters=sq.list_characters(project.id),
        outline=sq.list_outline(project.id),
        chapters=sq.list_chapters(project.id),
        style_notes=project.style_notes,
        world_md=world.content_md if world else "",
    )


# ---------------- Sub-agent 入口 ----------------

@dataclass
class SubAgentResult:
    advisor: str
    advice: str


# ---- 同步 LLM 调用（用于 Agent 工具层，事件循环已运行）----
def _ask_sync(llm: LLMClient, system: str, user_prompt: str) -> str:
    """在已运行的事件循环中同步调用 LLM。"""
    url = f"{llm.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {llm.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": llm.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
    }
    text: list[str] = []
    with httpx.stream("POST", url, json=body, headers=headers, timeout=60.0) as r:
        if r.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {r.status_code}")
        for line in r.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]" or not payload:
                break
            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for choice in chunk.get("choices", []):
                if content := (choice.get("delta") or {}).get("content"):
                    text.append(content)
    out = "".join(text).strip()
    return out or "(无输出)"


# ---- 异步 LLM 调用（保留供外部直接 await）----
async def _ask_async(llm: LLMClient, system: str, user_prompt: str) -> str:
    msgs = [LLMMessage("system", system), LLMMessage("user", user_prompt)]
    out: list[str] = []
    async for ev in llm.stream_chat_events(msgs, tools=[]):
        if ev["type"] == "delta":
            out.append(ev["text"])
    return "".join(out).strip() or "(无输出)"


# ---- sync 版本（供 Agent 工具层使用）----

def consult_outline_expert_sync(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, question: str,
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    user_prompt = f"## 项目上下文\n{ctx.to_prompt_block()}\n\n## 问题\n{question}"
    advice = _ask_sync(llm, OUTLINE_SYSTEM, user_prompt)
    return SubAgentResult(advisor="outline_expert", advice=advice)


def consult_style_expert_sync(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, text: str, focus: str = "",
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    user_prompt = (
        f"## 风格说明\n{ctx.style_notes or '（未指定）'}\n\n"
        f"## 待评审文本\n{text}\n\n"
        f"## 关注点\n{focus or '整体风格与节奏'}"
    )
    advice = _ask_sync(llm, STYLE_SYSTEM, user_prompt)
    return SubAgentResult(advisor="style_expert", advice=advice)


def consult_reviewer_sync(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, target: str, content_id: str = "",
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    focus_text = ""
    if content_id:
        ch = sq.get_chapter(content_id)
        if ch:
            focus_text = f"\n## 评审对象（章节 {ch.title}）\n{ch.content_md}\n"
    user_prompt = (
        f"## 项目上下文\n{ctx.to_prompt_block()}"
        f"{focus_text}\n## 评审目标\n{target}"
    )
    advice = _ask_sync(llm, REVIEWER_SYSTEM, user_prompt)
    return SubAgentResult(advisor="reviewer", advice=advice)


# ---- async 版本（保留供外部直接 await）----

async def consult_outline_expert(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, question: str,
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    user_prompt = f"## 项目上下文\n{ctx.to_prompt_block()}\n\n## 问题\n{question}"
    advice = await _ask_async(llm, OUTLINE_SYSTEM, user_prompt)
    return SubAgentResult(advisor="outline_expert", advice=advice)


async def consult_style_expert(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, text: str, focus: str = "",
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    user_prompt = (
        f"## 风格说明\n{ctx.style_notes or '（未指定）'}\n\n"
        f"## 待评审文本\n{text}\n\n"
        f"## 关注点\n{focus or '整体风格与节奏'}"
    )
    advice = await _ask_async(llm, STYLE_SYSTEM, user_prompt)
    return SubAgentResult(advisor="style_expert", advice=advice)


async def consult_reviewer(
    *, llm: LLMClient, sq: SqliteRepo, fr: FileRepo,
    project: Project, target: str, content_id: str = "",
) -> SubAgentResult:
    ctx = build_project_context(project, sq, fr)
    focus_text = ""
    if content_id:
        ch = sq.get_chapter(content_id)
        if ch:
            focus_text = f"\n## 评审对象（章节 {ch.title}）\n{ch.content_md}\n"
    user_prompt = (
        f"## 项目上下文\n{ctx.to_prompt_block()}"
        f"{focus_text}\n## 评审目标\n{target}"
    )
    advice = await _ask_async(llm, REVIEWER_SYSTEM, user_prompt)
    return SubAgentResult(advisor="reviewer", advice=advice)
