import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjectStore } from "../stores/projectStore";
import { useChatStore } from "../stores/chatStore";
import PhaseNav from "../components/PhaseNav";
import WorldEditor from "../features/world/WorldEditor";
import CharacterList from "../features/characters/CharacterList";
import OutlineTree from "../features/outline/OutlineTree";
import ChapterList from "../features/chapters/ChapterList";
import ChatPanel from "../features/chat/ChatPanel";
import AdvisorPanel from "../features/advisors/AdvisorPanel";

const PHASE_TITLES: Record<string, { en: string; cn: string }> = {
  INIT: { en: "The First Page", cn: "落墨之前" },
  WORLD: { en: "World Building", cn: "构 · 世界观" },
  CHARACTERS: { en: "Dramatis Personae", cn: "立 · 人物志" },
  OUTLINE: { en: "The Plot", cn: "谋 · 章纲" },
  WRITING: { en: "The Manuscript", cn: "书 · 章节" },
  DONE: { en: "The Final Draft", cn: "成 · 完稿" },
};

function getSessionId(pid: string): string {
  // 每项目一个稳定的 session_id，刷新页面后历史不丢
  const key = `novel:session:${pid}`;
  let sid = localStorage.getItem(key);
  if (!sid) {
    sid = `default-${pid}`;
    localStorage.setItem(key, sid);
  }
  return sid;
}

export default function Workspace() {
  const { pid = "" } = useParams();
  const navigate = useNavigate();
  const { project, load, setPhase } = useProjectStore();
  const { connect } = useChatStore();

  useEffect(() => {
    if (pid) {
      load(pid);
      connect(getSessionId(pid), pid);
    }
  }, [pid, load, connect]);

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="font-display italic text-2xl text-parchment-dim mb-2">
            <span className="ellipsis">从书架取下</span>
          </div>
          <p className="text-parchment-faint text-sm">正在装订这一卷……</p>
        </div>
      </div>
    );
  }

  const phaseTitle = PHASE_TITLES[project.current_phase] ?? { en: "", cn: "" };

  return (
    <div className="h-screen flex flex-col">
      {/* 顶部书名区 */}
      <header className="px-6 py-4 border-b border-leather bg-ink-soft/40 backdrop-blur-sm">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0 flex items-center gap-4">
            <button
              onClick={() => navigate("/")}
              className="btn btn-ghost btn-icon shrink-0"
              title="返回藏书"
              aria-label="返回"
            >
              ‹
            </button>
            <div className="min-w-0">
              <div className="label-ornament text-xs mb-0.5">卷</div>
              <h1 className="font-display text-2xl md:text-3xl text-parchment truncate">
                {project.name}
              </h1>
            </div>
          </div>
          <div className="hidden md:flex flex-col items-end shrink-0">
            <span className="font-ornament text-xs text-parchment-faint tracking-widest">
              {phaseTitle.en}
            </span>
            <span className="font-display italic text-gold text-lg">
              {phaseTitle.cn}
            </span>
          </div>
        </div>
      </header>

      <PhaseNav project={project} onAdvance={setPhase} />

      {/* 三栏：主工作区 + 顾问 + 对话 */}
      <main className="flex-1 grid grid-cols-12 gap-3 p-3 overflow-hidden">
        {/* 主工作区 */}
        <section className="col-span-12 lg:col-span-7 xl:col-span-8 overflow-y-auto pr-1">
          {project.current_phase === "INIT" && (
            <div className="parchment p-8 animate-fade-in">
              <div className="label-ornament mb-2">卷首语</div>
              <h2 className="font-display italic text-3xl mb-4">
                一切故事，从一个念头开始
              </h2>
              <div className="quote-fancy text-parchment-dim mb-4">
                在右侧与你的笔谈天——告诉它关于这个世界、
                这些人物、这个故事的种种。准备就绪后，揭开下一页书签。
              </div>
              <div className="divider-gold" />
              <p className="text-parchment-faint text-sm italic font-body">
                提示：笔随时听候差遣。
              </p>
            </div>
          )}
          {project.current_phase === "WORLD" && <WorldEditor pid={pid} />}
          {project.current_phase === "CHARACTERS" && <CharacterList pid={pid} />}
          {project.current_phase === "OUTLINE" && <OutlineTree pid={pid} />}
          {(project.current_phase === "WRITING" ||
            project.current_phase === "DONE") && <ChapterList pid={pid} />}
        </section>

        {/* 右侧栏：顾问 + 对话 */}
        <aside className="col-span-12 lg:col-span-5 xl:col-span-4 flex flex-col gap-3 overflow-hidden">
          <AdvisorPanel pid={pid} />
          <ChatPanel />
        </aside>
      </main>
    </div>
  );
}
