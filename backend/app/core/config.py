"""应用配置，从环境变量加载。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。所有字段从环境变量读取。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    llm_base_url: str
    llm_api_key: SecretStr
    llm_model: str

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    data_dir: Path = Path("./data")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局单例 Settings。"""
    return Settings()  # type: ignore[call-arg]
