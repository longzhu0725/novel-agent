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

const ROLE_KEYS = ["protagonist", "antagonist", "supporting", "mentor", "unknown"];

function formatDate(s: string): string {
  if (!s) return "";
  try {
    return new Date(s).toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
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
        <div className="label-ornament text-xs text-crimson mb-2">除名</div>
        <h3 className="font-display italic text-2xl text-parchment mb-3">
          确认删除此人物？
        </h3>
        <p className="font-body text-parchment-dim mb-1">
          <span className="text-gold">{name}</span> 将从名册中划去——
        </p>
        <p className="font-body italic text-parchment-faint text-sm mb-5">
          此举无法挽回。
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
            {busy ? "正在划去……" : "划去其名"}
          </button>
        </div>
      </div>
    </div>
  );
}

function EditCharacterModal({
  character,
  onClose,
  onSaved,
}: {
  character: Character;
  onClose: () => void;
  onSaved: (c: Character) => void;
}) {
  const [name, setName] = useState(character.name);
  const [role, setRole] = useState(character.role);
  const [profileMd, setProfileMd] = useState(character.profile_md);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    if (!name.trim()) {
      setErr("名讳不可为空");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const r = await api.patch<Character>(
        `/projects/${character.project_id}/characters/${character.id}`,
        { name: name.trim(), role, profile_md: profileMd },
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
              修订人物
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
          名字、定位、人物小传——可随时修订。
        </p>

        <div className="divider-gold" />

        <div className="space-y-3 my-4">
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              名字
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              autoFocus
            />
          </div>
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              定位
            </label>
            <div className="grid grid-cols-5 gap-2">
              {ROLE_KEYS.map((k) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setRole(k)}
                  className={`index-card !p-2 text-center cursor-pointer ${
                    role === k ? "active" : ""
                  }`}
                >
                  <span className="font-display text-sm text-parchment">
                    {ROLE_LABELS[k]}
                  </span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="font-ornament text-xs text-gold tracking-widest block mb-1.5">
              人物小传
            </label>
            <textarea
              value={profileMd}
              onChange={(e) => setProfileMd(e.target.value)}
              className="textarea textarea-prose"
              placeholder="出身、性格、动机、口癖、与其他人物的关系……"
              style={{ minHeight: "12rem" }}
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

export default function CharacterList({ pid }: { pid: string }) {
  const { characters, refreshCharacters } = useProjectStore();
  const [name, setName] = useState("");
  const [deleting, setDeleting] = useState<Character | null>(null);
  const [editing, setEditing] = useState<Character | null>(null);
  const [busy, setBusy] = useState(false);

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

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await api.delete(`/projects/${pid}/characters/${deleting.id}`);
      setDeleting(null);
      await refreshCharacters();
    } finally {
      setBusy(false);
    }
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
          <span className="text-parchment-faint">（点击卡牌可修订）</span>
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
            <li
              key={c.id}
              className="index-card relative group cursor-pointer hover:border-gold"
              onClick={() => setEditing(c)}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleting(c);
                }}
                className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center text-parchment-faint hover:text-crimson opacity-0 group-hover:opacity-100 transition-opacity z-10"
                title="删除人物"
                aria-label="删除人物"
              >
                ×
              </button>
              <div className="flex items-baseline justify-between gap-2 mb-2 pr-6">
                <h3 className="font-display text-xl text-parchment leading-tight">
                  {c.name}
                </h3>
                <span className="font-ornament text-xs text-gold tracking-widest shrink-0">
                  {ROLE_LABELS[c.role] ?? c.role}
                </span>
              </div>
              {c.profile_md ? (
                <p className="font-body text-parchment-dim text-sm leading-relaxed whitespace-pre-wrap line-clamp-4">
                  {c.profile_md}
                </p>
              ) : (
                <p className="font-body italic text-parchment-faint text-sm">
                  ——尚未着墨（点击修订）
                </p>
              )}
              <div className="mt-3 pt-2 border-t border-leather flex justify-between items-center">
                <span className="font-mono text-xs text-parchment-faint">
                  {formatDate(c.updated_at)}
                </span>
                <span className="text-gold opacity-50 text-xs font-display italic group-hover:opacity-100">
                  ❧ 修订 ›
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {deleting && (
        <ConfirmDelete
          name={deleting.name}
          busy={busy}
          onCancel={() => setDeleting(null)}
          onConfirm={confirmDelete}
        />
      )}
      {editing && (
        <EditCharacterModal
          character={editing}
          onClose={() => setEditing(null)}
          onSaved={(c) => {
            void refreshCharacters();
            setEditing(c);
          }}
        />
      )}
    </div>
  );
}
