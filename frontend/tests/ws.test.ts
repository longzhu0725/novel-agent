import { describe, it, expect, vi } from "vitest";
import { ChatSocket } from "../src/api/ws";

describe("ChatSocket", () => {
  it("emits parsed messages to handlers", () => {
    const sock = new ChatSocket("s1", "p1");
    const handler = vi.fn();
    sock.on(handler);
    const calls: unknown[] = [];
    class FakeWS {
      onmessage: ((e: { data: string }) => void) | null = null;
      onclose: (() => void) | null = null;
      readyState = 1;
      constructor(_: string) {}
      send(d: unknown) {
        calls.push(d);
      }
      close() {
        this.onclose?.();
      }
    }
    (globalThis as unknown as { WebSocket: unknown }).WebSocket = FakeWS;
    sock.connect();
    const fakeWs = (sock as unknown as { ws: FakeWS }).ws;
    fakeWs.onmessage?.({ data: JSON.stringify({ type: "delta", text: "hi" }) });
    expect(handler).toHaveBeenCalledWith({ type: "delta", text: "hi" });
  });

  it("send forwards payload to WebSocket", () => {
    const sock = new ChatSocket("s1", "p1");
    const calls: unknown[] = [];
    class FakeWS {
      onmessage: ((e: { data: string }) => void) | null = null;
      onclose: (() => void) | null = null;
      readyState = 1;
      constructor(_: string) {}
      send(d: unknown) {
        calls.push(d);
      }
      close() {}
    }
    (FakeWS as unknown as { OPEN: number }).OPEN = 1;
    (globalThis as unknown as { WebSocket: unknown }).WebSocket = FakeWS;
    sock.connect();
    sock.send({ type: "ping" });
    expect(calls[0]).toBe(JSON.stringify({ type: "ping" }));
  });
});
