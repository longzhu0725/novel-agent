import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useProjectStore } from "../stores/projectStore";
import { useChatStore } from "../stores/chatStore";
import PhaseNav from "../components/PhaseNav";
import WorldEditor from "../features/world/WorldEditor";
import CharacterList from "../features/characters/CharacterList";
import OutlineTree from "../features/outline/OutlineTree";
import ChapterList from "../features/chapters/ChapterList";
import ChatPanel from "../features/chat/ChatPanel";
import AdvisorPanel from "../features/advisors/AdvisorPanel";

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export default function Workspace() {
  const { pid = "" } = useParams();
  const { project, load, setPhase } = useProjectStore();
  const { connect } = useChatStore();

  useEffect(() => {
    if (pid) {
      load(pid);
      connect(uuid(), pid);
    }
  }, [pid, load, connect]);

  if (!project) return <div className="p-6">加载中…</div>;

  return (
    <div className="h-screen flex flex-col">
      <header className="px-4 py-2 border-b bg-white flex justify-between items-center">
        <h1 className="text-lg font-bold">{project.name}</h1>
        <span className="text-sm text-slate-500">{project.current_phase}</span>
      </header>
      <PhaseNav project={project} onAdvance={setPhase} />
      <main className="flex-1 grid grid-cols-4 gap-2 p-2 overflow-hidden">
        <div className="col-span-2 overflow-y-auto space-y-2">
          {project.current_phase === "INIT" && (
            <div className="bg-white p-3 rounded shadow text-sm text-slate-600">
              欢迎！请用右侧对话告诉 AI 你的小说创意，然后推进到 WORLD 阶段。
            </div>
          )}
          {project.current_phase === "WORLD" && <WorldEditor pid={pid} />}
          {project.current_phase === "CHARACTERS" && <CharacterList pid={pid} />}
          {project.current_phase === "OUTLINE" && <OutlineTree pid={pid} />}
          {(project.current_phase === "WRITING" ||
            project.current_phase === "DONE") && <ChapterList pid={pid} />}
        </div>
        <div className="overflow-y-auto space-y-2">
          <AdvisorPanel pid={pid} />
          <ChatPanel />
        </div>
      </main>
    </div>
  );
}
