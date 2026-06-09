"""真实 LLM 端到端冒烟：跑通流式章节 + 顾问 API。"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.agent import Agent
from app.agent.tools import ToolContext
from app.agent.subagents import (
    consult_outline_expert,
    consult_style_expert,
    consult_reviewer,
)
from app.core.config import get_settings
from app.core.llm import LLMClient
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo


def _setup() -> tuple[SqliteRepo, FileRepo, Project, LLMClient]:
    s = get_settings()
    data = Path(s.data_dir)
    data.mkdir(parents=True, exist_ok=True)
    sq = SqliteRepo(str(data / "novel.db"))
    sq.init_schema()
    fr = FileRepo(data / "projects")
    llm = LLMClient(
        base_url=s.llm_base_url,
        api_key=s.llm_api_key.get_secret_value(),
        model=s.llm_model,
    )
    pid = "smoke-" + datetime.now().strftime("%H%M%S")
    p = Project(
        id=pid,
        name="冒烟测试",
        logline="一个少年在废弃的矿山中醒来，发现自己失去了名字与过去。",
        genre="玄幻",
        style_notes="短句、画面感强、留白多。",
        current_phase=Phase.WRITING,
        storage_dir=pid,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    sq.insert_project(p)
    fr.create_project(pid)
    return sq, fr, p, llm


async def _run_streaming_chapter(
    sq: SqliteRepo, fr: FileRepo, p: Project, llm: LLMClient
) -> None:
    print("\n=== 流式章节：让 LLM 调用 begin_chapter + 写正文 + finalize_chapter ===")
    ctx = ToolContext(project_id=p.id, sqlite=sq, file=fr, project_phase=Phase.WRITING)
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    prompt = (
        "请开始写第一章。要求：1) 先调用 begin_chapter 工具，title=「第一章 醒矿」, order=1；"
        "2) 然后用中文写出约 150 字的正文（直接输出正文即可，不要再调用其它工具）；"
        "3) 写完后再调用 finalize_chapter 工具结束。"
    )
    delta_text: list[str] = []
    chapter_id: str | None = None
    finalized = False
    last_tool_name: str | None = None
    async for ev in agent.handle(ctx, prompt):
        t = ev.get("type")
        if t == "delta":
            delta_text.append(ev["text"])
        elif t == "tool_call":
            last_tool_name = ev["name"]
            print(f"  tool_call: {ev['name']}({json.dumps(ev['args'], ensure_ascii=False)})")
        elif t == "tool_result":
            d = ev["result"].get("data") or {}
            if d.get("id"):
                chapter_id = d["id"]
            print(f"  tool_result: ok={ev['result']['ok']} name={last_tool_name} data={json.dumps(d, ensure_ascii=False)[:80]}")
            if last_tool_name == "finalize_chapter" and ev["result"].get("ok"):
                finalized = True
    body = "".join(delta_text)
    print(f"  delta 长度: {len(body)} 字  finalized={finalized}")
    if chapter_id and finalized:
        ch = sq.get_chapter(chapter_id)
        print(f"  DB 章节: id={ch.id} title={ch.title} status={ch.status.value} 字数={ch.word_count}")
        fpath = fr.project_dir(p.id) / "chapters" / f"{ch.order:04d}_{ch.title}.md"
        print(f"  文件: {fpath} exists={fpath.is_file()}")
        assert ch.content_md == body, "DB 内容与 delta 文本不一致"
        assert fpath.read_text(encoding="utf-8") == body
        assert ch.status.value == "draft"
        print("  ✓ 流式章节落库校验通过")


async def _run_advisor(sq: SqliteRepo, fr: FileRepo, p: Project, llm: LLMClient) -> None:
    print("\n=== 顾问 sub-agent：让 3 个专家都跑一遍 ===")
    r1 = await consult_outline_expert(
        llm=llm, sq=sq, fr=fr, project=p, question="在前 3 章如何埋伏笔？"
    )
    print(f"  outline: {r1.advice[:120]}…")
    r2 = await consult_style_expert(
        llm=llm, sq=sq, fr=fr, project=p,
        text="夜色压山。剑鸣。少年睁眼。", focus="节奏",
    )
    print(f"  style: {r2.advice[:120]}…")
    r3 = await consult_reviewer(
        llm=llm, sq=sq, fr=fr, project=p, target="检查少年人设是否一致"
    )
    print(f"  reviewer: {r3.advice[:120]}…")
    assert r1.advisor == "outline_expert"
    assert r2.advisor == "style_expert"
    assert r3.advisor == "reviewer"
    print("  ✓ 三个 sub-agent 全部跑通")


async def main() -> None:
    sq, fr, p, llm = _setup()
    try:
        await _run_streaming_chapter(sq, fr, p, llm)
        await _run_advisor(sq, fr, p, llm)
    finally:
        # 清理：smoke 项目不入库

        # 不删除数据库，只把测试项目文件删了
        import shutil

        if fr.project_dir(p.id).exists():
            shutil.rmtree(fr.project_dir(p.id))
        print(f"\n清理 smoke 项目：{p.id}")


if __name__ == "__main__":
    asyncio.run(main())
