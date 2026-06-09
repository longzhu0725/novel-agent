import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function WorldEditor({ pid }: { pid: string }) {
  const [md, setMd] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    api.get(`/projects/${pid}/world`).then((r) => {
      setMd(r.data.content_md);
      setVersion(r.data.version);
    });
  }, [pid]);
  const save = async () => {
    const r = await api.put(`/projects/${pid}/world`, { content_md: md });
    setVersion(r.data.version);
  };
  return (
    <div className="bg-white rounded p-3 shadow">
      <div className="flex justify-between items-center mb-2">
        <h2 className="font-semibold">世界观 (v{version})</h2>
        <button
          onClick={save}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          保存
        </button>
      </div>
      <textarea
        value={md}
        onChange={(e) => setMd(e.target.value)}
        className="w-full h-96 border rounded p-2 font-mono text-sm"
        placeholder="# 世界观 markdown"
      />
    </div>
  );
}
