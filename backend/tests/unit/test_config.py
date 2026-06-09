"""配置加载测试。"""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """从环境变量加载必填字段。"""
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", "/tmp/novel")
    s = Settings()
    assert s.llm_base_url == "https://example.com/v1"
    assert s.llm_api_key.get_secret_value() == "sk-test"
    assert s.llm_model == "gpt-4o"
    assert str(s.data_dir) == "/tmp/novel"


def test_settings_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """缺必填字段时抛错。"""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "https://x")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", "/tmp")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
