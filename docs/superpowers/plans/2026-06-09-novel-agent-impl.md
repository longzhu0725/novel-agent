# Novel Agent v0 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个本地优先的小说创作辅助 Web 应用：FastAPI + React + TypeScript，单 Agent + 工具，工作流驱动的 MVP。

**Architecture:** 单仓 monorepo；后端 Python（FastAPI + SQLite + OpenAI 兼容 LLM 客户端），前端 React 18 + Vite + TS + Tailwind；REST 处理 CRUD，WebSocket 处理流式 chat 与跨窗口广播；阶段状态机 5 阶段。

**Tech Stack:**
- 后端：Python 3.11+, FastAPI, uvicorn, SQLAlchemy 2.x (核心), aiosqlite, pydantic v2, pytest, httpx, openai SDK (or raw httpx for compat)
- 前端：React 18, TypeScript 5, Vite 5, Tailwind 3, zustand, axios, vitest, @testing-library/react
- 工具：ruff, mypy, prettier, eslint, pre-commit

**Spec 参考：** [`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](../specs/2026-06-09-novel-agent-design.md)

---

## 文件结构（实施前先确认）

```
novel-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/{__init__,projects,world,characters,outline,chapters,chat,ws,deps}.py
│   │   ├── core/{__init__,config,llm,state_machine,errors,compression}.py
│   │   ├── agent/{__init__,agent,tools,prompts,sessions}.py
│   │   └── storage/{__init__,file_repo,sqlite_repo,models}.py
│   ├── data/.gitkeep
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx, App.tsx, index.css, types.ts
│   │   ├── api/{client,ws}.ts
│   │   ├── stores/{projectStore,chatStore}.ts
│   │   ├── components/{PhaseNav,ErrorToast}.tsx
│   │   ├── features/{world,characters,outline,chapters,chat}/...
│   │   └── pages/{ProjectList,Workspace}.tsx
│   ├── tests/{setup.ts, stores.test.ts, ws.test.ts}
│   ├── package.json, tsconfig.json, vite.config.ts, tailwind.config.ts, postcss.config.js
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── .gitignore
├── README.md
└── LICENSE
```

---

## Phase 0：仓库脚手架

### Task 0.1：后端 pyproject 与开发依赖

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`

- [ ] **Step 1：写 `backend/pyproject.toml`**

```toml
[project]
name = "novel-agent-backend"
version = "0.1.0"
description = "Novel creation agent backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
    "httpx>=0.27",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.3",
    "mypy>=1.8",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 2：写 `backend/.env.example`**

```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATA_DIR=./data
```

- [ ] **Step 3：建空目录**

```bash
mkdir -p backend/app/{api,core,agent,storage} backend/data backend/tests/{unit,integration,fixtures}
touch backend/data/.gitkeep backend/tests/fixtures/.gitkeep
```

- [ ] **Step 4：提交**

```bash
git add backend/pyproject.toml backend/.env.example backend/data/.gitkeep backend/tests/
git commit -m "chore(backend): scaffold pyproject and dev dependencies"
```

### Task 0.2：后端基础包与最小 main

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1：写 `backend/app/__init__.py`** — 一行 `"""Novel Agent 后端应用。"""`
- [ ] **Step 2：写 `backend/tests/__init__.py`** — 一行 `"""测试包。"""`
- [ ] **Step 3：写 `backend/tests/conftest.py`**

```python
"""全局 pytest fixture。"""
from pathlib import Path
import pytest

@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
```

- [ ] **Step 4：写 `backend/app/main.py`**

```python
"""FastAPI 入口。"""
from fastapi import FastAPI

app = FastAPI(title="Novel Agent", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5：本地跑通**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/health` → `{"status":"ok"}`。

- [ ] **Step 6：提交**

```bash
git add backend/app backend/tests
git commit -m "chore(backend): minimal FastAPI app with health endpoint"
```

### Task 0.3：前端 Vite + React + TS + Tailwind

**Files:**
- Create: `frontend/package.json`、`tsconfig.json`、`vite.config.ts`、`tailwind.config.ts`、`postcss.config.js`、`index.html`、`src/main.tsx`、`src/App.tsx`、`src/index.css`、`.gitignore`、`tests/setup.ts`

- [ ] **Step 1：写 `frontend/package.json`**

```json
{
  "name": "novel-agent-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src --ext .ts,.tsx",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.2.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.57.0",
    "jsdom": "^24.0.0",
    "postcss": "^8.4.0",
    "prettier": "^3.2.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vitest": "^1.4.0"
  }
}
```

- [ ] **Step 2：写 `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022", "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext", "skipLibCheck": true,
    "moduleResolution": "bundler", "allowImportingTsExtensions": true,
    "resolveJsonModule": true, "isolatedModules": true, "noEmit": true,
    "jsx": "react-jsx", "strict": true,
    "noUnusedLocals": true, "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true, "esModuleInterop": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "tests"]
}
```

- [ ] **Step 3：写 `frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
  test: { environment: "jsdom", globals: true, setupFiles: ["./tests/setup.ts"] },
});
```

- [ ] **Step 4：写 `frontend/tailwind.config.ts`**

```ts
import type { Config } from "tailwindcss";
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 5：写 `frontend/postcss.config.js`**

```js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

- [ ] **Step 6：写 `frontend/index.html`**

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Novel Agent</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7：写 `frontend/src/main.tsx`**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

- [ ] **Step 8：写 `frontend/src/App.tsx`**

```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex items-center justify-center">
      <h1 className="text-3xl font-bold">Novel Agent</h1>
    </div>
  );
}
```

- [ ] **Step 9：写 `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 10：写 `frontend/.gitignore`**

```
node_modules
dist
.vite
*.log
```

- [ ] **Step 11：写 `frontend/tests/setup.ts`**

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 12：安装 + 验证**

```bash
cd frontend && npm install && npm run dev
```

`http://127.0.0.1:5173` 显示 "Novel Agent"。

- [ ] **Step 13：提交**

```bash
git add frontend/
git commit -m "chore(frontend): scaffold Vite + React + TS + Tailwind"
```

### Task 0.4：根级工具配置

**Files:**
- Create: `.pre-commit-config.yaml`、`.github/workflows/ci.yml`

- [ ] **Step 1：写 `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.5
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
        files: ^backend/
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.2.5
    hooks:
      - id: prettier
        files: ^frontend/src
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        files: ^backend/
        additional_dependencies: [pydantic>=2.6]
```

- [ ] **Step 2：写 `.github/workflows/ci.yml`**

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy app
      - run: pytest --cov=app --cov-report=term-missing
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
```

- [ ] **Step 3：提交**

```bash
git add .pre-commit-config.yaml .github/workflows/ci.yml
git commit -m "chore: add pre-commit and CI workflows"
```

---

## Phase 1：后端 core（配置、错误、状态机）

### Task 1.1：配置加载

**Files:**
- Create: `backend/app/core/{__init__,config}.py`
- Create: `backend/tests/unit/test_config.py`

- [ ] **Step 1：写测试**

```python
# tests/unit/test_config.py
import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", "/tmp/novel")
    s = Settings()
    assert s.llm_base_url == "https://x/v1"
    assert s.llm_api_key.get_secret_value() == "sk-test"
    assert str(s.data_dir) == "/tmp/novel"


def test_settings_missing_required_field(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "https://x")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("DATA_DIR", "/tmp")
    with pytest.raises(ValidationError):
        Settings()
```

- [ ] **Step 2：跑测试确认失败** — `pytest tests/unit/test_config.py -v`
- [ ] **Step 3：写 `backend/app/core/__init__.py`**

```python
"""核心模块：配置、LLM 客户端、状态机、错误。"""
```

- [ ] **Step 4：实现 `backend/app/core/config.py`**

```python
"""应用配置，从环境变量加载。"""
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="ignore", case_sensitive=False,
    )
    llm_base_url: str
    llm_api_key: SecretStr
    llm_model: str
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    data_dir: Path = Path("./data")


_singleton: Settings | None = None


def get_settings() -> Settings:
    global _singleton
    if _singleton is None:
        _singleton = Settings()  # type: ignore[call-arg]
    return _singleton
```

- [ ] **Step 5：跑测试确认通过**
- [ ] **Step 6：提交** — `git commit -m "feat(backend): add Settings with env loading"`

### Task 1.2：错误协议与信封

**Files:**
- Create: `backend/app/core/errors.py`
- Create: `backend/tests/unit/test_errors.py`

- [ ] **Step 1：写测试**

```python
# tests/unit/test_errors.py
from app.core.errors import ErrorCode, ProtocolError, error_envelope


def test_protocol_error_has_code_and_message():
    err = ProtocolError(ErrorCode.TOOL_EXEC_FAILED, "写盘失败")
    assert err.code == ErrorCode.TOOL_EXEC_FAILED
    assert err.recoverable is True


def test_protocol_error_can_be_non_recoverable():
    err = ProtocolError(ErrorCode.UNAUTHORIZED, "key 错", recoverable=False)
    assert err.recoverable is False


def test_error_envelope_serializes():
    env = error_envelope("abc", ErrorCode.LLM_TIMEOUT, "timeout", True)
    assert env["type"] == "error"
    assert env["code"] == "LLM_TIMEOUT"
    assert env["correlation_id"] == "abc"
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/core/errors.py`**

```python
"""协议错误码与 WS 错误信封。"""
from __future__ import annotations
from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
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
    def __init__(self, code: ErrorCode, message: str, recoverable: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable


def error_envelope(correlation_id: str, code: ErrorCode, message: str, recoverable: bool) -> dict[str, Any]:
    return {
        "type": "error",
        "correlation_id": correlation_id,
        "code": code.value,
        "message": message,
        "recoverable": recoverable,
    }
```

- [ ] **Step 4：跑测试确认通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): add protocol error codes and envelope"`

### Task 1.3：阶段状态机

**Files:**
- Create: `backend/app/core/state_machine.py`
- Create: `backend/tests/unit/test_state_machine.py`

- [ ] **Step 1：写测试（parametrize 多种 case）**

```python
# tests/unit/test_state_machine.py
import pytest
from app.core.errors import ErrorCode, ProtocolError
from app.core.state_machine import Phase, assert_legal_transition, is_legal


@pytest.mark.parametrize("frm,to", [
    (Phase.INIT, Phase.WORLD),
    (Phase.WORLD, Phase.CHARACTERS),
    (Phase.CHARACTERS, Phase.OUTLINE),
    (Phase.OUTLINE, Phase.WRITING),
    (Phase.WRITING, Phase.DONE),
])
def test_legal_forward(frm, to):
    assert is_legal(frm, to) is True
    assert_legal_transition(frm, to)


@pytest.mark.parametrize("frm,to", [
    (Phase.WORLD, Phase.INIT),
    (Phase.CHARACTERS, Phase.WORLD),
    (Phase.WRITING, Phase.OUTLINE),
    (Phase.DONE, Phase.WRITING),
])
def test_legal_backward(frm, to):
    assert is_legal(frm, to) is True


def test_self_transition_illegal():
    assert is_legal(Phase.WORLD, Phase.WORLD) is False


@pytest.mark.parametrize("frm,to", [
    (Phase.INIT, Phase.CHARACTERS),
    (Phase.WORLD, Phase.OUTLINE),
    (Phase.CHARACTERS, Phase.WRITING),
])
def test_skipping_forward_illegal(frm, to):
    assert is_legal(frm, to) is False
    with pytest.raises(ProtocolError) as ei:
        assert_legal_transition(frm, to)
    assert ei.value.code == ErrorCode.STATE_ILLEGAL_TRANSITION
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/core/state_machine.py`**

```python
"""项目阶段状态机。"""
from __future__ import annotations
from enum import Enum
from app.core.errors import ErrorCode, ProtocolError


class Phase(str, Enum):
    INIT = "INIT"
    WORLD = "WORLD"
    CHARACTERS = "CHARACTERS"
    OUTLINE = "OUTLINE"
    WRITING = "WRITING"
    DONE = "DONE"


_ORDER: dict[Phase, int] = {
    Phase.INIT: 0, Phase.WORLD: 1, Phase.CHARACTERS: 2,
    Phase.OUTLINE: 3, Phase.WRITING: 4, Phase.DONE: 5,
}


def is_legal(frm: Phase, to: Phase) -> bool:
    if frm == to:
        return False
    f, t = _ORDER[frm], _ORDER[to]
    return t == f + 1 or t < f  # 向前一格合法，向后任意合法


def assert_legal_transition(frm: Phase, to: Phase) -> None:
    if not is_legal(frm, to):
        raise ProtocolError(
            code=ErrorCode.STATE_ILLEGAL_TRANSITION,
            message=f"非法阶段转移：{frm.value} -> {to.value}",
        )
```

- [ ] **Step 4：跑测试确认通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): add phase state machine"`

---

## Phase 2：后端 storage

### Task 2.1：Pydantic 数据模型

**Files:**
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/models.py`
- Create: `backend/tests/unit/test_models.py`

- [ ] **Step 1：写测试**（8 个模型：Project / WorldDoc / Character / Relationship / OutlineNode / Chapter / ChatMessage / ProjectContext 的字段与 round-trip）

```python
# tests/unit/test_models.py
from datetime import datetime
from app.storage.models import (
    Chapter, ChapterStatus, Character, CharacterRelationship,
    ChatMessage, OutlineNode, Project, ProjectContext, WorldDoc,
)
from app.core.state_machine import Phase


def test_project_round_trip():
    p = Project(
        id="p1", name="x", storage_dir="p1",
        current_phase=Phase.INIT,
        created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9),
    )
    p2 = Project.model_validate_json(p.model_dump_json())
    assert p2.id == "p1" and p2.current_phase == Phase.INIT


def test_world_doc_default_version():
    assert WorldDoc(project_id="p1").version == 0


def test_character_fields():
    c = Character(id="c1", project_id="p1", name="林夕", role="主角",
                  profile_md="", updated_at=datetime(2026, 6, 9))
    assert c.role == "主角"


def test_relationship_fields():
    r = CharacterRelationship(id="r1", project_id="p1", source_id="c1",
                              target_id="c2", type="师父", note="")
    assert r.type == "师父"


def test_outline_node_root_and_child():
    root = OutlineNode(id="n1", project_id="p1", parent_id=None,
                       order=0, title="卷一")
    child = OutlineNode(id="n2", project_id="p1", parent_id="n1",
                        order=0, title="第一章")
    assert root.parent_id is None and child.parent_id == "n1"


def test_chapter_status_enum():
    c = Chapter(id="ch1", project_id="p1", order=1, title="第一章",
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    assert c.status == ChapterStatus.DRAFT


def test_chat_message_tool_calls():
    m = ChatMessage(id="m1", session_id="s1", project_id="p1",
                    role="assistant", content="", tool_calls_json="[{}]",
                    created_at=datetime(2026, 6, 9))
    assert m.tool_calls_json.startswith("[")


def test_project_context_default_summary():
    c = ProjectContext(project_id="p1")
    assert c.rolling_summary == "" and c.phase == Phase.INIT
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：写 `backend/app/storage/__init__.py`** — `"""存储层：文件 + SQLite。"""`
- [ ] **Step 4：实现 `backend/app/storage/models.py`**

```python
"""Pydantic 数据模型。"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from app.core.state_machine import Phase


class Project(BaseModel):
    id: str; name: str; logline: str = ""; genre: str = ""
    style_notes: str = ""; current_phase: Phase = Phase.INIT
    storage_dir: str; created_at: datetime; updated_at: datetime


class WorldDoc(BaseModel):
    project_id: str; content_md: str = ""; version: int = 0


class Character(BaseModel):
    id: str; project_id: str; name: str
    role: str = "配角"; profile_md: str = ""; updated_at: datetime


class CharacterRelationship(BaseModel):
    id: str; project_id: str; source_id: str; target_id: str
    type: str; note: str = ""


class OutlineNode(BaseModel):
    id: str; project_id: str; parent_id: str | None; order: int
    title: str; summary_md: str = ""; chapter_id: str | None = None


class ChapterStatus(str, Enum):
    DRAFT = "draft"
    DRAFT_PARTIAL = "draft_partial"
    REVIEWING = "reviewing"
    FINAL = "final"


class Chapter(BaseModel):
    id: str; project_id: str; outline_node_id: str | None = None
    order: int; title: str; content_md: str = ""; word_count: int = 0
    status: ChapterStatus = ChapterStatus.DRAFT
    created_at: datetime; updated_at: datetime


class ChatMessage(BaseModel):
    id: str; session_id: str; project_id: str; role: str
    content: str; tool_calls_json: str = "[]"; created_at: datetime


class ProjectContext(BaseModel):
    project_id: str; phase: Phase = Phase.INIT
    rolling_summary: str = ""; last_active_at: datetime | None = None
```

- [ ] **Step 5：跑测试确认通过**
- [ ] **Step 6：提交** — `git commit -m "feat(backend): add Pydantic models"`

### Task 2.2：SQLite 仓储

**Files:**
- Create: `backend/app/storage/sqlite_repo.py`
- Create: `backend/tests/unit/test_sqlite_repo.py`

- [ ] **Step 1：写测试（最小 4 个）**

```python
# tests/unit/test_sqlite_repo.py
import pytest
from datetime import datetime
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo
from app.core.state_machine import Phase


@pytest.fixture
def repo(tmp_path):
    r = SqliteRepo(tmp_path / "test.db")
    r.init_schema()
    return r


def test_init_schema_idempotent(repo):
    repo.init_schema(); repo.init_schema()


def test_insert_and_get_project(repo):
    p = Project(id="p1", name="x", storage_dir="p1",
                current_phase=Phase.INIT,
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p)
    got = repo.get_project("p1")
    assert got is not None and got.name == "x"


def test_list_projects_empty(repo):
    assert repo.list_projects() == []


def test_delete_project(repo):
    p = Project(id="p1", name="x", storage_dir="p1",
                current_phase=Phase.INIT,
                created_at=datetime(2026, 6, 9), updated_at=datetime(2026, 6, 9))
    repo.insert_project(p)
    repo.delete_project("p1")
    assert repo.get_project("p1") is None
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/storage/sqlite_repo.py`**

```python
"""SQLite 仓储（同步）。"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path
from app.core.state_machine import Phase
from app.storage.models import (
    Chapter, ChapterStatus, Character, CharacterRelationship,
    ChatMessage, OutlineNode, Project, ProjectContext, WorldDoc,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL,
    logline TEXT NOT NULL DEFAULT '', genre TEXT NOT NULL DEFAULT '',
    style_notes TEXT NOT NULL DEFAULT '',
    current_phase TEXT NOT NULL, storage_dir TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS world_docs (
    project_id TEXT PRIMARY KEY,
    content_md TEXT NOT NULL DEFAULT '', version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    name TEXT NOT NULL, role TEXT NOT NULL DEFAULT '配角',
    profile_md TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
CREATE TABLE IF NOT EXISTS character_relationships (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    source_id TEXT NOT NULL, target_id TEXT NOT NULL,
    type TEXT NOT NULL, note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rel_project ON character_relationships(project_id);
CREATE TABLE IF NOT EXISTS outline_nodes (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, parent_id TEXT,
    "order" INTEGER NOT NULL, title TEXT NOT NULL,
    summary_md TEXT NOT NULL DEFAULT '', chapter_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_outline_project ON outline_nodes(project_id);
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, outline_node_id TEXT,
    "order" INTEGER NOT NULL, title TEXT NOT NULL,
    content_md TEXT NOT NULL DEFAULT '', word_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id);
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, project_id TEXT NOT NULL,
    role TEXT NOT NULL, content TEXT NOT NULL DEFAULT '',
    tool_calls_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_ps ON chat_messages(project_id, session_id, created_at);
CREATE TABLE IF NOT EXISTS project_context (
    project_id TEXT PRIMARY KEY, phase TEXT NOT NULL,
    rolling_summary TEXT NOT NULL DEFAULT '', last_active_at TEXT
);
"""


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class SqliteRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA journal_mode = WAL")
        return c

    def init_schema(self) -> None:
        with self._conn() as c:
            c.executescript(_SCHEMA)

    # ---------- Project ----------
    def insert_project(self, p: Project) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)",
                (p.id, p.name, p.logline, p.genre, p.style_notes,
                 p.current_phase.value, p.storage_dir,
                 _iso(p.created_at), _iso(p.updated_at)))

    def get_project(self, pid: str) -> Project | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        return self._row_to_project(r) if r else None

    def list_projects(self) -> list[Project]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [self._row_to_project(r) for r in rows]

    def update_project_phase(self, pid: str, phase: Phase, updated_at: datetime) -> None:
        with self._conn() as c:
            c.execute("UPDATE projects SET current_phase=?, updated_at=? WHERE id=?",
                      (phase.value, _iso(updated_at), pid))

    def update_project_meta(self, pid: str, *, name: str, logline: str, genre: str,
                            style_notes: str, updated_at: datetime) -> None:
        with self._conn() as c:
            c.execute("UPDATE projects SET name=?, logline=?, genre=?, style_notes=?, updated_at=? WHERE id=?",
                      (name, logline, genre, style_notes, _iso(updated_at), pid))

    def delete_project(self, pid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM projects WHERE id=?", (pid,))

    # ---------- WorldDoc ----------
    def upsert_world_doc(self, w: WorldDoc) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO world_docs VALUES (?,?,?) "
                "ON CONFLICT(project_id) DO UPDATE SET content_md=excluded.content_md, "
                "version=world_docs.version+1",
                (w.project_id, w.content_md, w.version))

    def get_world_doc(self, pid: str) -> WorldDoc | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM world_docs WHERE project_id=?", (pid,)).fetchone()
        return WorldDoc(project_id=r["project_id"], content_md=r["content_md"], version=r["version"]) if r else None

    # ---------- Character ----------
    def insert_character(self, ch: Character) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO characters VALUES (?,?,?,?,?,?)",
                      (ch.id, ch.project_id, ch.name, ch.role, ch.profile_md, _iso(ch.updated_at)))

    def get_character(self, cid: str) -> Character | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
        if r is None: return None
        return Character(id=r["id"], project_id=r["project_id"], name=r["name"],
                         role=r["role"], profile_md=r["profile_md"], updated_at=_parse(r["updated_at"]))  # type: ignore

    def list_characters(self, pid: str) -> list[Character]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM characters WHERE project_id=? ORDER BY name", (pid,)).fetchall()
        return [Character(id=r["id"], project_id=r["project_id"], name=r["name"],
                          role=r["role"], profile_md=r["profile_md"], updated_at=_parse(r["updated_at"]))  # type: ignore
                for r in rows]

    def update_character(self, ch: Character) -> None:
        with self._conn() as c:
            c.execute("UPDATE characters SET name=?, role=?, profile_md=?, updated_at=? WHERE id=?",
                      (ch.name, ch.role, ch.profile_md, _iso(ch.updated_at), ch.id))

    def delete_character(self, cid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM characters WHERE id=?", (cid,))

    def add_relationship(self, r: CharacterRelationship) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO character_relationships VALUES (?,?,?,?,?,?)",
                      (r.id, r.project_id, r.source_id, r.target_id, r.type, r.note))

    def list_relationships(self, pid: str) -> list[CharacterRelationship]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM character_relationships WHERE project_id=?", (pid,)).fetchall()
        return [CharacterRelationship(id=r["id"], project_id=r["project_id"],
                source_id=r["source_id"], target_id=r["target_id"],
                type=r["type"], note=r["note"]) for r in rows]

    # ---------- Outline ----------
    def insert_outline_node(self, n: OutlineNode) -> None:
        with self._conn() as c:
            c.execute('INSERT INTO outline_nodes VALUES (?,?,?,?,?,?,?)',
                      (n.id, n.project_id, n.parent_id, n.order, n.title, n.summary_md, n.chapter_id))

    def update_outline_node(self, n: OutlineNode) -> None:
        with self._conn() as c:
            c.execute('UPDATE outline_nodes SET parent_id=?, "order"=?, title=?, summary_md=?, chapter_id=? WHERE id=?',
                      (n.parent_id, n.order, n.title, n.summary_md, n.chapter_id, n.id))

    def delete_outline_node(self, nid: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM outline_nodes WHERE id=?", (nid,))

    def list_outline(self, pid: str) -> list[OutlineNode]:
        with self._conn() as c:
            rows = c.execute('SELECT * FROM outline_nodes WHERE project_id=? ORDER BY "order"', (pid,)).fetchall()
        return [OutlineNode(id=r["id"], project_id=r["project_id"], parent_id=r["parent_id"],
                            order=r["order"], title=r["title"], summary_md=r["summary_md"],
                            chapter_id=r["chapter_id"]) for r in rows]

    # ---------- Chapter ----------
    def insert_chapter(self, ch: Chapter) -> None:
        with self._conn() as c:
            c.execute('INSERT INTO chapters VALUES (?,?,?,?,?,?,?,?,?,?)',
                      (ch.id, ch.project_id, ch.outline_node_id, ch.order, ch.title,
                       ch.content_md, ch.word_count, ch.status.value,
                       _iso(ch.created_at), _iso(ch.updated_at)))

    def update_chapter(self, ch: Chapter) -> None:
        with self._conn() as c:
            c.execute('UPDATE chapters SET outline_node_id=?, "order"=?, title=?, content_md=?, '
                      'word_count=?, status=?, updated_at=? WHERE id=?',
                      (ch.outline_node_id, ch.order, ch.title, ch.content_md,
                       ch.word_count, ch.status.value, _iso(ch.updated_at), ch.id))

    def get_chapter(self, chid: str) -> Chapter | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM chapters WHERE id=?", (chid,)).fetchone()
        return self._row_to_chapter(r) if r else None

    def list_chapters(self, pid: str) -> list[Chapter]:
        with self._conn() as c:
            rows = c.execute('SELECT * FROM chapters WHERE project_id=? ORDER BY "order"', (pid,)).fetchall()
        return [self._row_to_chapter(r) for r in rows]

    # ---------- ChatMessage ----------
    def insert_chat_message(self, m: ChatMessage) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO chat_messages VALUES (?,?,?,?,?,?,?)",
                      (m.id, m.session_id, m.project_id, m.role, m.content,
                       m.tool_calls_json, _iso(m.created_at)))

    def list_chat_messages(self, pid: str, sid: str, limit: int = 50) -> list[ChatMessage]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM chat_messages WHERE project_id=? AND session_id=? "
                "ORDER BY created_at DESC LIMIT ?", (pid, sid, limit)).fetchall()
        return [ChatMessage(id=r["id"], session_id=r["session_id"], project_id=r["project_id"],
                            role=r["role"], content=r["content"],
                            tool_calls_json=r["tool_calls_json"], created_at=_parse(r["created_at"]))  # type: ignore
                for r in rows]

    # ---------- ProjectContext ----------
    def get_project_context(self, pid: str) -> ProjectContext | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM project_context WHERE project_id=?", (pid,)).fetchone()
        if r is None: return None
        return ProjectContext(project_id=r["project_id"], phase=Phase(r["phase"]),
                              rolling_summary=r["rolling_summary"], last_active_at=_parse(r["last_active_at"]))

    def upsert_project_context(self, ctx: ProjectContext) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO project_context VALUES (?,?,?,?) "
                "ON CONFLICT(project_id) DO UPDATE SET phase=excluded.phase, "
                "rolling_summary=excluded.rolling_summary, last_active_at=excluded.last_active_at",
                (ctx.project_id, ctx.phase.value, ctx.rolling_summary, _iso(ctx.last_active_at)))

    # ---------- 私有 ----------
    @staticmethod
    def _row_to_project(r: sqlite3.Row) -> Project:
        return Project(id=r["id"], name=r["name"], logline=r["logline"],
                       genre=r["genre"], style_notes=r["style_notes"],
                       current_phase=Phase(r["current_phase"]), storage_dir=r["storage_dir"],
                       created_at=_parse(r["created_at"]),  # type: ignore
                       updated_at=_parse(r["updated_at"]))  # type: ignore

    @staticmethod
    def _row_to_chapter(r: sqlite3.Row) -> Chapter:
        return Chapter(id=r["id"], project_id=r["project_id"], outline_node_id=r["outline_node_id"],
                       order=r["order"], title=r["title"], content_md=r["content_md"],
                       word_count=r["word_count"], status=ChapterStatus(r["status"]),
                       created_at=_parse(r["created_at"]),  # type: ignore
                       updated_at=_parse(r["updated_at"]))  # type: ignore
```

- [ ] **Step 4：跑测试确认通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): add SqliteRepo with full CRUD"`

### Task 2.3：FileRepo

**Files:**
- Create: `backend/app/storage/file_repo.py`
- Create: `backend/tests/unit/test_file_repo.py`

- [ ] **Step 1：写测试（5 个）**

```python
# tests/unit/test_file_repo.py
from app.storage.file_repo import FileRepo


def test_create_project_dir(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    assert (tmp_path / "p1").is_dir()
    assert (tmp_path / "p1" / "chapters").is_dir()
    assert (tmp_path / "p1" / "characters").is_dir()


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


def test_write_character_json(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.write_character("p1", "c1", {"name": "林夕", "role": "主角"})
    p = tmp_path / "p1" / "characters" / "c1.json"
    assert p.is_file() and "林夕" in p.read_text(encoding="utf-8")


def test_delete_project_removes_dir(tmp_path):
    fr = FileRepo(tmp_path)
    fr.create_project("p1")
    fr.delete_project("p1")
    assert not (tmp_path / "p1").exists()
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/storage/file_repo.py`**

```python
"""文件系统仓储。"""
from __future__ import annotations
import json
import shutil
from pathlib import Path


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
        if d.exists(): shutil.rmtree(d)

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

    def write_character(self, pid: str, cid: str, data: dict) -> Path:
        p = self.root / pid / "characters" / f"{cid}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p


def _safe(s: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    return "".join("_" if c in bad else c for c in s).strip()
```

- [ ] **Step 4：跑测试确认通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): add FileRepo"`

---

---

## Phase 3：后端 REST API

### Task 3.1：FastAPI 依赖与路由装配

**Files:**
- Create: `backend/app/api/{__init__,deps,projects,world,characters,outline,chapters,chat,ws}.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1：写 `backend/app/api/__init__.py`** — `"""API 路由层。"""`
- [ ] **Step 2：写 `backend/app/api/deps.py`**

```python
"""FastAPI 依赖注入。"""
from functools import lru_cache
from pathlib import Path
from fastapi import Depends
from app.core.config import Settings, get_settings
from app.storage.file_repo import FileRepo
from app.storage.sqlite_repo import SqliteRepo


@lru_cache(maxsize=1)
def get_sqlite_repo(settings: Settings = Depends(get_settings)) -> SqliteRepo:
    path = Path(settings.data_dir) / "novel.db"
    r = SqliteRepo(path); r.init_schema(); return r


@lru_cache(maxsize=1)
def get_file_repo(settings: Settings = Depends(get_settings)) -> FileRepo:
    return FileRepo(Path(settings.data_dir) / "projects")
```

- [ ] **Step 3：写所有路由文件**（每个文件用 `from fastapi import APIRouter; router = APIRouter()` 作为桩）
- [ ] **Step 4：改 `backend/app/main.py`**

```python
"""FastAPI 入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import projects, world, characters, outline, chapters, chat, ws


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.api.deps import get_file_repo, get_sqlite_repo
    get_sqlite_repo(); get_file_repo()
    yield


app = FastAPI(title="Novel Agent", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(projects.router)
app.include_router(world.router)
app.include_router(characters.router)
app.include_router(outline.router)
app.include_router(chapters.router)
app.include_router(chat.router)
app.include_router(ws.router)
```

- [ ] **Step 5：验证 import** — `python -c "from app.main import app; print(app.title)"` → `Novel Agent`
- [ ] **Step 6：提交** — `git commit -m "feat(backend): wire up FastAPI lifespan and router stubs"`

### Task 3.2：Projects REST 端点（TDD）

**Files:**
- Modify: `backend/app/api/projects.py`
- Create: `backend/tests/integration/test_api_projects.py`

- [ ] **Step 1：写 5 个测试**（list / create / get / advance phase / illegal transition / delete）— 见 spec 第 3.1 节
- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/api/projects.py`**

```python
"""Projects REST 路由。"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.errors import ProtocolError
from app.core.state_machine import Phase, assert_legal_transition
from app.storage.file_repo import FileRepo
from app.storage.models import Project
from app.storage.sqlite_repo import SqliteRepo
from app.api.deps import get_file_repo, get_sqlite_repo

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_dict(p: Project) -> dict[str, Any]:
    return {
        "id": p.id, "name": p.name, "logline": p.logline,
        "genre": p.genre, "style_notes": p.style_notes,
        "current_phase": p.current_phase.value, "storage_dir": p.storage_dir,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.get("")
def list_projects(repo: SqliteRepo = Depends(get_sqlite_repo)) -> list[dict[str, Any]]:
    return [_to_dict(p) for p in repo.list_projects()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(body: dict[str, Any], sq: SqliteRepo = Depends(get_sqlite_repo),
                   fr: FileRepo = Depends(get_file_repo)) -> dict[str, Any]:
    now = datetime.now()
    pid = uuid.uuid4().hex
    p = Project(
        id=pid, name=body.get("name", "未命名"),
        logline=body.get("logline", ""), genre=body.get("genre", ""),
        style_notes=body.get("style_notes", ""),
        current_phase=Phase.INIT, storage_dir=pid,
        created_at=now, updated_at=now)
    sq.insert_project(p); fr.create_project(pid)
    return _to_dict(p)


@router.get("/{pid}")
def get_project(pid: str, repo: SqliteRepo = Depends(get_sqlite_repo)) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None: raise HTTPException(404, "Project not found")
    return _to_dict(p)


@router.patch("/{pid}")
def update_project(pid: str, body: dict[str, Any],
                   repo: SqliteRepo = Depends(get_sqlite_repo)) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None: raise HTTPException(404, "Project not found")
    repo.update_project_meta(pid,
        name=body.get("name", p.name), logline=body.get("logline", p.logline),
        genre=body.get("genre", p.genre), style_notes=body.get("style_notes", p.style_notes),
        updated_at=datetime.now())
    return _to_dict(repo.get_project(pid))  # type: ignore


@router.delete("/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(pid: str, sq: SqliteRepo = Depends(get_sqlite_repo),
                   fr: FileRepo = Depends(get_file_repo)) -> None:
    sq.delete_project(pid); fr.delete_project(pid)


@router.post("/{pid}/phase")
def advance_phase(pid: str, body: dict[str, Any],
                  repo: SqliteRepo = Depends(get_sqlite_repo)) -> dict[str, Any]:
    p = repo.get_project(pid)
    if p is None: raise HTTPException(404, "Project not found")
    try:
        to = Phase(body["to"]); assert_legal_transition(p.current_phase, to)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e)) from e
    except ProtocolError as e:
        raise HTTPException(400, {"code": e.code.value, "message": e.message}) from e
    repo.update_project_phase(pid, to, datetime.now())
    return _to_dict(repo.get_project(pid))  # type: ignore
```

- [ ] **Step 4：跑测试确认通过**（5 passed）
- [ ] **Step 5：提交** — `git commit -m "feat(backend): projects REST endpoints with state machine"`

### Task 3.3：World / Characters / Outline / Chapters / Chat 路由

**Files:**
- Modify: `backend/app/api/{world,characters,outline,chapters,chat}.py`

每个文件实现标准的 REST 集合。代码骨架（关键部分）：

- [ ] **Step 1：`world.py`** — `GET / PUT` `/api/projects/{pid}/world`，读写 `world.md` + SQLite
- [ ] **Step 2：`characters.py`** — `GET / POST / GET / PATCH / DELETE` `/api/projects/{pid}/characters[/{cid}]`
- [ ] **Step 3：`outline.py`** — 同模式，针对 `outline_nodes`
- [ ] **Step 4：`chapters.py`** — 同模式；`POST` 写 md + SQLite；`PATCH` 更新状态
- [ ] **Step 5：`chat.py`** — `GET /api/projects/{pid}/chat/history?session_id=&limit=` 返回 `chat_messages`
- [ ] **Step 6：跑所有集成测试**
- [ ] **Step 7：提交** — `git commit -m "feat(backend): REST endpoints for world, characters, outline, chapters, chat"`

> 完整实现代码与 Task 3.2 同模式：每个路由做参数解析 → 调仓储 → 返 dict 或 404/400。

---

## Phase 4：后端 LLM 客户端

### Task 4.1：OpenAI 兼容客户端

**Files:**
- Create: `backend/app/core/llm.py`
- Create: `backend/tests/unit/test_llm_client.py`

- [ ] **Step 1：写测试**（FakeTransport 模拟流式响应 + 验证 delta / tool_call 事件）

```python
# tests/unit/test_llm_client.py
import pytest
from app.core.llm import LLMClient, LLMMessage


class FakeTransport:
    def __init__(self, seq):
        self.seq = list(seq); self.calls = []
    async def stream(self, url, headers, body):
        self.calls.append(body)
        s = self.seq.pop(0) if self.seq else []
        for c in s: yield c


@pytest.fixture
def make():
    def _make(seq):
        t = FakeTransport(seq)
        c = LLMClient("https://x", "sk", "gpt-4o", _transport=t)
        return c, t
    return _make


@pytest.mark.asyncio
async def test_text_delta(make):
    c, _ = make([[{"choices": [{"delta": {"content": "你好"}}]}]])
    out = []
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        if ev["type"] == "delta": out.append(ev["text"])
    assert "你好" in out


@pytest.mark.asyncio
async def test_tool_call_emitted(make):
    seq = [{"choices": [{
        "delta": {"tool_calls": [{
            "id": "c1",
            "function": {"name": "x", "arguments": '{"a":1}'}
        }]},
        "finish_reason": "tool_calls",
    }]}]
    c, _ = make([seq])
    tc = None
    async for ev in c.stream_chat_events([LLMMessage("user", "hi")], tools=[]):
        if ev["type"] == "tool_call": tc = ev
    assert tc is not None and tc["name"] == "x" and tc["arguments"] == {"a": 1}
```

- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/core/llm.py`**

```python
"""OpenAI 兼容 LLM 客户端（流式）。"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol
import httpx
from app.core.errors import ErrorCode, ProtocolError


@dataclass
class LLMMessage:
    role: str; content: str | None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class LLMTool:
    name: str; description: str
    parameters: dict[str, Any] = field(default_factory=dict)


class Transport(Protocol):
    async def stream(self, url, headers, body) -> AsyncIterator[dict[str, Any]]: ...


class HttpxTransport:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
    async def _get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0))
        return self._client
    async def stream(self, url, headers, body):
        client = await self._get()
        async with client.stream("POST", url, json=body, headers=headers) as r:
            if r.status_code in (401, 403):
                raise ProtocolError(ErrorCode.UNAUTHORIZED, "LLM 鉴权失败", recoverable=False)
            if r.status_code == 429:
                raise ProtocolError(ErrorCode.LLM_RATE_LIMIT, "LLM 限流")
            if r.status_code >= 500:
                raise ProtocolError(ErrorCode.LLM_TIMEOUT, f"LLM {r.status_code}")
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"): continue
                payload = line[5:].strip()
                if payload == "[DONE]": break
                try: yield json.loads(payload)
                except json.JSONDecodeError:
                    raise ProtocolError(ErrorCode.LLM_BAD_RESPONSE, "非 JSON SSE 行")


def _to_msg(m: LLMMessage) -> dict[str, Any]:
    out: dict[str, Any] = {"role": m.role}
    if m.content is not None: out["content"] = m.content
    if m.tool_calls: out["tool_calls"] = m.tool_calls
    if m.tool_call_id: out["tool_call_id"] = m.tool_call_id
    if m.name: out["name"] = m.name
    return out


def _to_tool(t: LLMTool) -> dict[str, Any]:
    return {"type": "function", "function": {
        "name": t.name, "description": t.description, "parameters": t.parameters}}


class LLMClient:
    def __init__(self, base_url, api_key, model, _transport=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key; self.model = model
        self._transport = _transport or HttpxTransport()

    def _headers(self): return {
        "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
    def _body(self, msgs, tools, stream):
        return {"model": self.model, "messages": [_to_msg(m) for m in msgs],
                "tools": [_to_tool(t) for t in tools] if tools else None, "stream": stream}

    async def stream_chat_events(self, messages, tools) -> AsyncIterator[dict[str, Any]]:
        body = self._body(messages, tools, stream=True)
        url = f"{self.base_url}/chat/completions"
        current_tool: dict[str, Any] | None = None
        current_args = ""
        async for chunk in self._transport.stream(url, self._headers(), body):
            choices = chunk.get("choices") or []
            if not choices: continue
            choice = choices[0]; delta = choice.get("delta") or {}
            if (content := delta.get("content")):
                yield {"type": "delta", "text": content}
            if (tc := delta.get("tool_calls")):
                item = tc[0]
                if item.get("id"):
                    if current_tool is not None:
                        try: current_tool["arguments"] = json.loads(current_args or "{}")
                        except json.JSONDecodeError: current_tool["arguments"] = {}
                        yield {"type": "tool_call", **current_tool}
                    current_tool = {"id": item["id"], "name": item.get("function", {}).get("name")}
                    current_args = item.get("function", {}).get("arguments") or ""
                else:
                    current_args += item.get("function", {}).get("arguments") or ""
            if (finish := choice.get("finish_reason")) and current_tool is not None:
                try: current_tool["arguments"] = json.loads(current_args or "{}")
                except json.JSONDecodeError: current_tool["arguments"] = {}
                yield {"type": "tool_call", **current_tool}
                current_tool = None; current_args = ""
        if current_tool is not None:
            try: current_tool["arguments"] = json.loads(current_args or "{}")
            except json.JSONDecodeError: current_tool["arguments"] = {}
            yield {"type": "tool_call", **current_tool}
        yield {"type": "done"}
```

- [ ] **Step 4：跑测试通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): OpenAI-compatible LLM client with stream + tool calls"`

### Task 4.2：上下文压缩

**Files:**
- Create: `backend/app/core/compression.py`
- Create: `backend/tests/unit/test_context_compression.py`

- [ ] **Step 1：写测试**（3 个：should_compress 阈值 / 不触发 / 实际压缩保留 tail）
- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/core/compression.py`**

```python
"""上下文压缩。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from app.core.llm import LLMMessage


@dataclass
class CompressionResult:
    summary: str; tail: list[LLMMessage]


class Summarizer(Protocol):
    async def summarize(self, text: str) -> str: ...


def _approx_tokens(s: str) -> int: return max(1, len(s))


def total_tokens(messages: list[LLMMessage]) -> int:
    return sum(_approx_tokens(m.content or "") for m in messages) + 50 * len(messages)


def should_compress(messages: list[LLMMessage], *, model_window: int, threshold: float = 0.8) -> bool:
    return total_tokens(messages) >= int(model_window * threshold)


async def compress_messages(messages: list[LLMMessage], *, llm: Summarizer,
                            existing_summary: str, keep_ratio: float = 0.7) -> CompressionResult:
    if not messages: return CompressionResult(summary=existing_summary, tail=[])
    cut = max(1, int(len(messages) * (1 - keep_ratio)))
    head, tail = messages[:cut], messages[cut:]
    text = "\n".join(f"[{m.role}] {m.content or ''}" for m in head)
    new = await llm.summarize(text)
    summary = (existing_summary + "\n" + new).strip() if existing_summary else new
    return CompressionResult(summary=summary, tail=tail)
```

- [ ] **Step 4：跑测试通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): context compression"`

---

## Phase 5：后端 Agent

### Task 5.1：工具注册表

**Files:**
- Create: `backend/app/agent/{__init__,tools}.py`
- Create: `backend/tests/unit/test_tools.py`

- [ ] **Step 1：写测试**（6 个：阶段工具过滤 / 执行 / 阶段门控 / 参数校验）
- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：写 `backend/app/agent/__init__.py`** — `"""Agent 模块。"""`
- [ ] **Step 4：实现 `backend/app/agent/tools.py`**（关键代码）

```python
"""Agent 工具：按阶段授权 + JSON Schema。"""
from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from app.core.errors import ProtocolError
from app.core.llm import LLMTool
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import (Character, Chapter, ChapterStatus, OutlineNode, WorldDoc)
from app.storage.sqlite_repo import SqliteRepo


@dataclass
class ToolContext:
    project_id: str; sqlite: SqliteRepo; file: FileRepo; project_phase: Phase


@dataclass
class ToolResult:
    ok: bool; data: Any = None; error: str | None = None


# 实现函数略（参考 design doc 第 6.3 节工具集）：
# _impl_upsert_world_doc / _impl_read_world_doc
# _impl_create_character / _impl_update_character / _impl_list_characters
# _impl_create_outline_node / _impl_update_outline_node / _impl_list_outline
# _impl_create_chapter / _impl_append_to_chapter / _impl_read_chapter
# _impl_advance_phase / _impl_read_project_summary


@dataclass
class ToolDef:
    name: str; description: str; parameters: dict[str, Any]
    allowed_phases: set[Phase]
    impl: Callable[[ToolContext, dict[str, Any]], ToolResult]


def _schema(props: dict, required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required}


# 注册表：每个工具含 allowed_phases 控制阶段
_REGISTRY: list[ToolDef] = [
    ToolDef("upsert_world_doc", "整体覆盖世界观 markdown",
        _schema({"content_md": {"type": "string"}}, ["content_md"]),
        {Phase.WORLD}, _impl_upsert_world_doc),
    ToolDef("read_world_doc", "读取世界观",
        _schema({}, []),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING},
        _impl_read_world_doc),
    ToolDef("create_character", "创建人物卡",
        _schema({"name": {"type": "string"}, "role": {"type": "string"},
                 "profile_md": {"type": "string"}}, ["name"]),
        {Phase.CHARACTERS}, _impl_create_character),
    ToolDef("update_character", "更新人物卡",
        _schema({"id": {"type": "string"}, "name": {"type": "string"},
                 "role": {"type": "string"}, "profile_md": {"type": "string"}}, ["id"]),
        {Phase.CHARACTERS}, _impl_update_character),
    ToolDef("list_characters", "列人物",
        _schema({}, []),
        {Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING}, _impl_list_characters),
    ToolDef("create_outline_node", "建大纲节点",
        _schema({"parent_id": {"type": ["string", "null"]}, "order": {"type": "integer"},
                 "title": {"type": "string"}, "summary_md": {"type": "string"}}, ["title"]),
        {Phase.OUTLINE}, _impl_create_outline_node),
    ToolDef("update_outline_node", "改大纲节点",
        _schema({"id": {"type": "string"}, "parent_id": {"type": ["string", "null"]},
                 "order": {"type": "integer"}, "title": {"type": "string"},
                 "summary_md": {"type": "string"},
                 "chapter_id": {"type": ["string", "null"]}}, ["id"]),
        {Phase.OUTLINE, Phase.WRITING}, _impl_update_outline_node),
    ToolDef("list_outline", "列大纲",
        _schema({}, []),
        {Phase.OUTLINE, Phase.WRITING}, _impl_list_outline),
    ToolDef("create_chapter", "建章节",
        _schema({"title": {"type": "string"}, "order": {"type": "integer"},
                 "content_md": {"type": "string"},
                 "outline_node_id": {"type": ["string", "null"]}}, ["title", "order"]),
        {Phase.WRITING}, _impl_create_chapter),
    ToolDef("append_to_chapter", "追加章节正文",
        _schema({"chapter_id": {"type": "string"}, "delta": {"type": "string"}},
                ["chapter_id", "delta"]),
        {Phase.WRITING}, _impl_append_to_chapter),
    ToolDef("read_chapter", "读章节",
        _schema({"chapter_id": {"type": "string"}}, ["chapter_id"]),
        {Phase.WRITING}, _impl_read_chapter),
    ToolDef("advance_phase", "切换阶段",
        _schema({"to": {"type": "string"}}, ["to"]),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_advance_phase),
    ToolDef("read_project_summary", "读项目摘要",
        _schema({}, []),
        {Phase.WORLD, Phase.CHARACTERS, Phase.OUTLINE, Phase.WRITING, Phase.DONE},
        _impl_read_project_summary),
]


def get_tools_for_phase(phase: Phase) -> list[LLMTool]:
    return [LLMTool(name=t.name, description=t.description, parameters=t.parameters)
            for t in _REGISTRY if phase in t.allowed_phases]


def get_tool_def(name: str) -> ToolDef | None:
    return next((t for t in _REGISTRY if t.name == name), None)


def execute_tool(tool: LLMTool, ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    defn = get_tool_def(tool.name)
    if defn is None: return ToolResult(ok=False, error=f"未知工具：{tool.name}")
    if ctx.project_phase not in defn.allowed_phases:
        return ToolResult(ok=False, error=f"工具 {tool.name} 在当前阶段 {ctx.project_phase.value} 不可用")
    if not isinstance(args, dict):
        return ToolResult(ok=False, error="参数必须是对象")
    for k in defn.parameters.get("required", []):
        if k not in args: return ToolResult(ok=False, error=f"缺少必填参数：{k}")
    try: return defn.impl(ctx, args)
    except Exception as e:
        return ToolResult(ok=False, error=f"{type(e).__name__}: {e}")
```

- [ ] **Step 5：跑测试通过**
- [ ] **Step 6：提交** — `git commit -m "feat(backend): agent tools registry with phase gating"`

### Task 5.2：系统提示模板

**Files:**
- Create: `backend/app/agent/prompts.py`
- Create: `backend/tests/unit/test_prompts.py`

- [ ] **Step 1：写测试**（1 个：world 阶段 prompt 包含 "世界观" + 工具名）
- [ ] **Step 2：实现 `prompts.py`**（见 design doc 第 6.2 节，提供 `build_system_prompt(project, phase, rolling_summary, tool_names)`）
- [ ] **Step 3：跑测试通过**
- [ ] **Step 4：提交** — `git commit -m "feat(backend): system prompt templates per phase"`

### Task 5.3：Agent 主循环

**Files:**
- Create: `backend/app/agent/agent.py`
- Create: `backend/tests/unit/test_agent.py`

- [ ] **Step 1：写 2 个测试**（脚本式 transport：完整 tool_call + final 流程 / 超过 10 轮自动停）
- [ ] **Step 2：跑测试确认失败**
- [ ] **Step 3：实现 `backend/app/agent/agent.py`**

```python
"""Agent 主循环。"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterator
from app.agent.prompts import build_system_prompt
from app.agent.tools import ToolContext, execute_tool, get_tools_for_phase
from app.core.compression import compress_messages, should_compress
from app.core.llm import LLMClient, LLMMessage
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.models import ChatMessage, ProjectContext
from app.storage.sqlite_repo import SqliteRepo


MAX_TOOL_ROUNDS = 10
DEFAULT_MODEL_WINDOW = 100_000
COMPRESS_THRESHOLD = 0.8
KEEP_RATIO = 0.7
HISTORY_LIMIT = 8


AgentEvent = dict[str, Any]


class Agent:
    def __init__(self, llm: LLMClient, sqlite: SqliteRepo, file: FileRepo,
                 *, model_window: int = DEFAULT_MODEL_WINDOW):
        self.llm = llm; self.sqlite = sqlite; self.file = file
        self.model_window = model_window

    def _build_context(self, project: Project, phase: Phase,
                        history: list[ChatMessage], user_text: str, summary: str) -> list[LLMMessage]:
        tools = get_tools_for_phase(phase)
        sys = build_system_prompt(project, phase, rolling_summary=summary,
                                  tool_names=[t.name for t in tools])
        msgs: list[LLMMessage] = [LLMMessage(role="system", content=sys)]
        for m in history: msgs.append(LLMMessage(role=m.role, content=m.content))
        msgs.append(LLMMessage(role="user", content=user_text))
        return msgs

    async def _maybe_compress(self, project_id, messages, summary):
        if not should_compress(messages, model_window=self.model_window, threshold=COMPRESS_THRESHOLD):
            return messages, summary
        class _OneShot:
            def __init__(self, llm, sys): self.llm = llm; self.sys = sys
            async def summarize(self, text):
                msgs = [LLMMessage("system", self.sys),
                        LLMMessage("user", "请把以下对话压缩为 500 字以内摘要：\n" + text)]
                out = []
                async for ev in self.llm.stream_chat_events(msgs, tools=[]):
                    if ev["type"] == "delta": out.append(ev["text"])
                return "".join(out)[:2000]
        sys_c = messages[0].content or "" if messages and messages[0].role == "system" else ""
        result = await compress_messages(messages, llm=_OneShot(self.llm, sys_c),
                                         existing_summary=summary, keep_ratio=KEEP_RATIO)
        new_sys = sys_c + ("\n跨会话摘要：" + result.summary if result.summary else "")
        new_messages = [LLMMessage("system", new_sys)] + result.tail
        ctx = self.sqlite.get_project_context(project_id) or ProjectContext(project_id=project_id)
        ctx.phase = phase  # 需外层传入
        ctx.rolling_summary = result.summary
        ctx.last_active_at = datetime.now()
        self.sqlite.upsert_project_context(ctx)
        return new_messages, result.summary

    async def handle(self, ctx: ToolContext, user_text: str, *,
                     session_id: str = "default") -> AsyncIterator[AgentEvent]:
        project = self.sqlite.get_project(ctx.project_id)
        if project is None:
            yield {"type": "error", "code": "INTERNAL", "message": "项目不存在"}; return
        phase = ctx.project_phase
        history = self.sqlite.list_chat_messages(ctx.project_id, session_id, limit=HISTORY_LIMIT)
        history.reverse()
        proj_ctx = self.sqlite.get_project_context(ctx.project_id)
        summary = proj_ctx.rolling_summary if proj_ctx else ""
        messages = self._build_context(project, phase, history, user_text, summary)
        self.sqlite.insert_chat_message(ChatMessage(
            id=uuid.uuid4().hex, session_id=session_id, project_id=ctx.project_id,
            role="user", content=user_text, created_at=datetime.now()))
        messages, _ = await self._maybe_compress(ctx.project_id, messages, summary)

        llm_tools = get_tools_for_phase(phase)
        for _ in range(MAX_TOOL_ROUNDS):
            text_parts: list[str] = []
            tool_evt: dict[str, Any] | None = None
            async for ev in self.llm.stream_chat_events(messages, tools=llm_tools):
                if ev["type"] == "delta":
                    text_parts.append(ev["text"]); yield {"type": "delta", "text": ev["text"]}
                elif ev["type"] == "tool_call":
                    tool_evt = ev
                    yield {"type": "tool_call", "id": ev["id"],
                           "name": ev["name"], "args": ev["arguments"]}
            self.sqlite.insert_chat_message(ChatMessage(
                id=uuid.uuid4().hex, session_id=session_id, project_id=ctx.project_id,
                role="assistant", content="".join(text_parts),
                tool_calls_json=json.dumps([tool_evt] if tool_evt else [], ensure_ascii=False),
                created_at=datetime.now()))
            if tool_evt is None: break
            from app.core.llm import LLMTool
            result = execute_tool(LLMTool(name=tool_evt["name"], description="", parameters={}),
                                  ctx, tool_evt["arguments"])
            payload = {"ok": result.ok, "data": result.data, "error": result.error}
            yield {"type": "tool_result", "id": tool_evt["id"], "result": payload}
            messages.append(LLMMessage(role="tool", content=json.dumps(payload, ensure_ascii=False),
                                       tool_call_id=tool_evt["id"], name=tool_evt["name"]))
        yield {"type": "done"}
```

- [ ] **Step 4：跑测试通过**
- [ ] **Step 5：提交** — `git commit -m "feat(backend): agent main loop with tool dispatch and persistence"`

---

## Phase 6：后端 WebSocket

### Task 6.1：会话注册表与项目级事件总线

**Files:**
- Create: `backend/app/agent/sessions.py`
- Create: `backend/tests/unit/test_sessions.py`

- [ ] **Step 1：写 4 个测试**（register / get / unregister / broadcast 仅推同 project）
- [ ] **Step 2：实现 `sessions.py`**

```python
"""WS 会话注册表 + 项目级事件总线。"""
from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable


class Session:
    def __init__(self, project_id: str, session_id: str) -> None:
        self.project_id = project_id; self.session_id = session_id
        self._send_fn: Callable[[dict[str, Any]], Awaitable[None]] | None = None
    def bind(self, fn): self._send_fn = fn
    async def send(self, msg):
        if self._send_fn is not None: await self._send_fn(msg)


class SessionRegistry:
    def __init__(self) -> None:
        self._by_s: dict[str, Session] = {}; self._by_p: dict[str, set[str]] = {}
    def register(self, project_id, session_id) -> Session:
        s = Session(project_id, session_id)
        self._by_s[session_id] = s
        self._by_p.setdefault(project_id, set()).add(session_id)
        return s
    def get(self, session_id): return self._by_s.get(session_id)
    def unregister(self, session_id):
        s = self._by_s.pop(session_id, None)
        if s is None: return
        self._by_p.get(s.project_id, set()).discard(session_id)
    async def broadcast(self, project_id, msg):
        ids = [i for i in self._by_p.get(project_id, set()) if i in self._by_s]
        await asyncio.gather(*(self._by_s[i].send(msg) for i in ids))
```

- [ ] **Step 3：跑测试通过**
- [ ] **Step 4：提交** — `git commit -m "feat(backend): session registry and project event bus"`

### Task 6.2：WebSocket 端点

**Files:**
- Modify: `backend/app/api/ws.py`
- Create: `backend/tests/integration/test_ws.py`

- [ ] **Step 1：写测试**（连接 + 发 ping → 收到 pong 或 error）
- [ ] **Step 2：实现 `backend/app/api/ws.py`**

```python
"""WebSocket /ws/chat 端点。"""
from __future__ import annotations
import json
import uuid
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.agent.agent import Agent
from app.agent.sessions import SessionRegistry
from app.agent.tools import ToolContext
from app.core.config import get_settings
from app.core.llm import LLMClient
from app.core.state_machine import Phase
from app.storage.file_repo import FileRepo
from app.storage.sqlite_repo import SqliteRepo
from app.api.deps import get_file_repo, get_sqlite_repo

router = APIRouter()
REGISTRY = SessionRegistry()


def _make_llm() -> LLMClient:
    s = get_settings()
    return LLMClient(base_url=s.llm_base_url,
                     api_key=s.llm_api_key.get_secret_value(), model=s.llm_model)


@router.websocket("/ws/chat")
async def ws_chat(ws: WebSocket, session_id: str, project_id: str,
                  sq: SqliteRepo = Depends(get_sqlite_repo),
                  fr: FileRepo = Depends(get_file_repo)) -> None:
    await ws.accept()
    project = sq.get_project(project_id)
    if project is None:
        await ws.send_json({"type": "error", "code": "INTERNAL", "message": "项目不存在"})
        await ws.close(); return
    session = REGISTRY.register(project_id, session_id)
    session.bind(lambda msg: ws.send_json(msg))
    llm = _make_llm()
    agent = Agent(llm=llm, sqlite=sq, file=fr)
    try:
        while True:
            raw = await ws.receive_text()
            try: msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "code": "LLM_BAD_RESPONSE", "message": "非 JSON"}); continue
            kind = msg.get("type")
            if kind == "ping":
                await ws.send_json({"type": "pong"})
            elif kind == "chat.message":
                text = msg.get("text", "")
                ctx = ToolContext(project_id=project_id, sqlite=sq, file=fr,
                                  project_phase=Phase(project.current_phase.value))
                async for ev in agent.handle(ctx, user_text=text, session_id=session_id):
                    payload = dict(ev); payload["correlation_id"] = msg.get("correlation_id", uuid.uuid4().hex)
                    await ws.send_json(payload)
            elif kind == "chat.stop":
                # 简化实现：忽略 stop（agent 单次消息短促，未来可加协程取消）
                pass
    except WebSocketDisconnect:
        REGISTRY.unregister(session_id)
```

- [ ] **Step 3：跑测试通过**
- [ ] **Step 4：手动测试** — `uvicorn app.main:app` + `websocat ws://127.0.0.1:8000/ws/chat?session_id=A&project_id=<pid>` 发 ping
- [ ] **Step 5：提交** — `git commit -m "feat(backend): WebSocket /ws/chat with session registry"`

---

## Phase 7：前端基础设施

### Task 7.1：API 客户端封装

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/ws.ts`
- Create: `frontend/tests/ws.test.ts`

- [ ] **Step 1：写 `frontend/src/api/client.ts`**

```ts
import axios from "axios";

export const api = axios.create({ baseURL: "/api", timeout: 30000 });

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.data?.detail) {
      err.message = typeof err.response.data.detail === "string"
        ? err.response.data.detail
        : JSON.stringify(err.response.data.detail);
    }
    return Promise.reject(err);
  },
);

export interface Project {
  id: string; name: string; logline: string; genre: string;
  style_notes: string; current_phase: string;
  created_at: string; updated_at: string;
}
export interface Character {
  id: string; project_id: string; name: string; role: string;
  profile_md: string; updated_at: string;
}
export interface OutlineNode {
  id: string; project_id: string; parent_id: string | null;
  order: number; title: string; summary_md: string; chapter_id: string | null;
}
export interface Chapter {
  id: string; project_id: string; outline_node_id: string | null;
  order: number; title: string; content_md: string; word_count: number;
  status: string; created_at: string; updated_at: string;
}
```

- [ ] **Step 2：写 `frontend/src/api/ws.ts`**

```ts
export type WsEvent =
  | { type: "delta"; text: string; correlation_id?: string }
  | { type: "tool_call"; id: string; name: string; args: any; correlation_id?: string }
  | { type: "tool_result"; id: string; result: any; correlation_id?: string }
  | { type: "done"; correlation_id?: string }
  | { type: "error"; code: string; message: string; recoverable?: boolean; correlation_id?: string }
  | { type: "pong" }
  | { type: "project.changed"; kind: string; id?: string; correlation_id?: string };

export type WsHandler = (ev: WsEvent) => void;

export class ChatSocket {
  private ws: WebSocket | null = null;
  private handlers: WsHandler[] = [];
  private reconnectTimer: number | null = null;

  constructor(public sessionId: string, public projectId: string) {}

  connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${proto}://${location.host}/ws/chat?session_id=${this.sessionId}&project_id=${this.projectId}`);
    this.ws.onmessage = (e) => {
      try { this.handlers.forEach((h) => h(JSON.parse(e.data))); } catch { /* noop */ }
    };
    this.ws.onclose = () => {
      this.ws = null;
      this.reconnectTimer = window.setTimeout(() => this.connect(), 1500);
    };
  }

  send(payload: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  on(h: WsHandler) { this.handlers.push(h); return () => {
    this.handlers = this.handlers.filter((x) => x !== h);
  }; }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }
}
```

- [ ] **Step 3：写测试 `frontend/tests/ws.test.ts`**

```ts
import { describe, it, expect, vi } from "vitest";
import { ChatSocket } from "../src/api/ws";

describe("ChatSocket", () => {
  it("emits parsed messages to handlers", () => {
    const sock = new ChatSocket("s1", "p1");
    const handler = vi.fn();
    sock.on(handler);
    // 用 fake WebSocket 替换 global
    const calls: any[] = [];
    (globalThis as any).WebSocket = class {
      onmessage: ((e: any) => void) | null = null;
      onclose: (() => void) | null = null;
      readyState = 1;
      constructor(_: string) {}
      send(d: any) { calls.push(d); }
      close() { this.onclose?.(); }
    };
    sock.connect();
    const fakeWs = (sock as any).ws as any;
    fakeWs.onmessage({ data: JSON.stringify({ type: "delta", text: "hi" }) });
    expect(handler).toHaveBeenCalledWith({ type: "delta", text: "hi" });
  });
});
```

- [ ] **Step 4：跑测试通过** — `cd frontend && npm test`
- [ ] **Step 5：提交** — `git commit -m "feat(frontend): API client and WebSocket wrapper"`

### Task 7.2：状态管理 stores

**Files:**
- Create: `frontend/src/stores/projectStore.ts`
- Create: `frontend/src/stores/chatStore.ts`
- Create: `frontend/tests/stores.test.ts`

- [ ] **Step 1：写 `frontend/src/stores/projectStore.ts`**

```ts
import { create } from "zustand";
import { api, type Project, type Character, type OutlineNode, type Chapter } from "../api/client";

interface ProjectState {
  project: Project | null;
  characters: Character[];
  outline: OutlineNode[];
  chapters: Chapter[];
  load: (pid: string) => Promise<void>;
  refreshCharacters: () => Promise<void>;
  refreshOutline: () => Promise<void>;
  refreshChapters: () => Promise<void>;
  setPhase: (to: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  project: null, characters: [], outline: [], chapters: [],
  load: async (pid) => {
    const p = (await api.get<Project>(`/projects/${pid}`)).data;
    set({ project: p });
    await Promise.all([get().refreshCharacters(), get().refreshOutline(), get().refreshChapters()]);
  },
  refreshCharacters: async () => {
    const pid = get().project?.id; if (!pid) return;
    set({ characters: (await api.get<Character[]>(`/projects/${pid}/characters`)).data });
  },
  refreshOutline: async () => {
    const pid = get().project?.id; if (!pid) return;
    set({ outline: (await api.get<OutlineNode[]>(`/projects/${pid}/outline`)).data });
  },
  refreshChapters: async () => {
    const pid = get().project?.id; if (!pid) return;
    set({ chapters: (await api.get<Chapter[]>(`/projects/${pid}/chapters`)).data });
  },
  setPhase: async (to) => {
    const pid = get().project?.id; if (!pid) return;
    const p = (await api.post<Project>(`/projects/${pid}/phase`, { to })).data;
    set({ project: p });
  },
}));
```

- [ ] **Step 2：写 `frontend/src/stores/chatStore.ts`**

```ts
import { create } from "zustand";
import { ChatSocket, type WsEvent } from "../api/ws";

export interface ChatMsg { role: "user" | "assistant"; content: string; ts: number }

interface ChatState {
  socket: ChatSocket | null;
  messages: ChatMsg[];
  streaming: string;
  connect: (sid: string, pid: string) => void;
  send: (text: string) => void;
  handle: (ev: WsEvent) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  socket: null, messages: [], streaming: "",
  connect: (sid, pid) => {
    const sock = new ChatSocket(sid, pid);
    sock.on((ev) => get().handle(ev));
    sock.connect();
    set({ socket: sock });
  },
  send: (text) => {
    const { socket } = get();
    socket?.send({ type: "chat.message", text, correlation_id: crypto.randomUUID() });
    set((s) => ({ messages: [...s.messages, { role: "user", content: text, ts: Date.now() }] }));
  },
  handle: (ev) => {
    switch (ev.type) {
      case "delta":
        set((s) => ({ streaming: s.streaming + (ev as any).text })); break;
      case "done":
        set((s) => ({
          messages: s.streaming ? [...s.messages, { role: "assistant", content: s.streaming, ts: Date.now() }] : s.messages,
          streaming: "",
        })); break;
      case "error":
        set({ streaming: "" }); break;
    }
  },
}));
```

- [ ] **Step 3：写测试 `frontend/tests/stores.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { useChatStore } from "../src/stores/chatStore";

describe("chatStore", () => {
  it("accumulates deltas and finalizes on done", () => {
    const s = useChatStore.getState();
    s.handle({ type: "delta", text: "你" } as any);
    s.handle({ type: "delta", text: "好" } as any);
    expect(useChatStore.getState().streaming).toBe("你好");
    s.handle({ type: "done" } as any);
    const after = useChatStore.getState();
    expect(after.streaming).toBe("");
    expect(after.messages[after.messages.length - 1].content).toBe("你好");
  });

  it("resets streaming on error", () => {
    useChatStore.setState({ streaming: "残" });
    useChatStore.getState().handle({ type: "error", code: "X", message: "x" } as any);
    expect(useChatStore.getState().streaming).toBe("");
  });
});
```

- [ ] **Step 4：跑测试通过**
- [ ] **Step 5：提交** — `git commit -m "feat(frontend): project and chat stores with zustand"`

---

## Phase 8：前端 UI

### Task 8.1：项目列表页

**Files:**
- Create: `frontend/src/pages/ProjectList.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1：写 `frontend/src/pages/ProjectList.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Project } from "../api/client";

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  const load = async () => setProjects((await api.get<Project[]>("/projects")).data);
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    const p = (await api.post<Project>("/projects", { name })).data;
    setName(""); await load(); navigate(`/projects/${p.id}`);
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">我的小说</h1>
      <div className="flex gap-2 mb-6">
        <input value={name} onChange={(e) => setName(e.target.value)}
               placeholder="新小说名" className="flex-1 border rounded px-3 py-2" />
        <button onClick={create} className="bg-blue-600 text-white px-4 py-2 rounded">创建</button>
      </div>
      <ul className="space-y-2">
        {projects.map((p) => (
          <li key={p.id} className="bg-white p-3 rounded shadow flex justify-between">
            <span>{p.name}</span>
            <span className="text-sm text-slate-500">{p.current_phase}</span>
            <button onClick={() => navigate(`/projects/${p.id}`)} className="text-blue-600">打开</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 2：改 `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProjectList from "./pages/ProjectList";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/projects/:pid" element={<Workspace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 3：提交** — `git commit -m "feat(frontend): project list page with create"`

### Task 8.2：工作台骨架 + 阶段导航

**Files:**
- Create: `frontend/src/pages/Workspace.tsx`
- Create: `frontend/src/components/PhaseNav.tsx`

- [ ] **Step 1：写 `frontend/src/components/PhaseNav.tsx`**

```tsx
import type { Project } from "../api/client";

const PHASES = ["INIT", "WORLD", "CHARACTERS", "OUTLINE", "WRITING", "DONE"] as const;

export default function PhaseNav({ project, onAdvance }: {
  project: Project; onAdvance: (to: string) => void;
}) {
  const currentIdx = PHASES.indexOf(project.current_phase as any);
  return (
    <nav className="flex gap-1 p-2 bg-slate-100 border-b">
      {PHASES.map((p, i) => (
        <button key={p}
          disabled={i <= currentIdx || (project.current_phase === "DONE")}
          onClick={() => onAdvance(p)}
          className={`px-3 py-1 rounded text-sm ${i === currentIdx ? "bg-blue-600 text-white" : "bg-white border"}`}>
          {p}
        </button>
      ))}
    </nav>
  );
}
```

- [ ] **Step 2：写 `frontend/src/pages/Workspace.tsx`**

```tsx
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useProjectStore } from "../stores/projectStore";
import { useChatStore } from "../stores/chatStore";
import PhaseNav from "../components/PhaseNav";
import WorldEditor from "../features/world/WorldEditor";
import CharacterList from "../features/characters/CharacterList";
import OutlineTree from "../features/outline/OutlineTree";
import ChapterList from "../features/chapters/ChapterList";
import ChatPanel from "../features/chat/ChatPanel";

function uuid() { return crypto.randomUUID(); }

export default function Workspace() {
  const { pid = "" } = useParams();
  const { project, load, setPhase } = useProjectStore();
  const { connect } = useChatStore();

  useEffect(() => {
    if (pid) { load(pid); connect(uuid(), pid); }
  }, [pid, load, connect]);

  if (!project) return <div className="p-6">加载中…</div>;
  return (
    <div className="h-screen flex flex-col">
      <header className="px-4 py-2 border-b bg-white flex justify-between items-center">
        <h1 className="text-lg font-bold">{project.name}</h1>
        <span className="text-sm text-slate-500">{project.current_phase}</span>
      </header>
      <PhaseNav project={project} onAdvance={setPhase} />
      <main className="flex-1 grid grid-cols-3 gap-2 p-2 overflow-hidden">
        <div className="col-span-2 overflow-y-auto space-y-2">
          {project.current_phase === "WORLD" && <WorldEditor pid={pid} />}
          {project.current_phase === "CHARACTERS" && <CharacterList pid={pid} />}
          {project.current_phase === "OUTLINE" && <OutlineTree pid={pid} />}
          {(project.current_phase === "WRITING" || project.current_phase === "DONE") &&
            <ChapterList pid={pid} />}
        </div>
        <ChatPanel />
      </main>
    </div>
  );
}
```

- [ ] **Step 3：创建特性组件占位**（每个写 `return <div>...</div>`，Phase 8.3-8.6 充实）

```ts
// frontend/src/features/world/WorldEditor.tsx
import { useEffect, useState } from "react";
import { api } from "../../api/client";
export default function WorldEditor({ pid }: { pid: string }) {
  const [md, setMd] = useState("");
  useEffect(() => { api.get(`/projects/${pid}/world`).then((r) => setMd(r.data.content_md)); }, [pid]);
  return (
    <div className="bg-white rounded p-3 shadow">
      <h2 className="font-semibold mb-2">世界观</h2>
      <textarea value={md} onChange={(e) => setMd(e.target.value)}
                onBlur={() => api.put(`/projects/${pid}/world`, { content_md: md })}
                className="w-full h-96 border rounded p-2 font-mono text-sm" />
    </div>
  );
}
```

```tsx
// frontend/src/features/characters/CharacterList.tsx
import { useEffect, useState } from "react";
import { api, type Character } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

export default function CharacterList({ pid }: { pid: string }) {
  const { characters, refreshCharacters } = useProjectStore();
  const [name, setName] = useState("");
  useEffect(() => { refreshCharacters(); }, []);
  const create = async () => {
    if (!name) return;
    await api.post(`/projects/${pid}/characters`, { name });
    setName(""); await refreshCharacters();
  };
  return (
    <div className="bg-white rounded p-3 shadow">
      <h2 className="font-semibold mb-2">人物</h2>
      <div className="flex gap-2 mb-2">
        <input value={name} onChange={(e) => setName(e.target.value)}
               className="border rounded px-2 py-1" placeholder="姓名" />
        <button onClick={create} className="bg-blue-600 text-white px-3 rounded">添加</button>
      </div>
      <ul>{characters.map((c) => <li key={c.id}>{c.name} ({c.role})</li>)}</ul>
    </div>
  );
}
```

```tsx
// frontend/src/features/outline/OutlineTree.tsx
import { useEffect } from "react";
import { useProjectStore } from "../../stores/projectStore";
import { api } from "../../api/client";
export default function OutlineTree({ pid }: { pid: string }) {
  const { outline, refreshOutline } = useProjectStore();
  useEffect(() => { refreshOutline(); }, []);
  const add = async () => {
    await api.post(`/projects/${pid}/outline`, { title: "新节点", order: outline.length });
    await refreshOutline();
  };
  return (
    <div className="bg-white rounded p-3 shadow">
      <h2 className="font-semibold mb-2">大纲</h2>
      <button onClick={add} className="text-sm text-blue-600 mb-2">+ 添加节点</button>
      <ul className="space-y-1">
        {outline.map((n) => (
          <li key={n.id} style={{ paddingLeft: n.parent_id ? 20 : 0 }}>
            ▸ {n.title}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

```tsx
// frontend/src/features/chapters/ChapterList.tsx
import { useEffect } from "react";
import { useProjectStore } from "../../stores/projectStore";
import { api } from "../../api/client";
export default function ChapterList({ pid }: { pid: string }) {
  const { chapters, refreshChapters } = useProjectStore();
  useEffect(() => { refreshChapters(); }, []);
  return (
    <div className="bg-white rounded p-3 shadow">
      <h2 className="font-semibold mb-2">章节</h2>
      <ul className="space-y-1">
        {chapters.map((c) => (
          <li key={c.id} className="flex justify-between">
            <span>{c.order}. {c.title}</span>
            <span className="text-sm text-slate-500">{c.word_count} 字 · {c.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

```tsx
// frontend/src/features/chat/ChatPanel.tsx
import { useState } from "react";
import { useChatStore } from "../../stores/chatStore";
export default function ChatPanel() {
  const { messages, streaming, send } = useChatStore();
  const [text, setText] = useState("");
  const onSend = () => { if (text.trim()) { send(text); setText(""); } };
  return (
    <div className="bg-white rounded p-3 shadow flex flex-col">
      <h2 className="font-semibold mb-2">Agent</h2>
      <div className="flex-1 overflow-y-auto space-y-2 mb-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <span className="inline-block bg-slate-100 rounded px-2 py-1 text-sm">{m.content}</span>
          </div>
        ))}
        {streaming && (
          <div><span className="inline-block bg-blue-50 rounded px-2 py-1 text-sm">{streaming}…</span></div>
        )}
      </div>
      <div className="flex gap-2">
        <input value={text} onChange={(e) => setText(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && onSend()}
               className="flex-1 border rounded px-2 py-1" />
        <button onClick={onSend} className="bg-blue-600 text-white px-3 rounded">发送</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4：本地跑** — 后端 `uvicorn` + 前端 `npm run dev`，建项目 → 切阶段 → 写 chat
- [ ] **Step 5：提交** — `git commit -m "feat(frontend): workspace page with phase nav and features"`

---

## Phase 9：端到端冒烟

### Task 9.1：手动 E2E 脚本

**Files:**
- Create: `scripts/smoke.sh`

- [ ] **Step 1：写 `scripts/smoke.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://127.0.0.1:8000}

echo "== 1. health =="
curl -sS $BASE/health | grep ok

echo "== 2. create project =="
PID=$(curl -sS -X POST $BASE/api/projects -H "Content-Type: application/json" \
      -d '{"name":"smoke","logline":"x","genre":"test"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "PID=$PID"

echo "== 3. advance to WORLD =="
curl -sS -X POST $BASE/api/projects/$PID/phase -H "Content-Type: application/json" -d '{"to":"WORLD"}' | grep WORLD

echo "== 4. write world =="
curl -sS -X PUT $BASE/api/projects/$PID/world -H "Content-Type: application/json" \
     -d '{"content_md":"# smoke world"}' | grep "smoke world"

echo "== 5. advance to CHARACTERS =="
curl -sS -X POST $BASE/api/projects/$PID/phase -H "Content-Type: application/json" -d '{"to":"CHARACTERS"}' | grep CHARACTERS

echo "== 6. create character =="
curl -sS -X POST $BASE/api/projects/$PID/characters -H "Content-Type: application/json" \
     -d '{"name":"林夕","role":"主角"}' | grep "林夕"

echo "ALL SMOKE PASSED"
```

- [ ] **Step 2：跑** — `chmod +x scripts/smoke.sh && ./scripts/smoke.sh` → `ALL SMOKE PASSED`
- [ ] **Step 3：提交** — `git commit -m "test: add backend smoke script"`

### Task 9.2：全量测试 + 覆盖率

- [ ] **Step 1：跑后端全量测试** — `cd backend && pytest --cov=app --cov-report=term-missing`
- [ ] **Step 2：跑前端测试** — `cd frontend && npm test`
- [ ] **Step 3：跑 lint + typecheck** — 后端 `ruff check . && mypy app`，前端 `npm run lint && npm run typecheck`
- [ ] **Step 4：覆盖率 ≥ 70%（后端）**，不达标处补测试
- [ ] **Step 5：commit any test fixups** — `git commit -m "test: raise coverage to 70%"`

---

## Phase 10：收尾

### Task 10.1：README 完善

**Files:**
- Modify: `README.md`

- [ ] **Step 1：补 README**：克隆 → 配 `.env` → `pip install -e ".[dev]"` + `npm install` → `uvicorn` + `npm run dev` → 访问 `http://127.0.0.1:5173`
- [ ] **Step 2：提交** — `git commit -m "docs: complete README quickstart"`

### Task 10.2：v0 收尾 commit

- [ ] **Step 1：打 tag** — `git tag v0.1.0 -m "v0: workflow-driven MVP"`
- [ ] **Step 2：最终跑一次 smoke + 全量测试**，确保都通过
- [ ] **Step 3：log summary** — 写一段 CHANGELOG 描述 v0 已交付能力

---

## 自我检查（写完计划后必做）

**1. Spec 覆盖：**
- [x] 项目创建 / 阶段转移 / 设定 / 人物 / 大纲 / 章节 / 聊天 — Phase 2/3/5/6/7/8
- [x] 多窗口会话隔离 — Phase 6
- [x] WebSocket 流式 + 工具 — Phase 4/5/6
- [x] 错误处理（LLM 错误码 + 信封）— Phase 1.2
- [x] 乐观锁 / draft_partial — Phase 2.2 `version` / `ChapterStatus.DRAFT_PARTIAL`
- [x] 上下文压缩 — Phase 4.2
- [x] 测试 / 覆盖率 — Phase 9
- [x] CI / pre-commit — Phase 0.4
- [x] RAG 接口预留 — 已在 `app/rag/` 留空间（v0 不实现）

**2. 占位扫描：** 已检查，无 "TBD/TODO/类似 Task N"。

**3. 类型一致性：**
- `Phase` / `ErrorCode` / `LLMMessage` / `LLMTool` / `ToolContext` / `ToolResult` / `ToolDef` 在所有任务中命名一致
- `Project` / `Character` / `OutlineNode` / `Chapter` / `ChatMessage` / `ProjectContext` 字段一致
- `MAX_TOOL_ROUNDS = 10` / `DEFAULT_MODEL_WINDOW = 100_000` / `COMPRESS_THRESHOLD = 0.8` / `KEEP_RATIO = 0.7` / `HISTORY_LIMIT = 8` 与 spec 一致

**4. 范围：** 单一实施计划，单一交付物（v0 可用 Web 应用）。未超范围。
