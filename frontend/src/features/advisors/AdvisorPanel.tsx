import { useState } from "react";
import { api } from "../../api/client";

type Advisor = "outline" | "style" | "reviewer";

const ADVISOR_META: Record<Advisor, { label: string; icon: string; color: string; desc: string; fields: { key: string; label: string; type: "text" | "textarea" }[] }> = {
  outline: {
    label: "大纲专家",
    icon: "📐",
    color: "bg-purple-50 border-purple-300",
    desc: "情节结构、伏笔、节奏",
    fields: [{ key: "question", label: "问题", type: "textarea" }],
  },
  style: {
    label: "风格专家",
    icon: "🎨",
    color: "bg-pink-50 border-pink-300",
    desc: "口吻、用词、节奏",
    fields: [
      { key: "text", label: "要评审的文本", type: "textarea" },
      { key: "focus", label: "关注点（可选）", type: "text" },
    ],
  },
  reviewer: {
    label: "评审专家",
    icon: "🔍",
    color: "bg-amber-50 border-amber-300",
    desc: "一致性、伏笔、节奏",
    fields: [
      { key: "target", label: "评审目标", type: "textarea" },
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
      const r = await api.post(`/projects/${pid}/advisors/${open}`, body);
      setAdvice(r.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setAdvice({ advisor: open, advice: `请求失败：${msg}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded p-3 shadow space-y-2">
      <h2 className="font-semibold text-sm">AI 团队</h2>
      <div className="grid grid-cols-3 gap-1">
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
              className={`p-2 rounded border text-xs ${m.color} hover:opacity-80`}
              title={m.desc}
            >
              <div className="text-lg">{m.icon}</div>
              <div className="font-medium">{m.label}</div>
            </button>
          );
        })}
      </div>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setOpen(null)}>
          <div className="bg-white rounded-lg shadow-xl p-5 w-full max-w-2xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-bold">
                {ADVISOR_META[open].icon} 咨询 {ADVISOR_META[open].label}
              </h3>
              <button onClick={() => setOpen(null)} className="text-slate-500 hover:text-slate-800">✕</button>
            </div>
            <p className="text-xs text-slate-500 mb-3">{ADVISOR_META[open].desc}</p>
            <div className="space-y-2 mb-3 overflow-y-auto">
              {ADVISOR_META[open].fields.map((f) => {
                const inputId = `advisor-${open}-${f.key}`;
                return (
                  <div key={f.key}>
                    <label htmlFor={inputId} className="text-sm text-slate-700">
                      {f.label}
                    </label>
                    {f.type === "textarea" ? (
                      <textarea
                        id={inputId}
                        value={form[f.key] ?? ""}
                        onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                        className="w-full border rounded p-2 text-sm h-24"
                      />
                    ) : (
                      <input
                        id={inputId}
                        value={form[f.key] ?? ""}
                        onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                        className="w-full border rounded p-2 text-sm"
                      />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex gap-2 justify-end mb-3">
              <button onClick={() => setOpen(null)} className="px-3 py-1 text-sm border rounded">
                取消
              </button>
              <button
                onClick={submit}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-1 text-sm rounded disabled:opacity-50"
              >
                {loading ? "咨询中…" : "提交"}
              </button>
            </div>
            {advice && (
              <div className="border-t pt-3 overflow-y-auto flex-1">
                <div className="text-xs text-slate-500 mb-1">来自 {advice.advisor}</div>
                <pre className="whitespace-pre-wrap text-sm font-sans">{advice.advice}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
