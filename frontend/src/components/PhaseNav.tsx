import { useState } from "react";
import { createPortal } from "react-dom";
import type { Project } from "../api/client";

const PHASES = [
  { key: "INIT", cn: "起", label: "构想" },
  { key: "FOUNDATION", cn: "壹", label: "基础" },
  { key: "WRITING", cn: "贰", label: "撰文" },
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
  const isDone = project.current_phase === "DONE";
  const [confirmBack, setConfirmBack] = useState<string | null>(null);

  const handleClick = (i: number, key: string) => {
    if (isDone) return;
    if (i < currentIdx) {
      setConfirmBack(key);
      return;
    }
    if (i === currentIdx + 1) {
      onAdvance(key);
    }
  };

  const targetLabel = confirmBack
    ? PHASES.find((p) => p.key === confirmBack)?.label ?? ""
    : "";
  const currentLabel = PHASES[currentIdx]?.label ?? "";

  return (
    <nav className="border-b border-leather bg-ink-soft/50 backdrop-blur-sm">
      <div className="px-6 py-2 flex items-center gap-1 overflow-x-auto">
        <span className="label-ornament mr-4 shrink-0 hidden md:inline">章回</span>
        {PHASES.map((p, i) => {
          const isActive = i === currentIdx;
          const isPast = i < currentIdx;
          const isNext = i === currentIdx + 1 && !isDone;
          const isFuture = i > currentIdx + 1;
          const isClickable = isPast || isNext;
          return (
            <button
              key={p.key}
              disabled={!isClickable}
              onClick={() => isClickable && handleClick(i, p.key)}
              className={`bookmark ${isActive ? "active" : ""} ${isPast ? "done" : ""} ${
                isFuture ? "opacity-30" : ""
              }`}
              title={
                isActive
                  ? "当前阶段"
                  : isPast
                  ? `回退到 ${p.label}`
                  : isNext
                  ? `推进至 ${p.label}`
                  : "需先完成前置阶段"
              }
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

      {confirmBack &&
        createPortal(
          <div
            className="modal-backdrop"
            onClick={() => setConfirmBack(null)}
          >
            <div
              className="modal-panel p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="label-ornament text-xs text-candle mb-2">回卷</div>
              <h3 className="font-display italic text-2xl text-parchment mb-3">
                确认回退至「{targetLabel}」？
              </h3>
              <p className="font-body text-parchment-dim mb-1">
                当前阶段「{currentLabel}」的工作已经就绪。
              </p>
              <p className="font-body italic text-parchment-faint text-sm mb-5">
                回退后再次前进需要重新经过每一卷。已写章节不会被删除，但需要重新进入才能继续。
              </p>
              <div className="divider-gold" />
              <div className="flex gap-2 justify-end mt-4">
                <button
                  onClick={() => setConfirmBack(null)}
                  className="btn btn-ghost"
                >
                  不动
                </button>
                <button
                  onClick={() => {
                    if (confirmBack) onAdvance(confirmBack);
                    setConfirmBack(null);
                  }}
                  className="btn"
                  style={{
                    borderColor: "var(--candle)",
                    color: "var(--candle)",
                  }}
                >
                  确认回退
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}
    </nav>
  );
}
