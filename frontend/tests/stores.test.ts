import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore } from "../src/stores/chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.setState({ messages: [], streaming: "" });
  });

  it("accumulates deltas and finalizes on done", () => {
    const s = useChatStore.getState();
    s.handle({ type: "delta", text: "你" });
    s.handle({ type: "delta", text: "好" });
    expect(useChatStore.getState().streaming).toBe("你好");
    s.handle({ type: "done" });
    const after = useChatStore.getState();
    expect(after.streaming).toBe("");
    expect(after.messages[after.messages.length - 1].content).toBe("你好");
  });

  it("resets streaming on error", () => {
    useChatStore.setState({ streaming: "残" });
    useChatStore
      .getState()
      .handle({ type: "error", code: "X", message: "x" });
    expect(useChatStore.getState().streaming).toBe("");
  });
});
