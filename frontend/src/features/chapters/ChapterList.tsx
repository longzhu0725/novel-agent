import { useEffect, useState } from "react";
import { api, type Chapter } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

const STATUS_LABELS: Record<string, { cn: string; color: string }> = {
  DRAFT: { cn: "草稿", color: "text-parchment-dim border-parchment-faint" },
  DRAFT_PARTIAL: { cn: "流式中", color: "text-candle border-candle" },
  REVIEWED: { cn: "已审", color: "text-emerald border-emerald" },
  FINAL: { cn: "完稿", color: "text-gold border-gold" },
};

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
        <div className="label-ornament text-xs text-crimson mb-2">焚稿</div>
        <h3 className="font-display italic text-2xl text-parchment mb-3">
          确认删除此章？
        </h3>
        <p className="font-body text-parchment-dim mb-1">
          <span className="text-gold">{title}</span> 将被永久焚稿——
        </p>
        <p className="font-body italic text-parchment-faint text-sm mb-5">
          正本（Markdown）亦将随之湮灭，无法挽回。
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
            {busy ? "正在焚稿……" : "焚毁此稿"}
          </button>
        </div>
      </div>
    </div>
  );
}

function NewChapterModal({
  pid,
  defaultOrder,
  onClose,
  onCreated,
}: {
  pid: string;
  defaultOrder: number;
  onClose: () => void;
  onCreated: (c: Chapter) => void;
}) {
  const [title, setTitle] = useState("");
  const [order, setOrder] = useState<string>(String(defaultOrder));
  const [outlineNodeId, setOutlineNodeId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const create = async () => {
    if (!title.trim()) {
      setErr("章名不可为空");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<Chapter>(`/projects/${pid}/chapters`, {
        title: title.trim(),
        order: Number(order) || defaultOrder,
        outline_node_id: outlineNodeId.trim() || null,
        content_md: "",
      });
      onCreated(r.data);
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
            <div className="label-ornament text-xs">新章</div>
            <h3 className="font-display italic text-2xl text-parchment mt-1">
              揭开一页新章
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
          为下一节命名——可稍后再写正文。
        </p>

        <div className="divider-gold" />

        <div className="space-y-3 my-4">
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              章名
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input"
              placeholder="第一章 · 长夜将明"
              autoFocus
            />
          </div>
          <div className="grid grid-cols-[1fr_auto] gap-3">
            <div>
              <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
                关联纲目 id（可选）
              </label>
              <input
                value={outlineNodeId}
                onChange={(e) => setOutlineNodeId(e.target.value)}
                className="input"
                placeholder="如要关联到大纲节点，填其 id"
              />
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
          {err && <p className="text-crimson text-sm font-body">{err}</p>}
        </div>

        <div className="divider-gold" />
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onClose} className="btn btn-ghost">取消</button>
          <button onClick={create} disabled={busy} className="btn btn-primary">
            {busy ? "正在启页……" : "启页"}
          </button>
        </div>
      </div>
    </div>
  );
}

function EditChapterMetaModal({
  chapter,
  onClose,
  onSaved,
}: {
  chapter: Chapter;
  onClose: () => void;
  onSaved: (c: Chapter) => void;
}) {
  const [title, setTitle] = useState(chapter.title);
  const [order, setOrder] = useState(String(chapter.order));
  const [status, setStatus] = useState(chapter.status);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    if (!title.trim()) {
      setErr("章名不可为空");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const r = await api.patch<Chapter>(
        `/projects/${chapter.project_id}/chapters/${chapter.id}`,
        {
          title: title.trim(),
          order: Number(order) || chapter.order,
          status,
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
              修订章节
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
          标题、顺序、状态——正文在下方编辑区。
        </p>

        <div className="divider-gold" />

        <div className="space-y-3 my-4">
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              章名
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
                状态
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="input"
              >
                <option value="DRAFT">草稿</option>
                <option value="DRAFT_PARTIAL">流式中</option>
                <option value="REVIEWED">已审</option>
                <option value="FINAL">完稿</option>
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

export default function ChapterList({ pid }: { pid: string }) {
  const { chapters, refreshChapters } = useProjectStore();
  const [active, setActive] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [deleting, setDeleting] = useState<Chapter | null>(null);
  const [editingMeta, setEditingMeta] = useState<Chapter | null>(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refreshChapters();
  }, [refreshChapters]);

  const open = (ch: Chapter) => {
    setActive(ch.id);
    setContent(ch.content_md);
    setSavedAt(null);
  };

  const save = async () => {
    if (!active) return;
    setSaving(true);
    try {
      await api.patch(`/projects/${pid}/chapters/${active}`, {
        content_md: content,
      });
      await refreshChapters();
      setSavedAt(new Date());
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await api.delete(`/projects/${pid}/chapters/${deleting.id}`);
      if (active === deleting.id) {
        setActive(null);
        setContent("");
      }
      setDeleting(null);
      await refreshChapters();
    } finally {
      setBusy(false);
    }
  };

  const onMetaSaved = (c: Chapter) => {
    void refreshChapters();
    setEditingMeta(null);
    setActive(c.id);
    setContent(c.content_md);
  };

  const onCreated = (c: Chapter) => {
    void refreshChapters();
    setActive(c.id);
    setContent(c.content_md);
  };

  const activeChapter = chapters.find((c) => c.id === active);
  const defaultOrder = (chapters.at(-1)?.order ?? 0) + 1;

  return (
    <div className="parchment p-6 md:p-8 animate-fade-in">
      {/* 标题 */}
      <div className="flex items-baseline justify-between gap-3 mb-2">
        <div>
          <div className="label-ornament mb-1">肆 · 撰文</div>
          <h2 className="font-display italic text-3xl text-parchment">
            章回
          </h2>
          <p className="font-body italic text-parchment-dim text-sm mt-1">
            落笔成章。每一个字，都是这卷不可分割的一部分。
            <span className="text-parchment-faint">（点击卡牌可修订）</span>
          </p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="btn btn-primary shrink-0"
        >
          + 启新章
        </button>
      </div>

      <div className="divider-gold" />

      {/* 章节选择器 */}
      {chapters.length === 0 ? (
        <div className="text-center py-12">
          <p className="font-display italic text-xl text-parchment-dim">
            尚未开篇
          </p>
          <p className="text-parchment-faint text-sm mt-2">
            点右上角「启新章」，或请右侧的笔为你揭幕第一章。
          </p>
        </div>
      ) : (
        <>
          <ul className="flex flex-wrap gap-2 mb-6">
            {chapters.map((ch) => {
              const s = STATUS_LABELS[ch.status] ?? {
                cn: ch.status,
                color: "text-parchment-faint border-leather",
              };
              return (
                <li key={ch.id} className="relative group">
                  <button
                    onClick={() => open(ch)}
                    onDoubleClick={() => setEditingMeta(ch)}
                    className={`index-card !p-3 text-left ${
                      ch.id === active ? "active" : ""
                    }`}
                    title="单击打开，双击修订章节信息"
                  >
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xs text-parchment-faint">
                        {String(ch.order).padStart(2, "0")}
                      </span>
                      <span
                        className={`font-display text-base ${
                          ch.id === active ? "text-gold-bright" : "text-parchment"
                        }`}
                      >
                        {ch.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1.5 text-xs">
                      <span
                        className={`font-ornament tracking-widest text-[10px] ${s.color.split(" ")[0]}`}
                      >
                        {s.cn}
                      </span>
                      <span className="font-mono text-parchment-faint">
                        {ch.word_count} 字
                      </span>
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleting(ch);
                    }}
                    className="absolute -top-2 -right-2 w-5 h-5 flex items-center justify-center bg-ink-soft border border-leather rounded-full text-parchment-faint hover:text-crimson hover:border-crimson opacity-0 group-hover:opacity-100 transition-opacity z-10"
                    title="删除章节"
                    aria-label="删除章节"
                  >
                    ×
                  </button>
                </li>
              );
            })}
          </ul>

          {active && activeChapter && (
            <div className="animate-fade-in">
              {/* 当前编辑的章节信息 */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="label-ornament text-xs">正在执笔</div>
                  <h3 className="font-display italic text-2xl text-parchment mt-0.5">
                    {String(activeChapter.order).padStart(2, "0")} · {activeChapter.title}
                  </h3>
                </div>
                <div className="text-right text-parchment-faint text-xs font-mono">
                  {content.length} 字
                </div>
              </div>

              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="textarea textarea-prose w-full min-h-[50vh]"
                placeholder="笔悬于此，落墨成章……"
              />

              <div className="flex items-center justify-between mt-4">
                <div className="text-parchment-faint text-xs font-body italic">
                  {savedAt ? (
                    <span>已存卷 · {savedAt.toLocaleTimeString("zh-CN")}</span>
                  ) : (
                    <span>未保存的改动将随风散去</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingMeta(activeChapter)}
                    className="btn"
                    style={{ borderColor: "var(--leather-light)", color: "var(--parchment-faint)" }}
                    title="修订章节元信息"
                  >
                    章节信息
                  </button>
                  <button
                    onClick={() => setDeleting(activeChapter)}
                    className="btn"
                    style={{ borderColor: "var(--crimson)", color: "var(--crimson)" }}
                    title="删除此章"
                  >
                    焚稿
                  </button>
                  <button onClick={save} disabled={saving} className="btn btn-primary">
                    {saving ? "正在落卷……" : "封存此页"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {deleting && (
        <ConfirmDelete
          title={deleting.title}
          busy={busy}
          onCancel={() => setDeleting(null)}
          onConfirm={confirmDelete}
        />
      )}
      {editingMeta && (
        <EditChapterMetaModal
          chapter={editingMeta}
          onClose={() => setEditingMeta(null)}
          onSaved={onMetaSaved}
        />
      )}
      {creating && (
        <NewChapterModal
          pid={pid}
          defaultOrder={defaultOrder}
          onClose={() => setCreating(false)}
          onCreated={onCreated}
        />
      )}
    </div>
  );
}
