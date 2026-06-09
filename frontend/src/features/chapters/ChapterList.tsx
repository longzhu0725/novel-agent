import { useEffect, useState } from "react";
import { api, type Chapter } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

const STATUS_LABELS: Record<string, { cn: string; color: string }> = {
  DRAFT: { cn: "草稿", color: "text-parchment-dim border-parchment-faint" },
  DRAFT_PARTIAL: { cn: "流式中", color: "text-candle border-candle" },
  REVIEWED: { cn: "已审", color: "text-emerald border-emerald" },
  FINAL: { cn: "完稿", color: "text-gold border-gold" },
};

export default function ChapterList({ pid }: { pid: string }) {
  const { chapters, refreshChapters } = useProjectStore();
  const [active, setActive] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);

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

  const activeChapter = chapters.find((c) => c.id === active);

  return (
    <div className="parchment p-6 md:p-8 animate-fade-in">
      {/* 标题 */}
      <div className="mb-2">
        <div className="label-ornament mb-1">肆 · 撰文</div>
        <h2 className="font-display italic text-3xl text-parchment">
          章回
        </h2>
        <p className="font-body italic text-parchment-dim text-sm mt-1">
          落笔成章。每一个字，都是这卷不可分割的一部分。
        </p>
      </div>

      <div className="divider-gold" />

      {/* 章节选择器 */}
      {chapters.length === 0 ? (
        <div className="text-center py-12">
          <p className="font-display italic text-xl text-parchment-dim">
            尚未开篇
          </p>
          <p className="text-parchment-faint text-sm mt-2">
            请告知右侧的笔——它会为你揭幕第一章。
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
                <li key={ch.id}>
                  <button
                    onClick={() => open(ch)}
                    className={`index-card !p-3 text-left ${
                      ch.id === active ? "active" : ""
                    }`}
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
                <button onClick={save} disabled={saving} className="btn btn-primary">
                  {saving ? "正在落卷……" : "封存此页"}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
