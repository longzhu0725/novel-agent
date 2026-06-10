"""一次性建好提纲树：3 卷 7 章。"""
import json
import urllib.request

PID = "ea6f0ac82a484a7cb0a7c29537094629"
BASE = f"http://127.0.0.1:8000/api/projects/{PID}"


def post(path: str, body: dict) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# 用嵌套 list 表达结构，避免索引混乱
structure = [
    {
        "title": "卷一 · 初见",
        "summary": "夏初初遇。琴房、走廊、老河埠。",
        "chapters": [
            ("第一章 · 转学生",
             "林夕在琴房听到陌生的琴声。下午班里来了转学生江屿。放学后她在老河埠看见他吹口琴。"),
            ("第二章 · 雨天的琴行",
             "暴雨。林夕在镇南琴行避雨，发现江屿也在这里。两人第一次正式对话——关于一首老歌。"),
            ("第三章 · 樟树下",
             "陆晨带江屿来找苏小棠和林夕一起吃冰棒。樟树下江屿拍下了林夕的侧脸。"),
        ],
    },
    {
        "title": "卷二 · 靠近",
        "summary": "盛夏渐近。两人开始用 QQ 留言，交换歌曲。",
        "chapters": [
            ("第四章 · 深夜的 QQ",
             "林夕失眠，江屿在线。两人隔着屏幕，第一次说出各自的心结——她放弃音乐、他父亲去世。"),
            ("第五章 · 河埠的下午",
             "暑假开始。两人在老河埠第一次一起度过整个下午。教吹口琴。江屿告诉她关于父亲的最后一首未完成的曲子。"),
            ("第六章 · 苏小棠的眼泪",
             "苏小棠与母亲大吵后跑出来，林夕和江屿一起在书店陪她坐到天黑。林夕发现，原来\"守护\"比\"恋爱\"更难说出口。"),
        ],
    },
    {
        "title": "卷三 · 蝉鸣",
        "summary": "夏末告别。",
        "chapters": [
            ("第七章 · 蝉鸣里的夏天",
             "江屿要回北方了。临行前夜，老河埠。他把那支父亲留下的口琴和那本手抄五线谱留给了林夕。樟树下，蝉鸣里，他们没有说出口的话，都写进了《山鬼》。"),
        ],
    },
]

chapter_ids = []
for v_idx, vol in enumerate(structure, start=1):
    r = post("/outline", {
        "parent_id": None,
        "order": v_idx,
        "title": vol["title"],
        "summary_md": vol["summary"],
    })
    vol_id = r["id"]
    print(f"  [V v{v_idx}] {vol['title']}  -> {vol_id[:8]}")
    for c_idx, (title, summary) in enumerate(vol["chapters"], start=1):
        r = post("/outline", {
            "parent_id": vol_id,
            "order": c_idx,
            "title": title,
            "summary_md": summary,
        })
        cid = r["id"]
        chapter_ids.append(cid)
        print(f"      [C c{c_idx}] {title}  -> {cid[:8]}  parent={vol_id[:8]}")

with open("/workspace/poc/chapter_ids.json", "w") as f:
    json.dump(chapter_ids, f, ensure_ascii=False)
print(f"\n共 {len(chapter_ids)} 章节, ids saved.")
