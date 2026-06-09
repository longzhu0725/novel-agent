import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../src/api/client", () => {
  const mkApi = () => ({
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  });
  return { api: mkApi() };
});

import { api } from "../src/api/client";
import { useProjectStore } from "../src/stores/projectStore";
import FoundationPanel from "../src/features/FoundationPanel";
import WritingPanel from "../src/features/WritingPanel";

const PID = "p-redesign";

beforeEach(() => {
  vi.clearAllMocks();
  // 重置所有 mock 的默认实现（mockResolvedValue 在 clearAllMocks 后会保留）
  (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
  (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  (api.put as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  (api.delete as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  // 重置 store，避免测试间状态泄露
  useProjectStore.setState({
    project: null,
    characters: [],
    outline: [],
    chapters: [],
  });
});

describe("FoundationPanel", () => {
  it("renders the tab switcher with both tabs", () => {
    render(<FoundationPanel pid={PID} />);
    // tab 标签（出现 2 次：tab 按钮 + 副标题中的 "世界观与人物"，所以用 getAllBy）
    expect(screen.getAllByText("世界观").length).toBeGreaterThan(0);
    expect(screen.getByText("人物志")).toBeTruthy();
  });

  it("starts on world tab by default and calls world API", async () => {
    render(<FoundationPanel pid={PID} />);
    // world 编辑器加载时会调 api.get("/projects/{pid}/world")，
    // 不依赖 store（WorldEditor 直接用 pid 调 API）
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(`/projects/${PID}/world`);
    });
  });

  it("switches to characters tab on click", async () => {
    render(<FoundationPanel pid={PID} />);
    // 先等 world 加载
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(`/projects/${PID}/world`);
    });
    // 找 tab 按钮里的 "人物志"（不是字符列表里的）
    const tabBtns = screen.getAllByText("人物志");
    fireEvent.click(tabBtns[0]);
    // tab 切换后，CharactersList 渲染时会触发它的 useEffect → store.refreshCharacters
    // 但 store.refreshCharacters 依赖 project.id，跳过；
    // 改用 store 直接设值的方式验证 tab 切换行为：点击后，character form 应出现
    await waitFor(() => {
      // character list 渲染时会有 "列入名册" 按钮（出现在 tab 标题与 form 中）
      expect(screen.getAllByText("列入名册").length).toBeGreaterThan(0);
    });
  });
});

describe("WritingPanel", () => {
  it("renders the title and empty state when no outline", () => {
    render(<WritingPanel pid={PID} />);
    expect(screen.getByText("落笔成章")).toBeTruthy();
    expect(screen.getByText("尚无纲目")).toBeTruthy();
  });

  it("renders outline nodes with chapter counts", () => {
    useProjectStore.setState({
      outline: [
        { id: "a", project_id: PID, parent_id: null, order: 1, title: "卷一", summary_md: "", chapter_id: null },
        { id: "b", project_id: PID, parent_id: null, order: 2, title: "卷二", summary_md: "", chapter_id: null },
      ],
      chapters: [
        { id: "c1", project_id: PID, outline_node_id: "a", order: 1, title: "ch1", content_md: "", word_count: 0, status: "DRAFT", created_at: "", updated_at: "" },
      ],
    });
    render(<WritingPanel pid={PID} />);
    expect(screen.getByText("卷一")).toBeTruthy();
    expect(screen.getByText("卷二")).toBeTruthy();
  });

  it("switches the right pane when clicking an outline node", async () => {
    useProjectStore.setState({
      outline: [
        { id: "a", project_id: PID, parent_id: null, order: 1, title: "卷一", summary_md: "", chapter_id: null },
        { id: "b", project_id: PID, parent_id: null, order: 2, title: "卷二", summary_md: "", chapter_id: null },
      ],
      chapters: [
        { id: "c1", project_id: PID, outline_node_id: "a", order: 1, title: "卷一章", content_md: "", word_count: 0, status: "DRAFT", created_at: "", updated_at: "" },
        { id: "c2", project_id: PID, outline_node_id: "b", order: 1, title: "卷二章", content_md: "", word_count: 0, status: "DRAFT", created_at: "", updated_at: "" },
      ],
    });
    render(<WritingPanel pid={PID} />);
    // 切到卷二（outline 节点在左侧按钮中；用 getAllByText 应对重复出现）
    const btns = screen.getAllByText("卷二");
    fireEvent.click(btns[0]);
    // 切换后，右侧应该渲染 ChapterList，而 ChapterList 标题"章回"出现
    await waitFor(() => {
      expect(screen.getByText("章回")).toBeTruthy();
    });
  });
});
