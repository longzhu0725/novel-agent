import { create } from "zustand";
import { api } from "../api/client";
import { ChatSocket, type WsEvent } from "../api/ws";

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  ts: number;
}

interface ChatState {
  socket: ChatSocket | null;
  sessionId: string;
  messages: ChatMsg[];
  streaming: string;
  historyLoaded: boolean;
  connect: (sid: string, pid: string) => void;
  loadHistory: (pid: string) => Promise<void>;
  send: (text: string) => void;
  handle: (ev: WsEvent) => void;
  reset: () => void;
}

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

export const useChatStore = create<ChatState>((set, get) => ({
  socket: null,
  sessionId: "default",
  messages: [],
  streaming: "",
  historyLoaded: false,

  connect: (sid, pid) => {
    // 关掉旧连接
    get().socket?.disconnect();
    const sock = new ChatSocket(sid, pid);
    sock.on((ev) => get().handle(ev));
    sock.connect();
    set({ socket: sock, sessionId: sid, historyLoaded: false });
    // 连接后立即拉历史
    void get().loadHistory(pid);
  },

  loadHistory: async (pid) => {
    const sid = get().sessionId;
    try {
      const r = await api.get<Array<{ role: string; content: string; created_at: string }>>(
        `/projects/${pid}/chat/history`,
        { params: { session_id: sid, limit: 200 } },
      );
      const msgs: ChatMsg[] = r.data
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          ts: new Date(m.created_at).getTime() || Date.now(),
        }));
      set({ messages: msgs, historyLoaded: true });
    } catch {
      set({ historyLoaded: true });
    }
  },

  send: (text) => {
    const { socket } = get();
    socket?.send({
      type: "chat.message",
      text,
      correlation_id: uuid(),
    });
    set((s) => ({
      messages: [...s.messages, { role: "user", content: text, ts: Date.now() }],
    }));
  },

  handle: (ev) => {
    switch (ev.type) {
      case "delta":
        set((s) => ({ streaming: s.streaming + ev.text }));
        break;
      case "done":
        set((s) => ({
          messages: s.streaming
            ? [
                ...s.messages,
                { role: "assistant", content: s.streaming, ts: Date.now() },
              ]
            : s.messages,
          streaming: "",
        }));
        break;
      case "error":
        set({ streaming: "" });
        break;
    }
  },

  reset: () => set({ messages: [], streaming: "", historyLoaded: false }),
}));
