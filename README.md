# Novel Agent

辅助完成小说创作的本地优先 Web 应用。单 Agent + 工具，引导式工作流：世界观 → 人物 → 大纲 → 章节正文。

## 状态

v0 设计稿已就绪（见 [`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](docs/superpowers/specs/2026-06-09-novel-agent-design.md)），实施计划与代码待补。

## 技术栈

- **后端**：Python 3.11+, FastAPI, SQLite, OpenAI 兼容 LLM 客户端
- **前端**：React 18, TypeScript, Vite, Tailwind, zustand
- **通信**：REST + WebSocket（多窗口 / 会话隔离 / 双向）
- **存储**：本地 Markdown / JSON + SQLite（聊天持久化、滚动摘要）

## 快速开始（待补）

> v0 实施完成后补：克隆、配置 `.env`、启动后端与前端。

## 文档

- 设计文档：[`docs/superpowers/specs/2026-06-09-novel-agent-design.md`](docs/superpowers/specs/2026-06-09-novel-agent-design.md)
- 实施计划：待生成

## 许可证

MIT
