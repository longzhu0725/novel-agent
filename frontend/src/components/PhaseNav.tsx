import type { Project } from "../api/client";

const PHASES = [
  { key: "INIT", cn: "起", label: "构想" },
  { key: "WORLD", cn: "壹", label: "世界" },
  { key: "CHARACTERS", cn: "贰", label: "人物" },
  { key: "OUTLINE", cn: "叁", label: "纲目" },
  { key: "WRITING", cn: "肆", label: "撰文" },
  { key: "DONE", cn: "终", label: "完稿" },
] as const;

export default function PhaseNav({
  project,
  onAdvance,
}: {
  project: Project;
  onAdvance: (to: string) => void;
}) {
  const currentIdx = PHASES.findIndex((p) => p.key === project.current_phase);

  return (
    <nav className="border-b border-leather bg-ink-soft/50 backdrop-blur-sm">
      <div className="px-6 py-2 flex items-center gap-1 overflow-x-auto">
        <span className="label-ornament mr-4 shrink-0 hidden md:inline">章回</span>
        {PHASES.map((p, i) => {
          const isActive = i === currentIdx;
          const isDone = i < currentIdx || project.current_phase === "DONE";
          const canAdvance = i > currentIdx && project.current_phase !== "DONE";
          return (
            <button
              key={p.key}
              disabled={!canAdvance}
              onClick={() => onAdvance(p.key)}
              className={`bookmark ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
              title={canAdvance ? `推进至 ${p.label}` : undefined}
            >
              <span className="font-display text-base mr-1 not-italic">{p.cn}</span>
              {p.label}
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-3 shrink-0">
          <span className="font-mono text-xs text-parchment-faint hidden lg:inline">
            {project.genre && `· ${project.genre} ·`}
          </span>
        </div>
      </div>
    </nav>
  );
}
