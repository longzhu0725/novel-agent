"""WebSocket /ws/chat 集成测试。"""
from __future__ import annotations

import json

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


def test_ping_returns_pong(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    with client.websocket_connect(f"/ws/chat?session_id=s1&project_id={pid}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        msg = ws.receive_json()
        assert msg["type"] == "pong"


def test_chat_message_unknown_project_rejected(client):
    with client.websocket_connect("/ws/chat?session_id=s1&project_id=missing") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"


def test_chat_history_endpoint(client):
    pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
    r = client.get(f"/api/projects/{pid}/chat/history?session_id=s1")
    assert r.status_code == 200 and r.json() == []
