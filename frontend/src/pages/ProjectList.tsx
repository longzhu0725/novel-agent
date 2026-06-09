import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Project } from "../api/client";

const PHASE_LABELS: Record<string, string> = {
  INIT: "起 · 构想",
  WORLD: "壹 · 世界",
  CHARACTERS: "贰 · 人物",
  OUTLINE: "叁 · 纲目",
  WRITING: "肆 · 撰文",
  DONE: "终 · 完稿",
};

function formatDate(s: string): string {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric" });
  } catch {
    return s;
  }
}

function ConfirmDelete({
  name,
  busy,
  onCancel,
  onConfirm,
}: {
  name: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal-panel p-6" onClick={(e) => e.stopPropagation()}>
        <div className="label-ornament text-xs text-crimson mb-2">焚书</div>
        <h3 className="font-display italic text-2xl text-parchment mb-3">
          确认删除此卷？
        </h3>
        <p className="font-body text-parchment-dim mb-1">
          <span className="text-gold">{name}</span> 将被永久焚毁——
        </p>
        <p className="font-body italic text-parchment-faint text-sm mb-5">
          人物、世界观、章节、对话……一切随风散去，无法挽回。
        </p>
        <div className="divider-gold" />
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onCancel} className="btn btn-ghost">收手</button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="btn"
            style={{
              borderColor: "var(--crimson)",
              color: "var(--crimson)",
            }}
          >
            {busy ? "正在焚卷……" : "焚毁此卷"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<Project | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const list = (await api.get<Project[]>("/projects")).data;
      setProjects(list);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    const p = (await api.post<Project>("/projects", { name: trimmed })).data;
    setName("");
    await load();
    navigate(`/projects/${p.id}`);
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await api.delete(`/projects/${deleting.id}`);
      setDeleting(null);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen px-6 py-12 max-w-5xl mx-auto">
      {/* 顶部：标题区 */}
      <header className="text-center mb-16 animate-fade-in-up">
        <div className="label-ornament mb-3">A Writer&apos;s Atelier</div>
        <h1 className="font-display text-5xl md:text-6xl mb-3 tracking-tight">
          <span className="italic">L&apos;</span>
          <span className="text-gold-bright">Atelier</span>
          <span className="text-parchment-faint mx-3">·</span>
          <span>小说工作室</span>
        </h1>
        <p className="font-body italic text-parchment-dim text-lg max-w-xl mx-auto">
          静坐一隅，与笔同游。
          <span className="flicker text-gold"> ✦</span>
        </p>
      </header>

      <div className="divider-gold" />

      {/* 新建项目 */}
      <section
        className="parchment p-6 md:p-8 mb-12 animate-fade-in-up"
        style={{ animationDelay: "0.1s" }}
      >
        <div className="label-ornament mb-3">✒ 开启一本新书</div>
        <h2 className="font-display text-2xl mb-4 italic">
          为下一部作品起个名字
        </h2>
        <div className="flex gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
            placeholder="譬如：《长安月》《深海回声》……"
            className="input flex-1"
            style={{ animationDelay: "0.2s" }}
          />
          <button onClick={create} className="btn btn-primary">
            落笔起卷
          </button>
        </div>
      </section>

      {/* 项目列表 */}
      <section style={{ animationDelay: "0.3s" }} className="animate-fade-in-up">
        <div className="flex items-baseline justify-between mb-5">
          <div>
            <div className="label-ornament mb-1">架上之卷</div>
            <h2 className="font-display text-3xl italic">我的藏书</h2>
          </div>
          <span className="font-mono text-xs text-parchment-faint">
            {projects.length} 卷
          </span>
        </div>

        {loading ? (
          <div className="text-center py-16 text-parchment-dim font-display italic">
            <span className="ellipsis">从书架取下</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="parchment p-12 text-center">
            <p className="font-display italic text-2xl text-parchment-dim mb-2">
              书架空空
            </p>
            <p className="text-parchment-faint">
              在上方落笔，写下你的第一卷。
            </p>
          </div>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((p, i) => (
              <li
                key={p.id}
                className="book-spine px-5 py-4 animate-fade-in-up relative group"
                style={{ animationDelay: `${0.1 * i}s` }}
              >
                <div
                  className="cursor-pointer"
                  onClick={() => navigate(`/projects/${p.id}`)}
                >
                  <div className="flex items-start justify-between gap-3 pl-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-display text-xl text-parchment leading-snug truncate">
                        {p.name}
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="phase-badge">
                          {PHASE_LABELS[p.current_phase] ?? p.current_phase}
                        </span>
                        <span className="font-mono text-xs text-parchment-faint">
                          {formatDate(p.updated_at)}
                        </span>
                      </div>
                      {p.logline && (
                        <p className="font-body italic text-parchment-dim text-sm mt-2 line-clamp-2">
                          {p.logline}
                        </p>
                      )}
                    </div>
                    <div className="text-gold opacity-60 self-center text-xl font-display">
                      ›
                    </div>
                  </div>
                </div>

                {/* 删除按钮 - 悬停时显现 */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleting(p);
                  }}
                  className="absolute top-2 right-2 w-7 h-7 flex items-center justify-center text-parchment-faint hover:text-crimson opacity-0 group-hover:opacity-100 transition-opacity"
                  title="删除此卷"
                  aria-label="删除项目"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="divider-gold" style={{ marginTop: "4rem" }} />

      <footer className="text-center text-parchment-faint text-xs font-ornament tracking-widest py-6">
        SCRIBE · QUILL · CANDLE
      </footer>

      {/* 删除确认 */}
      {deleting && (
        <ConfirmDelete
          name={deleting.name}
          busy={busy}
          onCancel={() => setDeleting(null)}
          onConfirm={confirmDelete}
        />
      )}
    </div>
  );
}
