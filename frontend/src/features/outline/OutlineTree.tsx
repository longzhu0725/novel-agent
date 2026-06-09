import { useEffect, useState } from "react";
import { api, type OutlineNode } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

interface Node extends OutlineNode {
  children: Node[];
}

function buildTree(list: OutlineNode[]): Node[] {
  const map = new Map<string, Node>();
  list.forEach((n) => map.set(n.id, { ...n, children: [] }));
  const roots: Node[] = [];
  map.forEach((n) => {
    if (n.parent_id && map.has(n.parent_id)) {
      map.get(n.parent_id)!.children.push(n);
    } else {
      roots.push(n);
    }
  });
  return roots.sort((a, b) => a.order - b.order);
}

function Tree({ nodes, depth = 0 }: { nodes: Node[]; depth?: number }) {
  if (nodes.length === 0) return null;
  return (
    <div className={depth === 0 ? "" : "ml-4"}>
      {nodes.map((n) => (
        <div key={n.id} className="outline-node">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-xs text-parchment-faint">
              {String(n.order).padStart(2, "0")}
            </span>
            <span className="outline-title">{n.title}</span>
            {n.chapter_id && (
              <span className="font-ornament text-[10px] text-gold tracking-widest ml-auto">
                章节
              </span>
            )}
          </div>
          {n.summary_md && (
            <p className="outline-summary">{n.summary_md}</p>
          )}
          {n.children.length > 0 && <Tree nodes={n.children} depth={depth + 1} />}
        </div>
      ))}
    </div>
  );
}

export default function OutlineTree({ pid }: { pid: string }) {
  const { outline, refreshOutline } = useProjectStore();
  const [title, setTitle] = useState("");
  const [parentId, setParentId] = useState<string>("");

  useEffect(() => {
    refreshOutline();
  }, [refreshOutline]);

  const create = async () => {
    const trimmed = title.trim();
    if (!trimmed) return;
    await api.post(`/projects/${pid}/outline`, {
      title: trimmed,
      parent_id: parentId || null,
      order: outline.length + 1,
    });
    setTitle("");
    setParentId("");
    await refreshOutline();
  };

  return (
    <div className="parchment p-6 md:p-8 animate-fade-in">
      {/* 标题 */}
      <div className="mb-2">
        <div className="label-ornament mb-1">叁 · 章纲</div>
        <h2 className="font-display italic text-3xl text-parchment">
          故事骨架
        </h2>
        <p className="font-body italic text-parchment-dim text-sm mt-1">
          情节、伏笔、节奏——这一切的蓝图。
        </p>
      </div>

      <div className="divider-gold" />

      {/* 新建节点 */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 mb-6">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
          placeholder="新节点的标题……"
          className="input"
        />
        <input
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
          placeholder="父节点 id（可选）"
          className="input md:w-48"
        />
        <button onClick={create} className="btn btn-primary">
          添加纲目
        </button>
      </div>

      {/* 大纲树 */}
      <div className="outline-tree">
        {outline.length === 0 ? (
          <div className="text-center py-12">
            <p className="font-display italic text-xl text-parchment-dim">
              卷中尚无章节
            </p>
            <p className="text-parchment-faint text-sm mt-2">
              先为故事起一个总纲。
            </p>
          </div>
        ) : (
          <Tree nodes={buildTree(outline)} />
        )}
      </div>
    </div>
  );
}
