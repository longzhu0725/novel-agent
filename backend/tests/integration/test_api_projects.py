"""Projects REST 集成测试。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # 避免 lru_cache 跨用例污染
    from app.core import config as cfg
    from app.api import deps
    cfg.get_settings.cache_clear()
    deps.get_sqlite_repo.cache_clear()
    deps.get_file_repo.cache_clear()
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_create_and_list_project(client):
    r = client.post("/api/projects", json={"name": "我的小说", "genre": "玄幻"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert (Path(os.environ["DATA_DIR"]) / "projects" / pid).is_dir()
    r = client.get("/api/projects")
    assert r.status_code == 200 and len(r.json()) == 1


def test_get_and_patch_project(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.patch(f"/api/projects/{pid}", json={"logline": "一句话简介"})
    assert r.status_code == 200 and r.json()["logline"] == "一句话简介"


def test_advance_phase_legal(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    # 新设计: INIT → FOUNDATION → WRITING → DONE
    r = client.post(f"/api/projects/{pid}/phase", json={"to": "FOUNDATION"})
    assert r.status_code == 200 and r.json()["current_phase"] == "FOUNDATION"
    r = client.post(f"/api/projects/{pid}/phase", json={"to": "WRITING"})
    assert r.status_code == 200 and r.json()["current_phase"] == "WRITING"
    r = client.post(f"/api/projects/{pid}/phase", json={"to": "DONE"})
    assert r.status_code == 200 and r.json()["current_phase"] == "DONE"


def test_advance_phase_illegal(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    # INIT → WRITING 跳级，应该 400
    r = client.post(f"/api/projects/{pid}/phase", json={"to": "WRITING"})
    assert r.status_code == 400


def test_advance_phase_unknown_value(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.post(f"/api/projects/{pid}/phase", json={"to": "NOPE"})
    assert r.status_code == 400


def test_delete_project(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.delete(f"/api/projects/{pid}")
    assert r.status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_get_missing_project(client):
    r = client.get("/api/projects/nope")
    assert r.status_code == 404
