"""FastAPI 依赖注入。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.storage.file_repo import FileRepo
from app.storage.sqlite_repo import SqliteRepo


@lru_cache(maxsize=1)
def get_sqlite_repo() -> SqliteRepo:
    settings = get_settings()
    path = Path(settings.data_dir) / "novel.db"
    r = SqliteRepo(path)
    r.init_schema()
    return r


@lru_cache(maxsize=1)
def get_file_repo() -> FileRepo:
    settings = get_settings()
    return FileRepo(Path(settings.data_dir) / "projects")
