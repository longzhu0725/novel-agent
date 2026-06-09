"""OpenAI 兼容 LLM 客户端（流式）。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol

import httpx

from app.core.errors import ErrorCode, ProtocolError


@dataclass
class LLMMessage:
    role: str
    content: str | None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class LLMTool:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


class Transport(Protocol):
    def stream(self, url: str, headers: dict[str, str], body: dict[str, Any]) -> AsyncIterator[dict[str, Any]]: ...


class HttpxTransport:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0))
        return self._client

    async def stream(
        self, url: str, headers: dict[str, str], body: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        client = await self._get()
        async with client.stream("POST", url, json=body, headers=headers) as r:
            if r.status_code in (401, 403):
                raise ProtocolError(ErrorCode.UNAUTHORIZED, "LLM 鉴权失败", recoverable=False)
            if r.status_code == 429:
                raise ProtocolError(ErrorCode.LLM_RATE_LIMIT, "LLM 限流")
            if r.status_code >= 500:
                raise ProtocolError(ErrorCode.LLM_TIMEOUT, f"LLM {r.status_code}")
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    yield json.loads(payload)
                except json.JSONDecodeError as e:
                    raise ProtocolError(ErrorCode.LLM_BAD_RESPONSE, "非 JSON SSE 行") from e


def _to_msg(m: LLMMessage) -> dict[str, Any]:
    out: dict[str, Any] = {"role": m.role}
    if m.content is not None:
        out["content"] = m.content
    if m.tool_calls:
        out["tool_calls"] = m.tool_calls
    if m.tool_call_id:
        out["tool_call_id"] = m.tool_call_id
    if m.name:
        out["name"] = m.name
    return out


def _to_tool(t: LLMTool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
        },
    }


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, _transport: Transport | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._transport: Transport = _transport or HttpxTransport()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _body(self, msgs: list[LLMMessage], tools: list[LLMTool], stream: bool) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [_to_msg(m) for m in msgs],
            "tools": [_to_tool(t) for t in tools] if tools else None,
            "stream": stream,
        }

    async def stream_chat_events(
        self, messages: list[LLMMessage], tools: list[LLMTool]
    ) -> AsyncIterator[dict[str, Any]]:
        body = self._body(messages, tools, stream=True)
        url = f"{self.base_url}/chat/completions"
        current_tool: dict[str, Any] | None = None
        current_args = ""
        async for chunk in self._transport.stream(url, self._headers(), body):
            choices = chunk.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            delta = choice.get("delta") or {}
            if content := delta.get("content"):
                yield {"type": "delta", "text": content}
            if tc := delta.get("tool_calls"):
                item = tc[0]
                if item.get("id"):
                    if current_tool is not None:
                        try:
                            current_tool["arguments"] = json.loads(current_args or "{}")
                        except json.JSONDecodeError:
                            current_tool["arguments"] = {}
                        yield {"type": "tool_call", **current_tool}
                    current_tool = {
                        "id": item["id"],
                        "name": (item.get("function") or {}).get("name"),
                    }
                    current_args = (item.get("function") or {}).get("arguments") or ""
                else:
                    current_args += (item.get("function") or {}).get("arguments") or ""
            if choice.get("finish_reason") and current_tool is not None:
                try:
                    current_tool["arguments"] = json.loads(current_args or "{}")
                except json.JSONDecodeError:
                    current_tool["arguments"] = {}
                yield {"type": "tool_call", **current_tool}
                current_tool = None
                current_args = ""
        if current_tool is not None:
            try:
                current_tool["arguments"] = json.loads(current_args or "{}")
            except json.JSONDecodeError:
                current_tool["arguments"] = {}
            yield {"type": "tool_call", **current_tool}
        yield {"type": "done"}
