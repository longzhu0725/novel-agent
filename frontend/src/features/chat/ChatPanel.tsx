import { useState } from "react";
import { useChatStore } from "../../stores/chatStore";

export default function ChatPanel() {
  const { messages, streaming, send } = useChatStore();
  const [text, setText] = useState("");

  const submit = () => {
    if (!text.trim()) return;
    send(text);
    setText("");
  };

  return (
    <div className="bg-white rounded p-3 shadow flex flex-col h-full">
      <h2 className="font-semibold mb-2">对话</h2>
      <div className="flex-1 overflow-y-auto space-y-2 mb-2">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-2 rounded text-sm whitespace-pre-wrap ${
              m.role === "user" ? "bg-blue-50" : "bg-slate-50"
            }`}
          >
            <div className="text-xs text-slate-500 mb-1">
              {m.role === "user" ? "我" : "AI"}
            </div>
            {m.content}
          </div>
        ))}
        {streaming && (
          <div className="p-2 rounded text-sm bg-slate-50 whitespace-pre-wrap">
            <div className="text-xs text-slate-500 mb-1">AI</div>
            {streaming}
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="说点什么…"
          className="flex-1 border rounded px-2 py-1"
        />
        <button
          onClick={submit}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          发送
        </button>
      </div>
    </div>
  );
}
