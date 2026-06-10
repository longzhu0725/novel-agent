# novel-agent 端到端可行性验证报告
> 项目：那年夏天的蝉鸣 (id: `ea6f0ac82a484a7cb0a7c29537094629`)
> 日期：2026-06-10
> 阶段：`DONE`

---

## 1. 流程覆盖

| 阶段 | 状态 | 产物 |
|---|---|---|
| INIT | ✅ | 项目《那年夏天的蝉鸣》创建，含 logline / genre / style_notes |
| FOUNDATION | ✅ | 世界观 1 篇、人物 5 位、提纲 3 卷 7 章 |
| WRITING | ✅ | 7 章节经历 DRAFT → DRAFT_PARTIAL → REVIEWING → FINAL 完整状态机 |
| DONE | ✅ | phase 已推进，章节全部 FINAL |

## 2. 核心数据

- **项目**：《那年夏天的蝉鸣》
- **总字数（中文）**：21,745 字
- **章节数**：7 / 7  FINAL
- **卷数**：3 卷
- **人物数**：5 位
- **世界观**：1 篇 Markdown

### 章节字数

| # | 标题 | 状态 | 字数 |
|---|---|---|---|
| 1 | 第一章 · 转学生 | final | 3,018 |
| 2 | 第二章 · 雨天的琴行 | final | 3,325 |
| 3 | 第三章 · 樟树下 | final | 3,485 |
| 4 | 第四章 · 深夜的 QQ | final | 3,323 |
| 5 | 第五章 · 河埠的下午 | final | 2,405 |
| 6 | 第六章 · 苏小棠的眼泪 | final | 3,029 |
| 7 | 第七章 · 蝉鸣里的夏天 | final | 3,160 |

## 3. API 验证清单

- ✅ `POST /api/projects` 创项目
- ✅ `POST /api/projects/{pid}/phase` 推进阶段（INIT→FOUNDATION→WRITING→DONE）
- ✅ `PUT  /api/projects/{pid}/world` 写世界观
- ✅ `POST /api/projects/{pid}/characters` 批量建人物
- ✅ `POST /api/projects/{pid}/outline` 嵌套建提纲（3 卷 + 7 章）
- ✅ `POST /api/projects/{pid}/chapters` 创建章节
- ✅ `PATCH /api/projects/{pid}/chapters/{chid}` 多次更新（内容 + 状态）
- ✅ `GET  /api/projects/{pid}/chapters` 列表
- ✅ 章节状态机 DRAFT → DRAFT_PARTIAL → REVIEWING → FINAL 全程贯通
- ✅ 阶段状态机 INIT → FOUNDATION → WRITING → DONE 全程贯通
- ✅ 阶段推进**严格顺序**（后端状态机校验，回退会被拒）
- ✅ LLM 端点可达（豆包 doubao-seed-code），续写调用成功

## 4. 关键设计点

- **FOUNDATION 阶段无序**：合并冲突时特意保留了"世界 + 人物无先后"的设计
- **提纲树形结构**：用 `parent_id` + `order` 表达 3 卷 7 章
- **章节状态机**：DRAFT → DRAFT_PARTIAL → REVIEWING → FINAL，PATCH 任意中间态可回到 DRAFT
- **双重存储**：SQLite 存元数据，Markdown 文件存正文
- **LLM 集成**：续写时使用真实豆包端点（API Key 已配），每次最大 2000 token

## 5. 交付物

| 文件 | 用途 |
|---|---|
| `novel.md` | 完整小说正文（21,745 字，3 卷 7 章） |
| `characters.md` | 人物档案（5 人） |
| `world.md` | 世界观 |
| `REPORT.md` | 本报告 |
| `c1.md` ~ `c7.md` | 章节源文件（导入用） |
| `extend.py` | LLM 续写脚本 |
| `import_chapters.py` | 章节导入 + 状态机脚本 |
| `build_outline.py` | 提纲建树脚本 |

## 6. 结论

**novel-agent 项目从 0 到 1 完成了一个 21,745 字的校园青春恋爱小说，全程跑通：**

1. 项目创建 → 世界观 + 人物 + 提纲 → 7 章正文 → 阶段推进到 DONE
2. **所有 4 个阶段状态机、章节 4 态状态机、提纲树结构都验证通过**
3. **LLM 真实接入**，7 章累计调用约 14 次豆包续写完成扩写
4. 21,745 字 ≥ 用户要求的 2 万字，**超额 8.7%**

**项目可行性：✅ 验证通过。**
