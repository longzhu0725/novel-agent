import type { Project } from "../api/client";

const PHASES = ["INIT", "WORLD", "CHARACTERS", "OUTLINE", "WRITING", "DONE"] as const;

export default function PhaseNav({
  project,
  onAdvance,
}: {
  project: Project;
  onAdvance: (to: string) => void;
}) {
  const currentIdx = PHASES.indexOf(project.current_phase as (typeof PHASES)[number]);
  return (
    <nav className="flex gap-1 p-2 bg-slate-100 border-b">
      {PHASES.map((p, i) => (
        <button
          key={p}
          disabled={i <= currentIdx || project.current_phase === "DONE"}
          onClick={() => onAdvance(p)}
          className={`px-3 py-1 rounded text-sm ${
            i === currentIdx ? "bg-blue-600 text-white" : "bg-white border disabled:opacity-50"
          }`}
        >
          {p}
        </button>
      ))}
    </nav>
  );
}
