import { useEffect, useState } from "react";
import { api, type Character } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

const ROLE_LABELS: Record<string, string> = {
  protagonist: "主角",
  antagonist: "反派",
  supporting: "配角",
  mentor: "导师",
  unknown: "未定",
};

function formatDate(s: string): string {
  if (!s) return "";
  try {
    return new Date(s).toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  } catch {
    return s;
  }
}

export default function CharacterList({ pid }: { pid: string }) {
  const { characters, refreshCharacters } = useProjectStore();
  const [name, setName] = useState("");

  useEffect(() => {
    refreshCharacters();
  }, [refreshCharacters]);

  const create = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    await api.post(`/projects/${pid}/characters`, { name: trimmed });
    setName("");
    await refreshCharacters();
  };

  return (
    <div className="parchment p-6 md:p-8 animate-fade-in">
      {/* 标题 */}
      <div className="mb-2">
        <div className="label-ornament mb-1">贰 · 人物志</div>
        <h2 className="font-display italic text-3xl text-parchment">
          登场诸君
        </h2>
        <p className="font-body italic text-parchment-dim text-sm mt-1">
          给他们一个名字，他们会自己开口说话。
        </p>
      </div>

      <div className="divider-gold" />

      {/* 新建 */}
      <div className="flex gap-3 mb-6">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
          placeholder="新人物的名字……"
          className="input flex-1"
        />
        <button onClick={create} className="btn btn-primary">
          列入名册
        </button>
      </div>

      {/* 人物卡列表 */}
      {characters.length === 0 ? (
        <div className="text-center py-12">
          <p className="font-display italic text-xl text-parchment-dim">
            名册尚是空白
          </p>
          <p className="text-parchment-faint text-sm mt-2">
            在上方为某位角色命名。
          </p>
        </div>
      ) : (
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {characters.map((c: Character) => (
            <li key={c.id} className="index-card">
              <div className="flex items-baseline justify-between gap-2 mb-2">
                <h3 className="font-display text-xl text-parchment leading-tight">
                  {c.name}
                </h3>
                <span className="font-ornament text-xs text-gold tracking-widest shrink-0">
                  {ROLE_LABELS[c.role] ?? c.role}
                </span>
              </div>
              {c.profile_md ? (
                <p className="font-body text-parchment-dim text-sm leading-relaxed whitespace-pre-wrap">
                  {c.profile_md}
                </p>
              ) : (
                <p className="font-body italic text-parchment-faint text-sm">
                  ——尚未着墨
                </p>
              )}
              <div className="mt-3 pt-2 border-t border-leather flex justify-between items-center">
                <span className="font-mono text-xs text-parchment-faint">
                  {formatDate(c.updated_at)}
                </span>
                <span className="text-gold opacity-50 text-xs font-display italic">
                  ❧
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
