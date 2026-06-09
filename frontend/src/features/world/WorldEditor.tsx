import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function WorldEditor({ pid, embedded = false }: { pid: string; embedded?: boolean }) {
  const [md, setMd] = useState("");
  const [version, setVersion] = useState(0);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  useEffect(() => {
    api.get(`/projects/${pid}/world`).then((r) => {
      setMd(r.data.content_md);
      setVersion(r.data.version);
    });
  }, [pid]);

  const save = async () => {
    setSaving(true);
    try {
      const r = await api.put(`/projects/${pid}/world`, { content_md: md });
      setVersion(r.data.version);
      setSavedAt(new Date());
    } finally {
      setSaving(false);
    }
  };

  const content = (
    <>
      {!embedded && (
        <div className="parchment p-6 md:p-8 animate-fade-in">
          {/* 标题区 */}
          <div className="flex items-start justify-between gap-4 mb-2">
            <div>
              <div className="label-ornament mb-1">壹 · 设定之卷</div>
              <h2 className="font-display italic text-3xl text-parchment">
                世界观
              </h2>
              <p className="font-body italic text-parchment-dim text-sm mt-1">
                此地何方，此时何世，一切故事生根之处。
              </p>
            </div>
            <div className="text-right shrink-0">
              <div className="font-ornament text-xs text-parchment-faint tracking-widest">
                VERSION
              </div>
              <div className="font-display text-2xl text-gold italic">
                v{version}
              </div>
            </div>
          </div>
          <div className="divider-gold" />
        </div>
      )}
      {embedded && (
        <div className="flex items-start justify-between gap-4 mb-2 px-6 md:px-8 pt-6 md:pt-8">
          <div>
            <h3 className="font-display italic text-2xl text-parchment">世界观</h3>
            <p className="font-body italic text-parchment-dim text-sm mt-1">
              此地何方，此时何世，一切故事生根之处。
            </p>
          </div>
          <div className="text-right shrink-0">
            <div className="font-ornament text-xs text-parchment-faint tracking-widest">VERSION</div>
            <div className="font-display text-2xl text-gold italic">v{version}</div>
          </div>
        </div>
      )}
      <textarea
        value={md}
        onChange={(e) => setMd(e.target.value)}
        className="textarea textarea-prose w-full min-h-[60vh] mx-6 md:mx-8"
        style={{ maxWidth: "calc(100% - 3rem)" }}
        placeholder={"# 世界观\n\n## 时代背景\n## 地理\n## 规则与禁忌\n## 历史与传说\n……"}
      />
      <div className="flex items-center justify-between mt-4 px-6 md:px-8 pb-6 md:pb-8">
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
    </>
  );

  if (embedded) {
    return <div className="parchment p-0 animate-fade-in">{content}</div>;
  }
  return <div>{content}</div>;
}
