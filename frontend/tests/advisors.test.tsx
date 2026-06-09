import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AdvisorPanel from "../src/features/advisors/AdvisorPanel";

vi.mock("../src/api/client", () => ({
  api: {
    post: vi.fn(),
  },
}));

import { api } from "../src/api/client";

const PID = "p123";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AdvisorPanel", () => {
  it("renders 3 advisor buttons", () => {
    render(<AdvisorPanel pid={PID} />);
    expect(screen.getByText("大纲专家")).toBeTruthy();
    expect(screen.getByText("风格专家")).toBeTruthy();
    expect(screen.getByText("评审专家")).toBeTruthy();
  });

  it("opens modal with question field for outline", () => {
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("大纲专家"));
    expect(screen.getByText(/咨询 大纲专家/)).toBeTruthy();
    expect(screen.getByText("问题")).toBeTruthy();
  });

  it("opens modal with text and focus fields for style", () => {
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("风格专家"));
    expect(screen.getByText("要评审的文本")).toBeTruthy();
    expect(screen.getByText("关注点（可选）")).toBeTruthy();
  });

  it("submits to /advisors/outline and displays advice", async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { advisor: "outline_expert", advice: "建议分三卷" },
    });
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("大纲专家"));
    const ta = screen.getByLabelText("问题") as HTMLTextAreaElement;
    fireEvent.change(ta, { target: { value: "怎么安排三卷结构" } });
    fireEvent.click(screen.getByText("提交"));
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        `/projects/${PID}/advisors/outline`,
        { question: "怎么安排三卷结构" },
        { timeout: 120_000 },
      );
    });
    await waitFor(() => {
      expect(screen.getByText("建议分三卷")).toBeTruthy();
    });
  });

  it("submits to /advisors/style with focus omitted when empty", async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { advisor: "style_expert", advice: "改" },
    });
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("风格专家"));
    fireEvent.change(screen.getByLabelText("要评审的文本"), {
      target: { value: "夜色压山" },
    });
    fireEvent.click(screen.getByText("提交"));
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        `/projects/${PID}/advisors/style`,
        { text: "夜色压山" },  // 无 focus
        { timeout: 120_000 },
      );
    });
  });

  it("shows error message on API failure", async () => {
    (api.post as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("network down"),
    );
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("评审专家"));
    fireEvent.change(screen.getByLabelText("评审目标"), {
      target: { value: "检查一致性" },
    });
    fireEvent.click(screen.getByText("提交"));
    await waitFor(() => {
      expect(screen.getByText(/请求失败/)).toBeTruthy();
    });
  });

  it("closes modal on ✕ click", () => {
    render(<AdvisorPanel pid={PID} />);
    fireEvent.click(screen.getByText("大纲专家"));
    expect(screen.getByText(/咨询 大纲专家/)).toBeTruthy();
    fireEvent.click(screen.getByText("✕"));
    expect(screen.queryByText(/咨询 大纲专家/)).toBeNull();
  });
});
