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

function Tree({ nodes }: { nodes: Node[] }) {
  return (
    <ul className="space-y-1">
      {nodes.map((n) => (
        <li key={n.id} className="border-l-2 border-slate-200 pl-2">
          <div className="font-medium">{n.title}</div>
          {n.summary_md && (
            <div className="text-sm text-slate-600">{n.summary_md}</div>
          )}
          {n.children.length > 0 && <Tree nodes={n.children} />}
        </li>
      ))}
    </ul>
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
    if (!title) return;
    await api.post(`/projects/${pid}/outline`, {
      title,
      parent_id: parentId || null,
      order: outline.length + 1,
    });
    setTitle("");
    await refreshOutline();
  };

  return (
    <div className="bg-white rounded p-3 shadow space-y-3">
      <h2 className="font-semibold">大纲</h2>
      <div className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="新节点标题"
          className="flex-1 border rounded px-2 py-1"
        />
        <input
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
          placeholder="父节点 id（可选）"
          className="border rounded px-2 py-1"
        />
        <button
          onClick={create}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          添加
        </button>
      </div>
      <Tree nodes={buildTree(outline)} />
    </div>
  );
}
