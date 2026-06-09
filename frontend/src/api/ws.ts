export type WsEvent =
  | { type: "delta"; text: string; correlation_id?: string }
  | {
      type: "tool_call";
      id: string;
      name: string;
      args: unknown;
      correlation_id?: string;
    }
  | { type: "tool_result"; id: string; result: unknown; correlation_id?: string }
  | { type: "done"; correlation_id?: string }
  | {
      type: "error";
      code: string;
      message: string;
      recoverable?: boolean;
      correlation_id?: string;
    }
  | { type: "pong" }
  | {
      type: "project.changed";
      kind: string;
      id?: string;
      correlation_id?: string;
    };

export type WsHandler = (ev: WsEvent) => void;

export class ChatSocket {
  private ws: WebSocket | null = null;
  private handlers: WsHandler[] = [];
  private reconnectTimer: number | null = null;

  constructor(
    public sessionId: string,
    public projectId: string,
  ) {}

  connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(
      `${proto}://${location.host}/ws/chat?session_id=${this.sessionId}&project_id=${this.projectId}`,
    );
    this.ws.onmessage = (e) => {
      try {
        this.handlers.forEach((h) => h(JSON.parse(e.data) as WsEvent));
      } catch {
        /* noop */
      }
    };
    this.ws.onclose = () => {
      this.ws = null;
      this.reconnectTimer = window.setTimeout(() => this.connect(), 1500);
    };
  }

  send(payload: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  on(h: WsHandler): () => void {
    this.handlers.push(h);
    return () => {
      this.handlers = this.handlers.filter((x) => x !== h);
    };
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }
}
