"""文件系统仓储。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class FileRepo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create_project(self, pid: str) -> Path:
        d = self.root / pid
        d.mkdir(parents=True, exist_ok=False)
        (d / "chapters").mkdir()
        (d / "characters").mkdir()
        (d / "world.md").write_text("", encoding="utf-8")
        return d

    def delete_project(self, pid: str) -> None:
        d = self.root / pid
        if d.exists():
            shutil.rmtree(d)

    def project_dir(self, pid: str) -> Path:
        return self.root / pid

    def read_world(self, pid: str) -> str:
        return (self.root / pid / "world.md").read_text(encoding="utf-8")

    def write_world(self, pid: str, content: str) -> None:
        (self.root / pid / "world.md").write_text(content, encoding="utf-8")

    def write_chapter(self, pid: str, order: int, title: str, content: str) -> Path:
        safe = _safe(title) or "untitled"
        p = self.root / pid / "chapters" / f"{order:04d}_{safe}.md"
        p.write_text(content, encoding="utf-8")
        return p

    def write_character(self, pid: str, cid: str, data: dict[str, Any]) -> Path:
        p = self.root / pid / "characters" / f"{cid}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p


def _safe(s: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    return "".join("_" if c in bad else c for c in s).strip()
