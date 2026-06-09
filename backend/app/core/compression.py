"""上下文压缩。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.llm import LLMMessage


@dataclass
class CompressionResult:
    summary: str
    tail: list[LLMMessage]


class Summarizer(Protocol):
    async def summarize(self, text: str) -> str: ...


def _approx_tokens(s: str) -> int:
    return max(1, len(s))


def total_tokens(messages: list[LLMMessage]) -> int:
    return sum(_approx_tokens(m.content or "") for m in messages) + 50 * len(messages)


def should_compress(
    messages: list[LLMMessage], *, model_window: int, threshold: float = 0.8
) -> bool:
    return total_tokens(messages) >= int(model_window * threshold)


async def compress_messages(
    messages: list[LLMMessage],
    *,
    llm: Summarizer,
    existing_summary: str,
    keep_ratio: float = 0.7,
) -> CompressionResult:
    if not messages:
        return CompressionResult(summary=existing_summary, tail=[])
    cut = max(1, int(len(messages) * (1 - keep_ratio)))
    head, tail = messages[:cut], messages[cut:]
    text = "\n".join(f"[{m.role}] {m.content or ''}" for m in head)
    new = await llm.summarize(text)
    summary = (existing_summary + "\n" + new).strip() if existing_summary else new
    return CompressionResult(summary=summary, tail=tail)
