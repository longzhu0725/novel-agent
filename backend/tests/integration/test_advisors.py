"""Advisor REST 端点集成测试。"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.core import config as cfg
    from app.api import deps
    cfg.get_settings.cache_clear()
    deps.get_sqlite_repo.cache_clear()
    deps.get_file_repo.cache_clear()
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_advisor_outline_missing_question(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.post(f"/api/projects/{pid}/advisors/outline", json={})
    assert r.status_code == 400


def test_advisor_style_missing_text(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.post(f"/api/projects/{pid}/advisors/style", json={})
    assert r.status_code == 400


def test_advisor_reviewer_missing_target(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.post(f"/api/projects/{pid}/advisors/reviewer", json={})
    assert r.status_code == 400


def test_advisor_on_missing_project(client):
    r = client.post("/api/projects/nonexistent/advisors/outline", json={"question": "x"})
    assert r.status_code == 404
