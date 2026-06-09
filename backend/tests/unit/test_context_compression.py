"""上下文压缩单元测试。"""
from __future__ import annotations

import pytest

from app.core.compression import (
    CompressionResult,
    compress_messages,
    should_compress,
    total_tokens,
)
from app.core.llm import LLMMessage


class FakeSummarizer:
    def __init__(self, out: str) -> None:
        self.out = out

    async def summarize(self, text: str) -> str:
        return self.out


def test_total_tokens_approximates_chars():
    msgs = [LLMMessage("user", "abc"), LLMMessage("assistant", "")]
    assert total_tokens(msgs) > 100  # 2*50 + 3 + 1


def test_should_compress_triggers_above_threshold():
    # 巨大消息 + 小窗口
    big = LLMMessage("user", "x" * 1000)
    assert should_compress([big] * 5, model_window=100, threshold=0.8) is True


def test_should_compress_skips_below_threshold():
    msgs = [LLMMessage("user", "hi")]
    assert should_compress(msgs, model_window=100_000) is False


@pytest.mark.asyncio
async def test_compress_keeps_tail_and_appends_summary():
    msgs = [LLMMessage(role="user", content=f"msg{i}") for i in range(10)]
    result = await compress_messages(
        msgs, llm=FakeSummarizer("【新摘要】"), existing_summary="", keep_ratio=0.7
    )
    assert isinstance(result, CompressionResult)
    # 保留 30% 尾部
    assert len(result.tail) >= 3
    assert "【新摘要】" in result.summary


@pytest.mark.asyncio
async def test_compress_concatenates_existing_summary():
    msgs = [LLMMessage("user", "x" * 1000)] * 5
    result = await compress_messages(
        msgs, llm=FakeSummarizer("B"), existing_summary="A", keep_ratio=0.5
    )
    assert result.summary.startswith("A")
    assert "B" in result.summary
