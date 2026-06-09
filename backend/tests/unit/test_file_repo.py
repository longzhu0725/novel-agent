"""FileRepo 单元测试。"""
from __future__ import annotations

import json

from app.storage.file_repo import FileRepo


def test_create_project_dir(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    assert (tmp_path / "p1").is_dir()
    assert (tmp_path / "p1" / "chapters").is_dir()
    assert (tmp_path / "p1" / "characters").is_dir()
    assert (tmp_path / "p1" / "world.md").is_file()


def test_read_write_world_md(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_world("p1", "# 世界")
    assert fr.read_world("p1") == "# 世界"


def test_write_chapter_creates_file(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_chapter("p1", 1, "第一章 楔子", "正文")
    p = tmp_path / "p1" / "chapters" / "0001_第一章 楔子.md"
    assert p.read_text(encoding="utf-8") == "正文"


def test_write_chapter_sanitizes_bad_chars(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_chapter("p1", 2, "卷/一:开始?", "正文二")
    # 文件名中的非法字符应被替换
    p = tmp_path / "p1" / "chapters" / "0002_卷_一_开始_.md"
    assert p.read_text(encoding="utf-8") == "正文二"


def test_write_character_json(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_character("p1", "c1", {"name": "林夕", "role": "主角"})
    p = tmp_path / "p1" / "characters" / "c1.json"
    assert p.is_file()
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["name"] == "林夕" and payload["role"] == "主角"


def test_delete_project_removes_dir(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_world("p1", "x")
    fr.delete_project("p1")
    assert not (tmp_path / "p1").exists()
