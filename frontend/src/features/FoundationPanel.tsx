import { useState } from "react";
import WorldEditor from "./world/WorldEditor";
import CharacterList from "./characters/CharacterList";

type Tab = "world" | "characters";

/**
 * FOUNDATION 阶段主面板。
 * - 把「世界观」和「人物志」合并为同一阶段
 * - 提供左右两个标签，**没有先后顺序**——可自由切换
 * - 数据各自独立，不强制要求「完成」一个再去做另一个
 */
export default function FoundationPanel({ pid }: { pid: string }) {
  const [tab, setTab] = useState<Tab>("world");

  return (
    <div className="parchment p-6 md:p-8 animate-fade-in">
      {/* 标题 */}
      <div className="mb-2">
        <div className="label-ornament mb-1">壹 · 基础设定</div>
        <h2 className="font-display italic text-3xl text-parchment">
          万丈高楼，起于垒土
        </h2>
        <p className="font-body italic text-parchment-dim text-sm mt-1">
          世界观与人物，<span className="text-gold">无先后之分</span>——
          想到哪儿，就落到哪儿。
        </p>
      </div>

      <div className="divider-gold" />

      {/* 标签切换 */}
      <div className="flex items-center gap-1 mb-6 border-b border-leather">
        <button
          onClick={() => setTab("world")}
          className={`px-5 py-2 font-ornament text-xs tracking-widest transition-all relative ${
            tab === "world"
              ? "text-gold-bright"
              : "text-parchment-faint hover:text-parchment-dim"
          }`}
        >
          <span className="font-display text-base mr-1.5 not-italic">壹</span>
          世界观
          {tab === "world" && (
            <span
              className="absolute bottom-0 left-0 right-0 h-px"
              style={{ background: "var(--antique-gold-bright)", boxShadow: "0 0 8px var(--antique-gold)" }}
            />
          )}
        </button>
        <button
          onClick={() => setTab("characters")}
          className={`px-5 py-2 font-ornament text-xs tracking-widest transition-all relative ${
            tab === "characters"
              ? "text-gold-bright"
              : "text-parchment-faint hover:text-parchment-dim"
          }`}
        >
          <span className="font-display text-base mr-1.5 not-italic">贰</span>
          人物志
          {tab === "characters" && (
            <span
              className="absolute bottom-0 left-0 right-0 h-px"
              style={{ background: "var(--antique-gold-bright)", boxShadow: "0 0 8px var(--antique-gold)" }}
            />
          )}
        </button>
        <span className="ml-auto text-parchment-faint text-xs font-ornament tracking-widest">
          {tab === "world" ? "WORLD BUILDING" : "DRAMATIS PERSONAE"}
        </span>
      </div>

      {/* 内容区 */}
      <div className="animate-fade-in">
        {tab === "world" ? (
          <div className="-m-6 md:-m-8">
            {/* 编辑区自带 parchment，这里去掉外层包裹以避免双层 */}
            <WorldEditor pid={pid} embedded />
          </div>
        ) : (
          <div className="-m-6 md:-m-8">
            <CharacterList pid={pid} embedded />
          </div>
        )}
      </div>
    </div>
  );
}
