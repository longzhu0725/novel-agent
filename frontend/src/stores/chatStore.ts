import { create } from "zustand";
import { ChatSocket, type WsEvent } from "../api/ws";

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  ts: number;
}

interface ChatState {
  socket: ChatSocket | null;
  messages: ChatMsg[];
  streaming: string;
  connect: (sid: string, pid: string) => void;
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
  messages: [],
  streaming: "",
  connect: (sid, pid) => {
    const sock = new ChatSocket(sid, pid);
    sock.on((ev) => get().handle(ev));
    sock.connect();
    set({ socket: sock });
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
  reset: () => set({ messages: [], streaming: "" }),
}));
