import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Project } from "../api/client";

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  const load = async () =>
    setProjects((await api.get<Project[]>("/projects")).data);

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    if (!name.trim()) return;
    const p = (await api.post<Project>("/projects", { name })).data;
    setName("");
    await load();
    navigate(`/projects/${p.id}`);
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">我的小说</h1>
      <div className="flex gap-2 mb-6">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="新小说名"
          className="flex-1 border rounded px-3 py-2"
        />
        <button
          onClick={create}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          创建
        </button>
      </div>
      <ul className="space-y-2">
        {projects.map((p) => (
          <li
            key={p.id}
            className="bg-white p-3 rounded shadow flex justify-between items-center"
          >
            <span>{p.name}</span>
            <span className="text-sm text-slate-500">{p.current_phase}</span>
            <button
              onClick={() => navigate(`/projects/${p.id}`)}
              className="text-blue-600"
            >
              打开
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
