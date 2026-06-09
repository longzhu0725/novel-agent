import { useState } from "react";
import { api } from "../../api/client";

type Advisor = "outline" | "style" | "reviewer";

const ADVISOR_META: Record<
  Advisor,
  {
    label: string;
    glyph: string;        // 字符画符号（衬线字体下表现力更强）
    cn: string;
    desc: string;
    fields: { key: string; label: string; type: "text" | "textarea"; placeholder?: string }[];
  }
> = {
  outline: {
    label: "Outline",
    cn: "纲目专家",
    glyph: "§",
    desc: "结构、伏笔、节奏——骨架的审读者。",
    fields: [{ key: "question", label: "询问", type: "textarea", placeholder: "你想请教什么？" }],
  },
  style: {
    label: "Style",
    cn: "风格专家",
    glyph: "✒",
    desc: "口吻、用词、韵律——文字的聆听者。",
    fields: [
      { key: "text", label: "需评议的文本", type: "textarea", placeholder: "将原文粘贴于此……" },
      { key: "focus", label: "关注点（可选）", type: "text", placeholder: "如：用词、画面感" },
    ],
  },
  reviewer: {
    label: "Review",
    cn: "评审专家",
    glyph: "✦",
    desc: "一致、伏笔、人物——故事的守门人。",
    fields: [
      { key: "target", label: "评审目标", type: "textarea", placeholder: "描述要评审的章节或情节……" },
      { key: "content_id", label: "章节 ID（可选）", type: "text" },
    ],
  },
};

export default function AdvisorPanel({ pid }: { pid: string }) {
  const [open, setOpen] = useState<Advisor | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [advice, setAdvice] = useState<{ advisor: string; advice: string } | null>(null);

  const submit = async () => {
    if (!open) return;
    setLoading(true);
    setAdvice(null);
    try {
      const body: Record<string, string> = {};
      ADVISOR_META[open].fields.forEach((f) => {
        const v = form[f.key]?.trim();
        if (v) body[f.key] = v;
      });
      const r = await api.post(`/projects/${pid}/advisors/${open}`, body, {
        timeout: 120_000,
      });
      setAdvice(r.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setAdvice({ advisor: open, advice: `请求失败：${msg}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="parchment p-5 animate-fade-in">
      {/* 标题 */}
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <div className="label-ornament text-xs">智囊</div>
          <h2 className="font-display italic text-2xl text-parchment">
            顾问<span className="text-gold"> ·</span> 三人
          </h2>
        </div>
        <span className="font-mono text-xs text-parchment-faint">3</span>
      </div>

      <div className="divider-gold" />

      {/* 顾问卡片 */}
      <div className="grid grid-cols-3 gap-2">
        {(Object.keys(ADVISOR_META) as Advisor[]).map((k) => {
          const m = ADVISOR_META[k];
          return (
            <button
              key={k}
              onClick={() => {
                setOpen(k);
                setForm({});
                setAdvice(null);
              }}
              className="advisor-card"
              title={m.desc}
            >
              <span className="advisor-glyph">{m.glyph}</span>
              <div className="advisor-name">{m.label}</div>
              <div className="font-ornament text-[9px] text-parchment-faint tracking-widest mt-1">
                {m.cn}
              </div>
            </button>
          );
        })}
      </div>

      {/* 模态 */}
      {open && (
        <div
          className="modal-backdrop"
          onClick={() => setOpen(null)}
        >
          <div
            className="modal-panel p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 模态头 */}
            <div className="flex items-start justify-between mb-1">
              <div>
                <div className="label-ornament text-xs">
                  {ADVISOR_META[open].cn} · {ADVISOR_META[open].label}
                </div>
                <h3 className="font-display italic text-2xl text-parchment mt-1 flex items-center gap-2">
                  <span className="text-gold text-3xl not-italic font-display">
                    {ADVISOR_META[open].glyph}
                  </span>
                  <span>请益</span>
                </h3>
              </div>
              <button
                onClick={() => setOpen(null)}
                className="btn btn-ghost btn-icon text-xl"
                aria-label="关闭"
              >
                ×
              </button>
            </div>
            <p className="font-body italic text-parchment-dim text-sm mb-4">
              {ADVISOR_META[open].desc}
            </p>

            <div className="divider-gold" />

            {/* 表单 */}
            <div className="space-y-3 my-4 overflow-y-auto" style={{ maxHeight: "30vh" }}>
              {ADVISOR_META[open].fields.map((f) => {
                const inputId = `advisor-${open}-${f.key}`;
                return (
                  <div key={f.key}>
                    <label
                      htmlFor={inputId}
                      className="font-ornament text-xs text-gold tracking-widest block mb-1.5"
                    >
                      {f.label}
                    </label>
                    {f.type === "textarea" ? (
                      <textarea
                        id={inputId}
                        value={form[f.key] ?? ""}
                        onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                        className="textarea textarea-prose"
                        placeholder={f.placeholder}
                        style={{ minHeight: "6rem" }}
                      />
                    ) : (
                      <input
                        id={inputId}
                        value={form[f.key] ?? ""}
                        onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                        className="input"
                        placeholder={f.placeholder}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            {/* 操作 */}
            <div className="flex gap-2 justify-end mb-3">
              <button
                onClick={() => setOpen(null)}
                className="btn btn-ghost"
              >
                收起
              </button>
              <button onClick={submit} disabled={loading} className="btn btn-primary">
                {loading ? (
                  <>
                    <span>顾问沉吟</span>
                    <span className="ellipsis" />
                  </>
                ) : (
                  "请益"
                )}
              </button>
            </div>

            {/* 答复 */}
            {advice && (
              <div className="border-t border-gold pt-4 overflow-y-auto flex-1 animate-fade-in">
                <div className="label-ornament mb-2">答复</div>
                <div className="font-body text-parchment leading-relaxed whitespace-pre-wrap text-[0.98rem]">
                  {advice.advice}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
