import { useEffect, useState } from "react";
import { api, type Chapter, type OutlineNode } from "../api/client";
import { useProjectStore } from "../stores/projectStore";
import Modal from "../components/Modal";
import ChapterList from "./chapters/ChapterList";

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
  const sortRec = (xs: Node[]) => {
    xs.sort((a, b) => a.order - b.order);
    xs.forEach((x) => sortRec(x.children));
  };
  sortRec(roots);
  return roots;
}

function collectIds(roots: Node[]): Set<string> {
  const ids = new Set<string>();
  const walk = (xs: Node[]) => {
    xs.forEach((n) => {
      ids.add(n.id);
      walk(n.children);
    });
  };
  walk(roots);
  return ids;
}

function TreeNode({
  node,
  selectedId,
  chapterCounts,
  onSelect,
  depth = 0,
}: {
  node: Node;
  selectedId: string | null;
  chapterCounts: Record<string, number>;
  onSelect: (id: string) => void;
  depth?: number;
}) {
  const isActive = node.id === selectedId;
  const count = chapterCounts[node.id] ?? 0;
  return (
    <div>
      <button
        onClick={() => onSelect(node.id)}
        className={`w-full text-left px-3 py-2 rounded transition-all flex items-baseline gap-2 group ${
          isActive
            ? "bg-gold/10 border border-gold/40"
            : "border border-transparent hover:border-leather hover:bg-ink-soft/30"
        }`}
        style={{ marginLeft: depth * 12 }}
      >
        <span className="font-mono text-[10px] text-parchment-faint shrink-0 w-6">
          {String(node.order).padStart(2, "0")}
        </span>
        <span
          className={`flex-1 font-display text-sm truncate ${
            isActive ? "text-gold-bright" : "text-parchment"
          }`}
        >
          {node.title}
        </span>
        <span
          className={`font-ornament text-[10px] tracking-widest shrink-0 ${
            count > 0 ? "text-emerald" : "text-parchment-faint"
          }`}
          title={`${count} 章`}
        >
          {count > 0 ? `${count}章` : "·"}
        </span>
      </button>
      {node.children.map((c) => (
        <TreeNode
          key={c.id}
          node={c}
          selectedId={selectedId}
          chapterCounts={chapterCounts}
          onSelect={onSelect}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}

function CreateOutlineNodeModal({
  pid,
  parentId,
  open,
  onClose,
  onCreated,
}: {
  pid: string;
  parentId: string | null;
  open: boolean;
  onClose: () => void;
  onCreated: (n: OutlineNode) => void;
}) {
  const { outline, refreshOutline } = useProjectStore();
  const [title, setTitle] = useState("");
  const [parent, setParent] = useState<string>(parentId ?? "");
  const [order, setOrder] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const create = async () => {
    if (!title.trim()) {
      setErr("标题不可为空");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const ord = Number(order);
      const r = await api.post<OutlineNode>(`/projects/${pid}/outline`, {
        title: title.trim(),
        parent_id: parent || null,
        order: Number.isFinite(ord) ? ord : outline.length + 1,
      });
      await refreshOutline();
      onCreated(r.data);
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} ariaLabel="新增纲目">
      <div className="p-6">
        <div className="flex items-start justify-between mb-1">
          <div>
            <div className="label-ornament text-xs">添节</div>
            <h3 className="font-display italic text-2xl text-parchment mt-1">
              新增纲目
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
          为故事再添一节骨架——
          <span className="text-parchment-faint">可作为后续章节的归属节点。</span>
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
                value={parent}
                onChange={(e) => setParent(e.target.value)}
                className="input"
              >
                <option value="">（根节点）</option>
                {outline.map((n) => (
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
                placeholder="自动"
              />
            </div>
          </div>
          {err && <p className="text-crimson text-sm font-body">{err}</p>}
        </div>
        <div className="divider-gold" />
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onClose} className="btn btn-ghost">取消</button>
          <button onClick={create} disabled={busy} className="btn btn-primary">
            {busy ? "正在添节……" : "添节"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/**
 * 嵌入了 ChapterList 的写作主面板（双栏）：
 * - 左：大纲树（可点击切换写作焦点）
 * - 右：当前节点下的章节列表
 */
function EmbeddedChapters({
  pid,
  outlineNodeId,
}: {
  pid: string;
  outlineNodeId: string | null;
}) {
  return (
    <div className="parchment p-6 md:p-8 animate-fade-in h-full overflow-y-auto">
      <ChapterListInner pid={pid} outlineNodeId={outlineNodeId} />
    </div>
  );
}

// 抽出 ChapterList 的渲染（避免循环 import）
function ChapterListInner({
  pid,
  outlineNodeId,
}: {
  pid: string;
  outlineNodeId: string | null;
}) {
  return <ChapterList pid={pid} outlineNodeId={outlineNodeId} embedded />;
}

export default function WritingPanel({ pid }: { pid: string }) {
  const { outline, chapters, refreshOutline } = useProjectStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creatingNode, setCreatingNode] = useState(false);

  useEffect(() => {
    refreshOutline();
  }, [refreshOutline]);

  // 每次重新计算：默认选中第一个根节点
  useEffect(() => {
    if (!outline.length) {
      setSelectedId(null);
      return;
    }
    if (selectedId && outline.some((n) => n.id === selectedId)) return;
    // 找第一个有章节的节点；都没有就选第一个根节点
    const withChapters = outline.find((n) =>
      chapters.some((c) => c.outline_node_id === n.id),
    );
    const tree = buildTree(outline);
    const ids = collectIds(tree);
    const firstWithCh = ids.size
      ? Array.from(ids).find((id) =>
          chapters.some((c) => c.outline_node_id === id),
        )
      : null;
    const fallback = tree[0]?.id ?? outline[0]?.id ?? null;
    setSelectedId(firstWithCh ?? withChapters?.id ?? fallback);
    // 仅在 outline / chapters 列表变化时重新计算
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outline, chapters]);

  const tree = buildTree(outline);

  // 每个节点下章节数
  const chapterCounts: Record<string, number> = {};
  for (const c of chapters as Chapter[]) {
    if (c.outline_node_id) {
      chapterCounts[c.outline_node_id] = (chapterCounts[c.outline_node_id] ?? 0) + 1;
    }
  }

  return (
    <div className="parchment p-0 animate-fade-in h-full flex flex-col overflow-hidden">
      {/* 标题区 */}
      <div className="px-6 md:px-8 pt-6 md:pt-8 pb-2 shrink-0">
        <div className="label-ornament mb-1">贰 · 撰文</div>
        <h2 className="font-display italic text-3xl text-parchment">
          落笔成章
        </h2>
        <p className="font-body italic text-parchment-dim text-sm mt-1">
          选一节纲目，便为它写一段故事——
          <span className="text-parchment-faint">每节自成单元，章回各归其位。</span>
        </p>
      </div>
      <div className="divider-gold mx-6 md:mx-8" />

      {/* 双栏 */}
      <div className="flex-1 grid grid-cols-12 gap-3 p-3 overflow-hidden min-h-0">
        {/* 左：大纲浏览 */}
        <section className="col-span-12 md:col-span-4 lg:col-span-3 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2 shrink-0">
            <div className="label-ornament text-xs">纲目</div>
            <button
              onClick={() => setCreatingNode(true)}
              className="text-parchment-faint hover:text-gold text-xs font-ornament tracking-widest"
              title="新增纲目"
            >
              + 添节
            </button>
          </div>
          {outline.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center px-4">
                <p className="font-display italic text-base text-parchment-dim">
                  尚无纲目
                </p>
                <p className="text-parchment-faint text-xs mt-1">
                  先在右侧请笔为你立一个总纲，
                  <br />
                  或点上方「+ 添节」起笔。
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto pr-1 space-y-0.5">
              {tree.map((n) => (
                <TreeNode
                  key={n.id}
                  node={n}
                  selectedId={selectedId}
                  chapterCounts={chapterCounts}
                  onSelect={setSelectedId}
                />
              ))}
            </div>
          )}
        </section>

        {/* 右：当前节点章节 */}
        <section className="col-span-12 md:col-span-8 lg:col-span-9 min-h-0 overflow-hidden">
          {selectedId ? (
            <EmbeddedChapters pid={pid} outlineNodeId={selectedId} />
          ) : (
            <div className="parchment p-8 h-full flex items-center justify-center">
              <div className="text-center">
                <p className="font-display italic text-2xl text-parchment-dim">
                  尚无可书之卷
                </p>
                <p className="text-parchment-faint text-sm mt-2">
                  左侧添一节纲目，便可为它揭幕第一页。
                </p>
              </div>
            </div>
          )}
        </section>
      </div>

      {creatingNode && (
        <CreateOutlineNodeModal
          pid={pid}
          parentId={null}
          open
          onClose={() => setCreatingNode(false)}
          onCreated={(n) => setSelectedId(n.id)}
        />
      )}
    </div>
  );
}
