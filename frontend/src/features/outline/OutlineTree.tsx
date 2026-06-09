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

function Tree({
  nodes,
  onEdit,
  onDelete,
  depth = 0,
}: {
  nodes: Node[];
  onEdit: (n: OutlineNode) => void;
  onDelete: (n: OutlineNode) => void;
  depth?: number;
}) {
  if (nodes.length === 0) return null;
  return (
    <div className={depth === 0 ? "" : "ml-4"}>
      {nodes.map((n) => (
        <div
          key={n.id}
          className="outline-node group cursor-pointer hover:border-gold"
          onClick={() => onEdit(n)}
        >
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-xs text-parchment-faint">
              {String(n.order).padStart(2, "0")}
            </span>
            <span className="outline-title flex-1">{n.title}</span>
            {n.chapter_id && (
              <span className="font-ornament text-[10px] text-gold tracking-widest">
                章节
              </span>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(n);
              }}
              className="ml-1 w-5 h-5 flex items-center justify-center text-parchment-faint hover:text-crimson opacity-0 group-hover:opacity-100 transition-opacity"
              title="删除纲目"
              aria-label="删除节点"
            >
              ×
            </button>
          </div>
          {n.summary_md && (
            <p className="outline-summary">{n.summary_md}</p>
          )}
          {n.children.length > 0 && (
            <Tree
              nodes={n.children}
              onEdit={onEdit}
              onDelete={onDelete}
              depth={depth + 1}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function ConfirmDelete({
  title,
  busy,
  onCancel,
  onConfirm,
}: {
  title: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal-panel p-6" onClick={(e) => e.stopPropagation()}>
        <div className="label-ornament text-xs text-crimson mb-2">删节</div>
        <h3 className="font-display italic text-2xl text-parchment mb-3">
          确认删除此纲目？
        </h3>
        <p className="font-body text-parchment-dim mb-1">
          <span className="text-gold">{title}</span> 将从骨架中抹去——
        </p>
        <p className="font-body italic text-parchment-faint text-sm mb-5">
          子纲目亦将一并消逝。
        </p>
        <div className="divider-gold" />
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onCancel} className="btn btn-ghost">收手</button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="btn"
            style={{ borderColor: "var(--crimson)", color: "var(--crimson)" }}
          >
            {busy ? "正在删节……" : "删去此节"}
          </button>
        </div>
      </div>
    </div>
  );
}

function EditOutlineModal({
  node,
  allNodes,
  onClose,
  onSaved,
}: {
  node: OutlineNode;
  allNodes: OutlineNode[];
  onClose: () => void;
  onSaved: (n: OutlineNode) => void;
}) {
  const [title, setTitle] = useState(node.title);
  const [summary, setSummary] = useState(node.summary_md);
  const [parentId, setParentId] = useState<string>(node.parent_id ?? "");
  const [order, setOrder] = useState<string>(String(node.order));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  // 父节点候选：排除自己和自己的后代
  const excludeIds = new Set<string>([node.id]);
  function collect(n: OutlineNode): void {
    for (const c of allNodes) {
      if (c.parent_id === n.id) {
        excludeIds.add(c.id);
        collect(c);
      }
    }
  }
  collect(node);

  const save = async () => {
    if (!title.trim()) {
      setErr("标题不可为空");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const r = await api.patch<OutlineNode>(
        `/projects/${node.project_id}/outline/${node.id}`,
        {
          title: title.trim(),
          summary_md: summary,
          parent_id: parentId || null,
          order: Number(order) || 0,
        },
      );
      onSaved(r.data);
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-1">
          <div>
            <div className="label-ornament text-xs">校阅</div>
            <h3 className="font-display italic text-2xl text-parchment mt-1">
              修订纲目
            </h3>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-icon text-xl"
            aria-label="关闭"
          >
            ×
          </button>
        </div>
        <p className="font-body italic text-parchment-dim text-sm mb-4">
          标题、摘要、归属与顺序——可随时修订。
        </p>

        <div className="divider-gold" />

        <div className="space-y-3 my-4">
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              标题
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input"
              autoFocus
            />
          </div>
          <div className="grid grid-cols-[1fr_auto] gap-3">
            <div>
              <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
                父节点
              </label>
              <select
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
                className="input"
              >
                <option value="">（根节点）</option>
                {allNodes
                  .filter((n) => !excludeIds.has(n.id))
                  .map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.title}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
                顺序
              </label>
              <input
                type="number"
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                className="input w-20"
              />
            </div>
          </div>
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              摘要
            </label>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="textarea textarea-prose"
              placeholder="这一节讲了什么、伏笔、关键转折……"
              style={{ minHeight: "8rem" }}
            />
          </div>
          {err && <p className="text-crimson text-sm font-body">{err}</p>}
        </div>

        <div className="divider-gold" />
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onClose} className="btn btn-ghost">取消</button>
          <button onClick={save} disabled={busy} className="btn btn-primary">
            {busy ? "正在定稿……" : "定稿"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function OutlineTree({ pid }: { pid: string }) {
  const { outline, refreshOutline } = useProjectStore();
  const [title, setTitle] = useState("");
  const [parentId, setParentId] = useState<string>("");
  const [deleting, setDeleting] = useState<OutlineNode | null>(null);
  const [editing, setEditing] = useState<OutlineNode | null>(null);
  const [busy, setBusy] = useState(false);

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

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await api.delete(`/projects/${pid}/outline/${deleting.id}`);
      setDeleting(null);
      await refreshOutline();
    } finally {
      setBusy(false);
    }
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
          <span className="text-parchment-faint">（点击节点可修订）</span>
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
          <Tree
            nodes={buildTree(outline)}
            onEdit={setEditing}
            onDelete={setDeleting}
          />
        )}
      </div>

      {deleting && (
        <ConfirmDelete
          title={deleting.title}
          busy={busy}
          onCancel={() => setDeleting(null)}
          onConfirm={confirmDelete}
        />
      )}
      {editing && (
        <EditOutlineModal
          node={editing}
          allNodes={outline}
          onClose={() => setEditing(null)}
          onSaved={() => {
            void refreshOutline();
          }}
        />
      )}
    </div>
  );
}
