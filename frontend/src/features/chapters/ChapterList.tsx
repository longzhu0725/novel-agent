import { useEffect, useState } from "react";
import { api, type Chapter } from "../../api/client";
import { useProjectStore } from "../../stores/projectStore";

export default function ChapterList({ pid }: { pid: string }) {
  const { chapters, refreshChapters } = useProjectStore();
  const [active, setActive] = useState<string | null>(null);
  const [content, setContent] = useState("");

  useEffect(() => {
    refreshChapters();
  }, [refreshChapters]);

  const open = async (ch: Chapter) => {
    setActive(ch.id);
    setContent(ch.content_md);
  };

  const save = async () => {
    if (!active) return;
    await api.patch(`/projects/${pid}/chapters/${active}`, {
      content_md: content,
    });
    await refreshChapters();
  };

  return (
    <div className="bg-white rounded p-3 shadow space-y-3">
      <h2 className="font-semibold">章节</h2>
      <ul className="flex flex-wrap gap-2">
        {chapters.map((ch: Chapter) => (
          <li key={ch.id}>
            <button
              onClick={() => open(ch)}
              className={`px-2 py-1 rounded text-sm border ${
                ch.id === active ? "bg-blue-600 text-white" : "bg-white"
              }`}
            >
              {ch.order}. {ch.title}{" "}
              <span className="text-xs">({ch.word_count})</span>
            </button>
          </li>
        ))}
      </ul>
      {active && (
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-slate-500">正在编辑：{active}</span>
            <button
              onClick={save}
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
            >
              保存
            </button>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-96 border rounded p-2 font-mono text-sm"
          />
        </div>
      )}
    </div>
  );
}
