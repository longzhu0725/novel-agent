"""LLMClient 单元测试。"""
from __future__ import annotations

from typing import Any

import pytest

from app.core.llm import LLMClient, LLMMessage


class FakeTransport:
    def __init__(self, seq: list[list[dict[str, Any]]]) -> None:
        self.seq = list(seq)
        self.calls: list[dict[str, Any]] = []

    async def stream(self, url, headers, body):
        self.calls.append(body)
        chunks = self.seq.pop(0) if self.seq else []
        for c in chunks:
            yield c


@pytest.fixture
def make():
    def _make(seq: list[list[dict[str, Any]]]) -> tuple[LLMClient, FakeTransport]:
        t = FakeTransport(seq)
        c = LLMClient("https://x", "sk", "gpt-4o", _transport=t)
        return c, t

    return _make


@pytest.mark.asyncio
async def test_text_delta(make):
    c, _ = make([[{"choices": [{"delta": {"content": "你好"}}]}]])
    out: list[str] = []
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        if ev["type"] == "delta":
            out.append(ev["text"])
    assert "你好" in out


@pytest.mark.asyncio
async def test_tool_call_emitted(make):
    seq = [
        [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "id": "c1",
                                    "function": {
                                        "name": "create_character",
                                        "arguments": '{"name":"林夕"}',
                                    },
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            }
        ]
    ]
    c, _ = make(seq)
    tc = None
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        if ev["type"] == "tool_call":
            tc = ev
    assert tc is not None
    assert tc["name"] == "create_character"
    assert tc["arguments"] == {"name": "林夕"}


@pytest.mark.asyncio
async def test_done_yielded_at_end(make):
    c, _ = make([[{"choices": [{"delta": {"content": "ok"}}]}]])
    types: list[str] = []
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        types.append(ev["type"])
    assert types[-1] == "done"


@pytest.mark.asyncio
async def test_tool_args_streamed_then_finalized(make):
    # 模拟 tool_call 跨多个 chunk 累积参数
    seq = [
        [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "id": "c1",
                                    "function": {
                                        "name": "create_character",
                                        "arguments": '{"name":',
                                    },
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "function": {"arguments": '"林夕"}'},
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "delta": {},
                        "finish_reason": "tool_calls",
                    }
                ]
            },
        ]
    ]
    c, _ = make(seq)
    tc = None
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        if ev["type"] == "tool_call":
            tc = ev
    assert tc is not None and tc["arguments"] == {"name": "林夕"}
