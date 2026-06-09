"""错误码与信封测试。"""
from app.core.errors import ErrorCode, ProtocolError, error_envelope


def test_protocol_error_has_code_and_message() -> None:
    err = ProtocolError(ErrorCode.TOOL_EXEC_FAILED, "写盘失败")
    assert err.code == ErrorCode.TOOL_EXEC_FAILED
    assert err.message == "写盘失败"
    assert err.recoverable is True  # 默认可恢复


def test_protocol_error_can_be_non_recoverable() -> None:
    err = ProtocolError(ErrorCode.UNAUTHORIZED, "key 错", recoverable=False)
    assert err.recoverable is False


def test_error_envelope_serializes() -> None:
    env = error_envelope(
        correlation_id="abc-123",
        code=ErrorCode.LLM_TIMEOUT,
        message="timeout",
        recoverable=True,
    )
    assert env["type"] == "error"
    assert env["correlation_id"] == "abc-123"
    assert env["code"] == "LLM_TIMEOUT"
    assert env["message"] == "timeout"
    assert env["recoverable"] is True
