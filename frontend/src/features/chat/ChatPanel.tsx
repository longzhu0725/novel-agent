import { useEffect, useRef, useState } from "react";
import { useChatStore } from "../../stores/chatStore";

export default function ChatPanel() {
  const { messages, streaming, send } = useChatStore();
  const [text, setText] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // 自动滚到底部
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, streaming]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    send(trimmed);
    setText("");
  };

  const isStreaming = !!streaming;

  return (
    <div className="parchment p-5 flex flex-col flex-1 min-h-0 animate-fade-in">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div>
          <div className="label-ornament text-xs">笔谈</div>
          <h2 className="font-display italic text-2xl text-parchment">
            与<span className="text-gold"> 笔 </span>对坐
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isStreaming ? "bg-candle animate-pulse" : "bg-emerald"
            }`}
            style={{ boxShadow: isStreaming ? "0 0 8px var(--candle)" : "0 0 6px var(--emerald)" }}
          />
          <span className="font-ornament text-[10px] text-parchment-faint tracking-widest">
            {isStreaming ? "WRITING" : "READY"}
          </span>
        </div>
      </div>

      <div className="divider-gold" />

      {/* 消息流 */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto py-3 space-y-4 min-h-0"
      >
        {messages.length === 0 && !streaming ? (
          <div className="text-center py-8">
            <p className="font-display italic text-lg text-parchment-dim">
              烛光摇曳，纸页空白
            </p>
            <p className="text-parchment-faint text-sm mt-1">
              告诉笔你的第一个念头。
            </p>
          </div>
        ) : (
          <>
            {messages.map((m, i) => (
              <div
                key={i}
                className={`message ${
                  m.role === "user" ? "message-user" : "message-ai"
                } animate-fade-in-up`}
                style={{ animationDelay: "0.05s" }}
              >
                {m.content}
              </div>
            ))}
            {streaming && (
              <div className="message message-ai message-streaming">
                {streaming}
              </div>
            )}
          </>
        )}
      </div>

      {/* 输入区 */}
      <div className="shrink-0 pt-3 border-t border-leather">
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit()}
            placeholder="说点什么……"
            className="input flex-1"
          />
          <button onClick={submit} className="btn btn-primary" disabled={isStreaming}>
            {isStreaming ? "落笔中" : "呈与笔"}
          </button>
        </div>
      </div>
    </div>
  );
}
