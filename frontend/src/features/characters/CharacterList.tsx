import { useEffect, useState } from "react";
import { api, type Character } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

export default function CharacterList({ pid }: { pid: string }) {
  const { characters, refreshCharacters } = useProjectStore();
  const [name, setName] = useState("");

  useEffect(() => {
    refreshCharacters();
  }, [refreshCharacters]);

  const create = async () => {
    if (!name) return;
    await api.post(`/projects/${pid}/characters`, { name });
    setName("");
    await refreshCharacters();
  };

  return (
    <div className="bg-white rounded p-3 shadow space-y-3">
      <h2 className="font-semibold">人物</h2>
      <div className="flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="新人物名"
          className="flex-1 border rounded px-2 py-1"
        />
        <button
          onClick={create}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          创建
        </button>
      </div>
      <ul className="space-y-2">
        {characters.map((c: Character) => (
          <li
            key={c.id}
            className="border rounded p-2 flex justify-between items-start"
          >
            <div>
              <div className="font-medium">
                {c.name}{" "}
                <span className="text-xs text-slate-500">({c.role})</span>
              </div>
              <div className="text-sm text-slate-700 whitespace-pre-wrap">
                {c.profile_md}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
