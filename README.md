# Novel Agent

> 本地优先的小说创作辅助 Web 应用：单 Agent + 工具，引导式工作流
> （世界观 → 人物 → 大纲 → 章节正文），FastAPI + React。

**接手须知**：本文是项目的"入口 README + 交接手册"。如果你只想看一个东西能跑起来、谁负责什么、下一步该做什么，看完本文件即可。要看设计稿/实现细节，往下挖到 `docs/superpowers/`。

---

## 1. 一句话现状

| 项 | 状态 |
|---|---|
| 后端 pytest | **105 passed**（2026-06-09） |
| 前端 vitest | **11 passed** |
| 后端 lint/typecheck | ruff + mypy（CI 接好） |
| 真实 LLM 冒烟 | `scripts/smoke_llm.py` 跑通（流式章节 + 3 顾问） |
| 当前 v0 目标 | workflow-driven MVP（单 Agent + 5 阶段状态机） |
| 已超 v0 范围 | 流式章节（begin/append/finalize）、3 个顾问 sub-agent、AdvisorPanel UI |

---

## 2. 仓库布局

```
novel-agent/
├── backend/                        # FastAPI + SQLite + OpenAI 兼容 LLM 客户端
│   ├── app/
│   │   ├── main.py                 # 入口 + lifespan + 路由装配
│   │   ├── api/                    # 路由层（参数解析 + 调仓储，不写业务）
│   │   │   ├── projects.py         #   项目 CRUD + phase 切换
│   │   │   ├── world.py            #   世界观 markdown
│   │   │   ├── characters.py       #   人物卡
│   │   │   ├── outline.py          #   大纲树
│   │   │   ├── chapters.py         #   章节 CRUD
│   │   │   ├── chat.py             #   REST 拉历史
│   │   │   ├── ws.py               #   WebSocket /ws/chat
│   │   │   └── advisors.py         #   POST /api/projects/{pid}/advisors/{name}
│   │   ├── core/
│   │   │   ├── config.py           # pydantic-settings，读 .env
│   │   │   ├── llm.py              # OpenAI 兼容客户端（流式 + tool_calls + retry）
│   │   │   ├── state_machine.py    # 5 阶段 + 转移规则
│   │   │   ├── compression.py      # 上下文压缩（80% 触发，保留 70% tail）
│   │   │   └── errors.py           # 协议错误码 + WS error 信封
│   │   ├── agent/
│   │   │   ├── agent.py            # Agent 主循环（流式 delta 实时落库）
│   │   │   ├── tools.py            # 工具注册表 + 阶段门控 + 流式章节三件套
│   │   │   ├── prompts.py          # 各阶段 system prompt 模板
│   │   │   ├── subagents.py        # 3 个顾问 sub-agent（outline/style/reviewer）
│   │   │   └── sessions.py         # WS 会话注册表 + 项目级事件总线
│   │   └── storage/
│   │       ├── models.py           # Pydantic 模型
│   │       ├── sqlite_repo.py      # SQLite CRUD（同步）
│   │       └── file_repo.py        # 磁盘 *.md / *.json
│   ├── tests/
│   │   ├── unit/                   # 105 个测试：state_machine / repos / llm / tools / agent
│   │   └── integration/            # REST + WS 集成测试
│   ├── scripts/
│   │   └── smoke_llm.py            # 真实 LLM 端到端冒烟（流式章节 + 3 顾问）
│   ├── pyproject.toml
│   └── .env.example
├── frontend/                       # React 18 + Vite + TS + Tailwind + zustand
│   ├── src/
│   │   ├── pages/                  # ProjectList / Workspace
│   │   ├── features/
│   │   │   ├── world/ characters/ outline/ chapters/ chat/
│   │   │   └── advisors/AdvisorPanel.tsx
│   │   ├── components/             # PhaseNav / ErrorToast
│   │   ├── api/                    # client.ts (axios) + ws.ts (ChatSocket)
│   │   ├── stores/                 # projectStore / chatStore（zustand）
│   │   ├── App.tsx + main.tsx
│   ├── tests/                      # vitest
│   ├── vite.config.ts              # /api /ws 代理到 127.0.0.1:8000
│   └── package.json
├── docs/superpowers/
│   ├── specs/2026-06-09-novel-agent-design.md   # 完整设计文档
│   └── plans/2026-06-09-novel-agent-impl.md     # 实施计划（带 checkbox）
├── .github/workflows/ci.yml        # 后端 + 前端 CI（只本地，未 push）
├── .pre-commit-config.yaml
└── README.md                        # ← 你正在读
```

### 2.1 分层不变量

- `api/` 只做参数解析和返回，**不写业务**
- `agent/` 不直接读写文件 / DB，**必须经 `storage/`**
- 任何跨模块的全局状态（LLM 客户端、配置、单例）**从 `core/` 取**
- 错误用 `core/errors.py` 的 `ProtocolError` + `ErrorCode`，不要裸抛

---

## 3. 快速启动

### 3.1 环境要求

- Python **3.11+**、Node **20+**
- 任何 OpenAI 兼容 LLM 端点（OpenAI 官方 / 火山方舟 / DeepSeek / 本地 vLLM 都可）
- SQLite（Python 自带）

### 3.2 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # 填 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
pytest                        # 105 tests
uvicorn app.main:app --reload # 127.0.0.1:8000
```

`.env` 必填项：

```bash
LLM_BASE_URL=https://api.openai.com/v1   # 或你用的供应商
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
DATA_DIR=./data
```

### 3.3 前端

```bash
cd frontend
npm install
npm test                       # 11 tests
npm run dev                    # http://127.0.0.1:5173
```

Vite dev server 已经把 `/api` 和 `/ws` 代理到 `127.0.0.1:8000`，开两个终端跑就能用。

### 3.4 真实 LLM 冒烟

最快验证全链路的方式（不依赖前端，纯后端）：

```bash
cd backend && source .venv/bin/activate
python scripts/smoke_llm.py
```

预期输出：
- ✓ LLM 调用 `begin_chapter` 工具 + 流式输出正文 + `finalize_chapter`，
  章节落到 `backend/data/projects/smoke-*/chapters/0001_*.md`
- ✓ 三个顾问 sub-agent（大纲 / 风格 / 评审）都返回 ≥ 1 句实质建议
- 测试结束后自动清理 smoke 项目文件

### 3.5 CI

`.github/workflows/ci.yml` 跑 ruff + mypy + pytest + 前端 lint/typecheck/test。
**注意**：当前只本地存在，push 时 PAT 缺 `Workflows: write` 权限。补一个 PAT 就能启用。

---

## 4. 架构与接口

### 4.1 阶段状态机

```
INIT ─► WORLD ─► CHARACTERS ─► OUTLINE ─► WRITING ─► DONE
  │      │           │            │          │
  └──────┴───────────┴────────────┴──────────┘
                任意阶段可回退修订
```

定义在 [`backend/app/core/state_machine.py`](backend/app/core/state_machine.py)。

- **向前一格合法**（`to = from + 1`）
- **向后任意格合法**（用户改主意）
- **自转移非法**（`WORLD → WORLD` 拒绝）
- **跳级非法**（`INIT → CHARACTERS` 拒绝）
- API 层 400 拒绝；agent 越权调工具时工具层抛 `PermissionError`

### 4.2 REST API

所有路径前缀 `/api`。完整列表见 [`docs/superpowers/specs/...-design.md` §3.1](docs/superpowers/specs/2026-06-09-novel-agent-design.md)。
下面是高频用的：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET/POST/DELETE` | `/projects` | 项目列表/创建/删除 |
| `GET/PATCH` | `/projects/{pid}` | 项目详情/改元信息 |
| `POST` | `/projects/{pid}/phase` | `{to: "WORLD"}` 切阶段 |
| `GET/PUT` | `/projects/{pid}/world` | 世界观 markdown |
| `GET/POST` | `/projects/{pid}/characters` | 人物列表/新增 |
| `GET/PATCH/DELETE` | `/projects/{pid}/characters/{cid}` | |
| `GET/POST` | `/projects/{pid}/outline` | 大纲节点 |
| `GET` | `/projects/{pid}/chapters` | 章节列表 |
| `GET/PATCH` | `/projects/{pid}/chapters/{chid}` | |
| `GET` | `/projects/{pid}/chat/history?session_id=...` | 拉历史 |
| **`POST`** | **`/projects/{pid}/advisors/{outline_expert\|style_expert\|reviewer}`** | 顾问 sub-agent REST（v0 新增） |

### 4.3 WebSocket 协议

单一端点：`/ws/chat?session_id=<uuid>&project_id=<pid>`

信封（双向通用）：
```json
{ "type": "...", "correlation_id": "uuid", "payload": { ... } }
```

客户端 → 服务端：

| type | payload |
|---|---|
| `chat.message`  | `{ text: string }` |
| `chat.stop`     | `{}`（中断当前生成） |
| `tool.approve`  | `{ tool_call_id, approved }` |
| `ping`          | `{}` |

服务端 → 客户端：

| type | payload |
|---|---|
| `chat.delta`       | `{ text }`（增量 token） |
| `chat.tool_call`   | `{ id, name, args }` |
| `chat.tool_result` | `{ id, ok, result \| error }` |
| `chat.done`        | `{ message_id, usage }` |
| `agent.suggest`    | `{ text, actions? }` |
| `project.changed`  | `{ kind, id }`（跨窗口广播） |
| `error`            | `{ code, message, recoverable }` |
| `pong`             | `{}` |

实现见 [`backend/app/api/ws.py`](backend/app/api/ws.py) + [`agent/sessions.py`](backend/app/agent/sessions.py)。

### 4.4 Agent 工具集（按阶段）

工具在 [`backend/app/agent/tools.py`](backend/app/agent/tools.py) 注册，由 `allowed_phases` 门控。

| 阶段 | 工具 |
|---|---|
| WORLD      | `upsert_world_doc` / `read_world_doc` |
| CHARACTERS | `create_character` / `update_character` / `add_relationship` / `list_characters` |
| OUTLINE    | `create_outline_node` / `update_outline_node` / `move_outline_node` / `list_outline` |
| WRITING    | `create_chapter` / **`begin_chapter`** / **`append_to_chapter`** / **`finalize_chapter`** / `read_chapter` / `read_outline` / `read_characters` |
| 任意       | `advance_phase` / `read_project_summary` / `set_rolling_summary` |

**流式章节三件套**（v0 后加）：
1. `begin_chapter({title, order, outline_node_id?})` → 状态 `DRAFT_PARTIAL`，Agent 跟踪 `streaming_chapter_id`
2. Agent 后续的 `chat.delta` 每个 token **实时落盘**（DB + `0001_*.md`）
3. `finalize_chapter({chapter_id})` → 状态 `DRAFT`，跳出 Agent loop

### 4.5 数据模型 & 存储策略

| 数据 | 落点 | 理由 |
|---|---|---|
| `content_md`（章节、设定、人物） | 磁盘 `*.md` | 人类可读、可 diff、可备份 |
| 元信息（id/order/parent/word_count/状态） | SQLite | 关系查询、列表、排序、统计 |
| 聊天原文 | SQLite `chat_messages` | 持久化，支持历史回溯 |
| 滚动摘要 | SQLite `project_context` | 项目级、跨会话 |

每项目目录布局（`backend/data/projects/<pid>/`）：
```
world.md
characters/<cid>.json
outline.json                # 整树快照
chapters/0001_<title>.md
chapters/0002_<title>.md
...
```

### 4.6 顾问 sub-agent（v0 后加）

3 个 sub-agent 调同一个 LLM，但用不同系统提示侧重不同维度：

| Advisor | 用途 |
|---|---|
| `outline_expert`   | 检查大纲结构、伏笔、节奏 |
| `style_expert`     | 检查文风一致性（参数带原文 focus） |
| `reviewer`         | 一致性 / 人设 / 设定自洽检查 |

入口：REST（前端用）+ 函数（Agent 调用）。实现见 [`agent/subagents.py`](backend/app/agent/subagents.py)。

---

## 5. 设计决策与理由

| 决策 | 选择 | 理由 | 细节 |
|---|---|---|---|
| 通信协议 | REST + WebSocket | 多窗口、双向、跨窗口广播需要 WS；纯 SSE 推不出跨窗口事件 | spec §3 |
| Agent 框架 | 手写最小循环 | 依赖少、可控、便于将来扩 | spec §6.4 |
| 大纲结构 | 树形（卷/幕/章/节） | 长篇需要分层 | spec §4.4 |
| 聊天持久化 | SQLite（不是仅内存） | 用户要求历史回溯 | spec §4.6 |
| 章节失败恢复 | 保留 `draft_partial`（不自动回滚） | 用户成果优先，手动决定 | spec §8.2 |
| 存储分工 | md/json + SQLite | 既可读可备份，又有结构化查询 | spec §5 |
| 状态机 | 5 阶段 + 任意向前一格 + 任意向后 | 引导式工作流但允许回退 | spec §6.1 |
| 上下文压缩 | 取最早 30% → 500 字 summary → 保留 70% tail | 80% 阈值触发 | spec §8.3 + `core/compression.py` |
| 流式章节 | begin/append/finalize 三件套 + Agent 自动跟踪 | 不需要 LLM 显式调 append；每个 delta 直接落盘 | 本 README §4.4 + `agent/agent.py` |
| LLM 客户端 | OpenAI 兼容 SDK（httpx 裸调） | 跨供应商；可注入 `_transport` mock 测试 | `core/llm.py` |
| 测试 LLM | 写一个 `FakeTransport`，喂 chunk 序列 | 让 Agent 循环跑起来而不依赖真 LLM | `tests/unit/test_agent.py` |

---

## 6. 状态与 TODO

### 6.1 已完成（v0 全部能力 + 几个超 v0）

- ✅ 后端：5 阶段状态机、SQLite + 文件双仓、CRUD REST、WebSocket 流式 + 工具
- ✅ Agent：流式 delta 落库、上下文压缩、10 轮上限、可中断
- ✅ 流式章节：`begin_chapter` / `append_to_chapter` / `finalize_chapter` 工具链
- ✅ 顾问：3 个 sub-agent（outline_expert / style_expert / reviewer）
- ✅ 前端：ProjectList / Workspace / PhaseNav / 4 个特性组件 / ChatPanel / **AdvisorPanel**
- ✅ 真实 LLM 冒烟脚本 + 105 + 11 测试全绿
- ✅ REST 顾问端点（前端可用，CLI 也可调）

### 6.2 范围外（见 spec §10，不在 v0 任务）

- ❌ RAG（接口留了 `app/rag/retriever.py: NoopRetriever`）
- ❌ 评审 agent 的"自动打分"
- ❌ 多用户实时协作
- ❌ 导出 epub / docx
- ❌ 插件化工具注册
- ❌ 移动端 / SSR

### 6.3 已知技术债 / 风险

- **`chat.stop` 当前是 no-op**：agent 单次消息短促没真接，WS 协程取消未实现（spec §6.4 留口子）
- **大上下文压缩未带持久化测试**：`_maybe_compress` 在 `agent/agent.py` 里有，但缺专门单测；只是冒烟脚本间接验证
- **CI workflow 未 push**：`.github/workflows/ci.yml` 本地有，push 需要 PAT `Workflows: write`
- **错误 `tool_call_id` 重试**：LLM 返回 tool_call 但 `streaming_chapter_id` 已 finalize 的话，agent 会用错 id；目前没强校验
- **TypeScript `noUnusedLocals=true`**：可能误伤未来代码

### 6.4 下一步（建议顺序）

1. **CI 启用**（补 PAT + push workflow）
2. **`chat.stop` 协程取消**（~50 行）
3. **RAG v0.1**：Chroma + 把 `Retriever` 接到 `read_*` 工具
4. **评审 sub-agent 自动化**：用 reviewer 检查每章一致性
5. **导出 epub**：基于磁盘 markdown 直接跑 pandoc

---

## 7. 调试与运维技巧

### 7.1 看数据

```bash
# 项目文件（直接 ls）
ls backend/data/projects/<pid>/chapters/

# SQLite 原始查询
sqlite3 backend/data/novel.db "SELECT id, name, current_phase, updated_at FROM projects ORDER BY updated_at DESC;"

# 某个项目的最近 8 条聊天
sqlite3 backend/data/novel.db "SELECT role, content, substr(created_at,1,19) FROM chat_messages WHERE project_id='<pid>' AND session_id='<sid>' ORDER BY created_at DESC LIMIT 8;"
```

### 7.2 Agent 跑偏排查

1. 打开 `backend/data/projects/<pid>/world.md` 看设定是否合理
2. 看 `project_context.rolling_summary` 是否已经丢了关键设定
3. 跑 `python -c "from app.agent.prompts import build_system_prompt; print(build_system_prompt(...))"` 检查 prompt 实际内容
4. 跑 `scripts/smoke_llm.py` 同 prompt 看是否复现

### 7.3 LLM 端点换供应商

只需改 `.env` 三个字段，**不需要改代码**。验证：
```bash
cd backend && source .venv/bin/activate
python -c "from app.core.config import get_settings; s = get_settings(); print(s.llm_base_url, s.llm_model)"
```

### 7.4 重新跑流式章节测试

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/unit/test_agent.py -v
```

### 7.5 把所有测试 + 类型 + 真实 LLM 一起跑

```bash
cd backend && source .venv/bin/activate
pytest                                       # 单元 + 集成
ruff check . && mypy app                     # 静态
python scripts/smoke_llm.py                  # 真实 LLM
cd ../frontend && npm test && npm run typecheck
```

---

## 8. 远程与许可

- 远程：<https://github.com/longzhu0725/novel-agent>
- 许可证：MIT
- 详细设计：[`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](docs/superpowers/specs/2026-06-09-novel-agent-design.md)
- 实施计划（带 checkbox 历史）：[`docs/superpowers/plans/2026-06-09-novel-agent-impl.md`](docs/superpowers/plans/2026-06-09-novel-agent-impl.md)

---

**最后更新**：2026-06-09 — 增加了流式章节 + 顾问 sub-agent + AdvisorPanel 章节。
