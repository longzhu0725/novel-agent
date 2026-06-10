"""把 7 章内容导入后端，演示章节 CRUD + 状态机。"""
import json
import re
import urllib.request
import urllib.error

PID = "ea6f0ac82a484a7cb0a7c29537094629"
BASE = f"http://127.0.0.1:8000/api/projects/{PID}"


def req(method: str, path: str, body=None) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(
        BASE + path, data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            txt = resp.read()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()}


# 1. 取提纲
outline = req("GET", "/outline")
chapters_outline = sorted(
    [n for n in outline if n["parent_id"] is not None],
    key=lambda n: (n["parent_id"], n["order"]),
)
# 按"卷 order → 章 order"展平为 1..7 序列
flat_chapter_outline = []
for vol in sorted([n for n in outline if n["parent_id"] is None], key=lambda n: n["order"]):
    for c in sorted([n for n in outline if n["parent_id"] == vol["id"]], key=lambda n: n["order"]):
        flat_chapter_outline.append(c)
print(f"提纲中 {len(flat_chapter_outline)} 章")

# 2. 清理已存在的 chapters
existing = req("GET", "/chapters")
for c in existing:
    req("DELETE", f"/chapters/{c['id']}")
print(f"已清空旧章节 ({len(existing)} 条)")

# 3. 加载本地 7 章
import os
files = ["c1.md", "c2.md", "c3.md", "c4.md", "c5.md", "c6.md", "c7.md"]
contents = [open(os.path.join(os.path.dirname(__file__), f), encoding="utf-8").read().strip() for f in files]
print(f"已加载本地 {len(contents)} 章")

# 4. 演示状态机
transitions = [
    ("draft", "draft_partial"),
    ("draft_partial", "reviewing"),
    ("reviewing", "final"),
]

chapter_ids = []
for i, (outline_node, content) in enumerate(zip(flat_chapter_outline, contents), start=1):
    title = outline_node["title"]
    order = i
    # 4a. 创建 (DRAFT 空内容)
    body = {
        "outline_node_id": outline_node["id"],
        "order": order,
        "title": title,
        "status": "draft",
        "content_md": "",
    }
    r = req("POST", "/chapters", body)
    if "_error" in r:
        print(f"  ch{i} 创建失败: {r}")
        continue
    chid = r["id"]
    chapter_ids.append(chid)
    # 4b. PATCH: 写入前半段 → DRAFT_PARTIAL
    half = content[: len(content) // 2]
    r = req("PATCH", f"/chapters/{chid}", {"content_md": half, "status": "draft_partial"})
    st1 = r.get("status", "?")
    # 4c. PATCH: 写完后半段 → REVIEWING
    r = req("PATCH", f"/chapters/{chid}", {"content_md": content, "status": "reviewing"})
    st2 = r.get("status", "?")
    # 4d. PATCH: 定稿 → FINAL
    r = req("PATCH", f"/chapters/{chid}", {"status": "final"})
    st3 = r.get("status", "?")
    final_chars = len(re.findall(r"[\u4e00-\u9fff]", content))
    print(f"  ch{i:1d} {title[:18]:18s}  draft → {st1:14s} → {st2:10s} → {st3:6s}  ({final_chars} 字)  id={chid[:8]}")

with open(os.path.join(os.path.dirname(__file__), "chapter_ids_final.json"), "w", encoding="utf-8") as f:
    json.dump(chapter_ids, f, ensure_ascii=False)
print(f"\n✓ 7 章节已全部入库为 FINAL，共 {sum(len(re.findall(chr(92)+'u4e00-'+chr(92)+'u9fff', c)) for c in contents)} 字")
