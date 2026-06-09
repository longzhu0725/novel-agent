# Novel Agent — 设计文档

- **日期**：2026-06-09
- **状态**：v0 设计稿（待 review）
- **范围**：小说创作辅助 agent 的首个可交付版本

## 1. 概述

构建一个本地优先的 Web 应用，通过单 Agent + 工具的方式，辅助用户完成从世界观、人物、大纲到章节正文的小说创作全流程。

### 1.1 目标

- 用户能在引导式工作流中完成一部长篇小说的骨架与正文
- Agent 能主动读写项目素材（设定、人物、大纲、章节），并在长对话中保持一致性
- 多窗口可同时打开同一项目，会话彼此隔离
- LLM 提供方可在 `.env` 中自由配置（OpenAI 兼容端点）
- 数据落盘可读、可 diff、可备份

### 1.2 非目标（v0）

- 多人实时协作（光标同步、冲突协同编辑）
- 自动质量评审 / 文学性打分
- 内置 RAG（仅留接口与配置开关，实现 v0.1 再说）
- 多 Agent 编排（架构预留，v0 只做单 Agent）
- 移动端适配、SSR、SEO

## 2. 架构与仓库布局

单仓，前后端分离，Python 后端 + React 前端。

```
novel-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口，挂载路由 + WS
│   │   ├── api/                   # 路由层
│   │   │   ├── projects.py
│   │   │   ├── characters.py
│   │   │   ├── outline.py
│   │   │   ├── chapters.py
│   │   │   ├── chat.py            # REST 部分（历史查询）
│   │   │   └── ws.py              # WebSocket /ws/chat
│   │   ├── core/
│   │   │   ├── config.py          # .env 读取
│   │   │   ├── llm.py             # OpenAI 兼容客户端（流式 + 非流式）
│   │   │   └── state_machine.py   # 阶段定义、转移规则
│   │   ├── agent/
│   │   │   ├── agent.py           # Agent 主循环
│   │   │   ├── tools.py           # 工具函数与 JSON Schema
│   │   │   ├── prompts/           # 各阶段系统提示模板
│   │   │   └── sessions.py        # WS 会话状态
│   │   ├── storage/
│   │   │   ├── file_repo.py       # 磁盘文件读写
│   │   │   ├── sqlite_repo.py     # SQLite CRUD
│   │   │   └── models.py          # Pydantic 模型
│   │   ├── rag/
│   │   │   └── retriever.py       # 抽象接口 + NoopRetriever 占位
│   │   └── errors.py              # 协议错误码与信封
│   ├── data/                      # 运行时数据（git ignore）
│   │   └── projects/              # 每项目一个子目录
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ProjectList.tsx
│   │   │   └── Workspace.tsx
│   │   ├── features/
│   │   │   ├── world/             # 世界观编辑
│   │   │   ├── characters/        # 人物卡
│   │   │   ├── outline/           # 大纲树
│   │   │   ├── chapters/          # 章节编辑器
│   │   │   └── chat/              # Agent 聊天面板
│   │   ├── components/
│   │   ├── api/                   # 后端封装（REST + WS 客户端）
│   │   ├── stores/                # zustand
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── docs/
│   └── superpowers/
│       ├── specs/                 # 设计文档
│       └── plans/                 # 实施计划
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
└── LICENSE
```

### 2.1 后端分层不变量

- `api/` 只做参数解析与返回
- `agent/` 不直接读写文件，必须经 `storage/`
- 任何跨模块的全局状态（如 LLM 客户端、配置）从 `core/` 取

## 3. 通信

### 3.1 REST

用于非流式、CRUD 类操作：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET    | `/api/projects`                     | 项目列表 |
| POST   | `/api/projects`                     | 创建项目 |
| GET    | `/api/projects/{id}`                | 项目详情 |
| PATCH  | `/api/projects/{id}`                | 更新元信息 |
| DELETE | `/api/projects/{id}`                | 删除项目 |
| POST   | `/api/projects/{id}/phase`          | 切换 phase |
| GET    | `/api/projects/{id}/world`          | 读世界观 |
| PUT    | `/api/projects/{id}/world`          | 写世界观 |
| GET    | `/api/projects/{id}/characters`     | 人物列表 |
| POST   | `/api/projects/{id}/characters`     | 新建人物 |
| GET    | `/api/projects/{id}/chat/history`   | 拉取历史消息（分页） |
| GET    | `/api/projects/{id}/characters/{cid}`        | 人物详情 |
| PATCH  | `/api/projects/{id}/characters/{cid}`        | 更新人物 |
| DELETE | `/api/projects/{id}/characters/{cid}`        | 删除人物 |
| GET    | `/api/projects/{id}/outline`                 | 大纲树 |
| POST   | `/api/projects/{id}/outline`                 | 创建节点 |
| PATCH  | `/api/projects/{id}/outline/{nid}`           | 更新节点 |
| DELETE | `/api/projects/{id}/outline/{nid}`           | 删除节点 |
| GET    | `/api/projects/{id}/chapters`                | 章节列表 |
| GET    | `/api/projects/{id}/chapters/{chid}`         | 章节详情 |
| PATCH  | `/api/projects/{id}/chapters/{chid}`         | 更新章节元信息 |

### 3.2 WebSocket

单一端点：`/ws/chat?session_id=...&project_id=...`

握手时携带两个 key，后端据此隔离会话。

**消息信封**（双向通用）：

```json
{
  "type": "<event_type>",
  "correlation_id": "uuid",
  "payload": { ... }
}
```

**客户端 → 服务端**：

| type | payload |
|---|---|
| `chat.message`   | `{ text: string }` |
| `chat.stop`      | `{}`（中断当前生成） |
| `tool.approve`   | `{ tool_call_id: string, approved: bool }` |
| `ping`           | `{}`（保活） |

**服务端 → 客户端**：

| type | payload |
|---|---|
| `chat.delta`        | `{ text: "..." }`（增量 token） |
| `chat.tool_call`    | `{ id, name, args }` |
| `chat.tool_result`  | `{ id, ok, result | error }` |
| `chat.done`         | `{ message_id, usage }` |
| `agent.suggest`     | `{ text, actions?: [...] }`（agent 主动建议） |
| `project.changed`   | `{ kind: "character" | "outline" | "chapter" | "world", id }`（跨窗口广播） |
| `error`             | `{ code, message, recoverable }` |
| `pong`              | `{}` |

### 3.3 多窗口会话隔离

- `session_id` 由前端生成（uuid，挂 localStorage），同一浏览器 tab 一份
- 服务端维护 `sessions: dict[session_id, Session]`
- 项目级事件总线 `bus: dict[project_id, set[Session]]` 用于跨窗口广播
- 同一 `session_id` 重连：旧 session 优雅关闭，未发送完的 delta 迁移到新连接

## 4. 数据模型

### 4.1 Project

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str (uuid) | 主键 |
| name | str | 小说名 |
| logline | str | 一句话简介 |
| genre | str | 类型 |
| style_notes | str (md) | 文风备忘 |
| current_phase | enum | INIT / WORLD / CHARACTERS / OUTLINE / WRITING / DONE |
| storage_dir | str | 相对 `backend/data/projects/` 的子目录名 |
| created_at, updated_at | datetime | |

### 4.2 WorldDoc

| 字段 | 类型 | 说明 |
|---|---|---|
| project_id | str | 外键，PK 的一部分 |
| content_md | str | 整段 markdown |
| version | int | 乐观锁 |

### 4.3 Character

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str (uuid) | 主键 |
| project_id | str | |
| name | str | |
| role | str | 主角/反派/配角 |
| profile_md | str | 自由格式 md |
| updated_at | datetime | |

`CharacterRelationship`（独立表）：

| 字段 | 类型 |
|---|---|
| id | uuid |
| project_id | str |
| source_id | str（人物 id） |
| target_id | str（人物 id） |
| type | str（如 "师父"、"仇人"） |
| note | str |

### 4.4 OutlineNode（树形）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str (uuid) | |
| project_id | str | |
| parent_id | str \| None | 父节点（卷/幕/章/节） |
| order | int | 同级排序 |
| title | str | |
| summary_md | str | 节点内容/摘要 |
| chapter_id | str \| None | 关联章节（叶子节点才有） |

### 4.5 Chapter

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str (uuid) | |
| project_id | str | |
| outline_node_id | str \| None | |
| order | int | 章节号 |
| title | str | |
| content_md | str | 正文 |
| word_count | int | 写入时计算 |
| status | enum | `draft` / `draft_partial` / `reviewing` / `final` |
| created_at, updated_at | datetime | |

### 4.6 ChatMessage（持久化）

| 字段 | 类型 |
|---|---|
| id | uuid |
| session_id | str |
| project_id | str |
| role | enum：`system` / `user` / `assistant` / `tool` |
| content | str |
| tool_calls_json | str（JSON 序列化） |
| created_at | datetime |

### 4.7 ProjectContext

| 字段 | 类型 | 说明 |
|---|---|---|
| project_id | str | PK |
| phase | enum | 冗余存储当前阶段（与 projects 表一致，避免 join） |
| rolling_summary | str | 长对话压缩摘要 |
| last_active_at | datetime | |

## 5. 存储策略

| 数据 | 落点 | 理由 |
|---|---|---|
| `content_md`（章节、设定、大纲详写） | 磁盘 `*.md` | 人类可读、可 diff、可备份 |
| 元信息（id/order/parent/关系/word_count/状态） | SQLite | 关系查询、列表、排序、统计 |
| 聊天原文 | SQLite `chat_messages` | 持久化，支持历史回溯 |
| 滚动摘要 | SQLite `project_context` | 项目级、跨会话 |

文件目录布局（每个项目）：

```
backend/data/projects/<project_id>/
├── world.md
├── characters/<character_id>.json
├── outline.json                  # 大纲树整体快照（方便一次性读取）
└── chapters/
    ├── 0001_<title>.md
    ├── 0002_<title>.md
    └── ...
```

仓储层只暴露**领域方法**（如 `create_chapter`、`list_characters_by_project`），不向上层暴露 SQL/文件路径。

## 6. Agent 设计

### 6.1 状态机

```
INIT ──► WORLD ──► CHARACTERS ──► OUTLINE ──► WRITING ──► DONE
   │        │            │            │           │
   └────────┴────────────┴────────────┴───────────┘
                 任意阶段可回退修订
```

- 阶段定义与合法转移集中在 `core/state_machine.py`
- 非法转移：API 层 400 拒绝；agent 想越权调工具：工具层抛 `PermissionError`
- 进入 WRITING 阶段后允许向前回退到任意阶段（用户改主意）；离开 DONE 回到 WRITING 视为"二稿"

### 6.2 系统提示

每个阶段一个 `prompts/<phase>.md` 模板，运行时填充：

- 项目元信息（name / logline / genre / style_notes）
- `rolling_summary`
- 当前可用工具列表
- 该阶段的目标、约束、推荐工作流

### 6.3 工具集（按阶段）

| 阶段 | 工具 |
|---|---|
| WORLD      | `upsert_world_doc` / `read_world_doc` |
| CHARACTERS | `create_character` / `update_character` / `add_relationship` / `list_characters` |
| OUTLINE    | `create_outline_node` / `update_outline_node` / `move_outline_node` / `list_outline` |
| WRITING    | `create_chapter` / `append_to_chapter` / `rewrite_chapter` / `read_chapter` / `read_outline` / `read_characters` |
| 任意       | `advance_phase` / `read_project_summary` / `set_rolling_summary` |

工具在系统提示中以 JSON Schema 描述，agent 调出 `tool_call` 后由后端执行。

### 6.4 Agent 主循环

```python
async def handle_message(session, project, user_text):
    history = load_recent_messages(project.id, session.id, limit=8)
    messages = build_context(project, session, history, user_text)
    
    for round in range(MAX_TOOL_ROUNDS):  # 10
        async for delta in llm.stream(messages, tools=current_tools):
            ws.send({type: "chat.delta", text: delta})
        
        if assistant_issued_tool_call:
            ws.send({type: "chat.tool_call", ...})
            result = await execute_tool(tool_call, project)
            ws.send({type: "chat.tool_result", ...})
            messages.append(tool_result_message)
            continue  # 继续下一轮让 LLM 看到结果
        else:
            break  # 自然结束
    
    save_messages(messages)  # 全部落 SQLite
    update_rolling_summary_if_needed(project)
    ws.send({type: "chat.done", ...})
```

护栏：

- **轮数上限**：10 轮 tool call
- **总 token 上限**：单次 WS 消息 100k；接近时强制压缩
- **单轮超时**：LLM 单次流 60s 切断
- **可中断**：`chat.stop` 触发 `asyncio.CancelledError`

## 7. 关键数据流

### 7.1 创建项目 → 写世界观

```
POST /api/projects
  →  sqlite_repo.insert(project) + file_repo.mkdir(storage_dir) + 写空 world.md
  →  返回 {id, current_phase: INIT}
POST /api/projects/{id}/phase  {to: WORLD}
  →  state_machine.assert_legal_transition
  →  切换 phase
前端加载工作台，phase 指示器切到 WORLD
用户在 chat 面板发："帮我写个赛博朋克世界观，主题是记忆交易"
  →  WS /ws/chat
  →  agent 读 world.md 模板 → LLM 流式输出 + 调用 upsert_world_doc
  →  world.md 落盘 + SQLite 更新 version
```

### 7.2 撰写章节

```
用户在 chat 面板发："写第一章，5000 字"
  →  WS /ws/chat
  →  agent 加载上下文：阶段提示 + 项目元信息 + 大纲相关节点 + 涉及人物摘要 + 最近 8 条消息 + rolling_summary
  →  LLM 流式返回：
       1. chat.delta（解释写作计划）
       2. chat.tool_call(read_outline) → 工具执行 → 结果回灌
       3. chat.tool_call(create_chapter) → 工具执行 → 章节初稿落盘
       4. chat.tool_call(append_to_chapter) × N → 流式追加
       5. chat.delta（写作说明 / 收尾）
  →  chat.done
前端：章节列表自动刷新（订阅 project.changed 事件），可点开查看
```

### 7.3 多窗口会话隔离

```
窗口 1  WS.connect(session_id=A, project_id=P)  →  Session(A) 入注册表
窗口 2  WS.connect(session_id=B, project_id=P)  →  Session(B) 入注册表

窗口 1 发 "写第一章"
  →  server 找 Session(A)
  →  agent 处理 → 推送给 Session(A) 的 WS
  →  不影响 Session(B)
窗口 1 通过工具改了人物卡
  →  工具成功 → bus.broadcast(P, {type: "project.changed", kind: "character"})
  →  Session(A) 和 Session(B) 都收到
  →  窗口 2 人物面板可选择刷新
```

## 8. 错误处理

### 8.1 分层

| 层 | 错误 | 应对 |
|---|---|---|
| LLM | 网络超时 / 5xx / rate limit | 指数退避重试 3 次（1s/3s/9s）；仍失败 → "模型服务暂不可用" |
| LLM | 401 / 403 | 不重试，提示检查 `.env` 中 `LLM_API_KEY` |
| LLM | context_too_long | 触发**上下文压缩**（取最早 30% → 500 字 summary → 重发） |
| LLM | 解析失败 / 拒绝回答 | 原始结果回灌 LLM 让它按规范重写，最多 2 次 |
| Tool | 参数校验失败 | 不落盘，错误回灌 LLM 让它修正 |
| Tool | 执行异常（IO/DB） | 工具结果带 `error` 字段返回给 LLM |
| State | 非法 phase 转移 | API 400 拒绝；agent 越权 → `PermissionError` |
| WS | 客户端中途断 | 取消 agent 协程；未发送内容并入 `rolling_summary` |
| WS | 同一 session_id 重连 | 旧 session 关闭，delta 迁移 |
| Storage | 并发写冲突 | 乐观锁（`updated_at` 比对），UI 弹"谁后改以谁为准"对话框 |
| Storage | 磁盘满 / 权限 | 整条 agent 操作回滚（事务） |
| 前端 | 表单/API 错 | axios 拦截器 toast；WS 错误走专用错误条 |

### 8.2 章节撰写的事务性

- 每次 `append_to_chapter` 视为一个 checkpoint（每段独立落盘）
- 流式追加中失败：chapter 状态置为 `draft_partial`，前端标黄
- 用户决定续写或回滚到上一个 `final`
- 失败不自动回滚已写段落（保留用户成果）

### 8.3 上下文压缩

```
触发：context > 80% model_window
动作：
  1. 取最早 30% 消息
  2. 调 LLM 生成 500 字 summary
  3. summary 追加到 ProjectContext.rolling_summary
  4. 用 summary + 最近 70% 消息重发
```

### 8.4 协议错误信封

```json
{
  "type": "error",
  "correlation_id": "...",
  "code": "TOOL_EXEC_FAILED",
  "message": "写文件失败：磁盘空间不足",
  "recoverable": true
}
```

前端按 `code` 决定 UI 表现（toast / 对话框 / 重连提示）。

### 8.5 全局兜底

每个 API 路由与 WS 处理器最外层包 try/except，未知错误打 ERROR 日志（含 stack + correlation_id），返回通用"内部错误"，不暴露实现细节。

## 9. 测试

### 9.1 后端（pytest）

| 类别 | 内容 | 方式 |
|---|---|---|
| 单元 - 状态机 | 合法/非法 phase 转移全枚举 | 表驱动 |
| 单元 - 仓储 | FileRepo / SqliteRepo CRUD、关系查询、乐观锁冲突 | tmp dir + 内存 SQLite |
| 单元 - 工具 | 入参校验、执行路径、错误返回 | mock 仓储 |
| 单元 - LLM 客户端 | 流式解析、retry、context_too_long 触发压缩 | mock httpx |
| 单元 - 上下文压缩 | 给定对话历史，验证 summary 注入 + 重发 | mock LLM |
| 集成 - HTTP | REST 端点 happy/error path | TestClient |
| 集成 - WS | 连 → 发 → 收 delta → 收 done / 中途断 / 重连 | TestClient + asyncio |
| 集成 - Agent 端到端 | mock LLM 跑完整 tool_call + final_answer 流程 | 真实 agent 循环 + 真实仓储，断言最终文件/SQLite 状态 |

**Mock LLM 策略**：写一个 `FakeLLM` 类，喂入"消息→响应"序列（含 tool_call + final_answer），让 agent 循环跑起来。

### 9.2 前端

| 类别 | 内容 | 方式 |
|---|---|---|
| 单元 - 组件 | PhaseNav / CharacterCard / ChapterEditor / ChatPanel | vitest + @testing-library/react |
| 单元 - stores | zustand store action 正确性 | vitest |
| 集成 - API 封装 | axios/WS 序列化、错误处理 | vitest + msw |
| E2E | 创建项目 → 全阶段 → 写完一章 happy path | Playwright（v0 末决定） |

### 9.3 不测什么

- LLM 输出质量
- 性能基准
- 视觉回归
- 多浏览器兼容

### 9.4 质量门禁

| 项 | 工具 | 触发 |
|---|---|---|
| 格式化 | ruff format / prettier | pre-commit + CI |
| Lint | ruff / eslint | pre-commit + CI |
| 类型 | mypy / tsc --noEmit | CI |
| 测试 | pytest / vitest | CI，必过 |
| 覆盖率 | pytest-cov，后端 ≥ 70% | CI 报告 |

## 10. 未来扩展（不在 v0 范围）

- **RAG**：v0.1 引入 Chroma/Qdrant，内嵌或本地服务；`Retriever` 接口已留
- **多 Agent 编排**：v0.2 拆分为大纲师 / 人物师 / 写作师 / 评审师
- **评审 agent**：自动跑一致性检查、伏笔提醒、文风统一
- **导出**：导出整书为 epub / docx
- **协作**：多用户实时协作（届时换 CRDT）
- **插件化工具**：用户自定义工具注册

## 11. 关键决策记录

| 决策 | 选择 | 备选 | 理由 |
|---|---|---|---|
| 通信 | REST + WebSocket | REST + SSE | 多窗口、双向、跨窗口广播需要 WS |
| Agent 框架 | 手写最小循环 | LangChain | 依赖更少、可控性更高、便于以后扩展 |
| 大纲结构 | 树形 | 扁平 | 长篇需要分层 |
| 聊天持久化 | SQLite | 仅内存 | 用户要求，便于历史回溯 |
| 章节失败恢复 | 保留 draft_partial | 自动回滚 | 用户成果优先，手动决定 |
| 存储分工 | md/json + SQLite | 纯 SQLite 或纯文件 | 既可读可备份，又有结构化查询 |
| 状态机 | 5 阶段 + 可回退 | 自由流 | 引导式工作流，质量更稳 |
