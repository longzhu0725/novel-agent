"""协议错误码与 WS 错误信封。"""
from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """协议级错误码。前端按 code 决定 UI 表现。"""

    UNAUTHORIZED = "UNAUTHORIZED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_CONTEXT_TOO_LONG = "LLM_CONTEXT_TOO_LONG"
    LLM_BAD_RESPONSE = "LLM_BAD_RESPONSE"
    TOOL_VALIDATION_FAILED = "TOOL_VALIDATION_FAILED"
    TOOL_EXEC_FAILED = "TOOL_EXEC_FAILED"
    STATE_ILLEGAL_TRANSITION = "STATE_ILLEGAL_TRANSITION"
    STORAGE_CONFLICT = "STORAGE_CONFLICT"
    INTERNAL = "INTERNAL"


class ProtocolError(Exception):
    """协议层错误。"""

    def __init__(self, code: ErrorCode, message: str, recoverable: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable


def error_envelope(
    correlation_id: str,
    code: ErrorCode,
    message: str,
    recoverable: bool,
) -> dict[str, Any]:
    """构造 WS 错误消息。"""
    return {
        "type": "error",
        "correlation_id": correlation_id,
        "code": code.value,
        "message": message,
        "recoverable": recoverable,
    }
