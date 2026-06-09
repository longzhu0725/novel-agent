# Novel Agent

辅助完成小说创作的本地优先 Web 应用。单 Agent + 工具，引导式工作流：世界观 → 人物 → 大纲 → 章节正文。

## 状态

v0 已就绪：后端 84 测试全绿，前端骨架可运行。详见 [`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](docs/superpowers/specs/2026-06-09-novel-agent-design.md) 与 [`docs/superpowers/plans/2026-06-09-novel-agent-impl.md`](docs/superpowers/plans/2026-06-09-novel-agent-impl.md)。

## 技术栈

- **后端**：Python 3.11+, FastAPI, SQLite, OpenAI 兼容 LLM 客户端
- **前端**：React 18, TypeScript, Vite, Tailwind, zustand
- **通信**：REST + WebSocket（多窗口 / 会话隔离 / 双向）
- **存储**：本地 Markdown / JSON + SQLite（聊天持久化、滚动摘要）

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 填入 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
python -m pytest -q
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm test
npm run dev   # http://127.0.0.1:5173
```

Vite dev server 已经把 `/api` 和 `/ws` 代理到 `127.0.0.1:8000`。

## 仓库

远程：<https://github.com/longzhu0725/novel-agent>

## 文档

- 设计文档：[`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](docs/superpowers/specs/2026-06-09-novel-agent-design.md)
- 实施计划：[`docs/superpowers/plans/2026-06-09-novel-agent-impl.md`](docs/superpowers/plans/2026-06-09-novel-agent-impl.md)

## 许可证

MIT
