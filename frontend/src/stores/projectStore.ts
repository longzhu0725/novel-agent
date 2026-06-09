import { create } from "zustand";
import {
  api,
  type Chapter,
  type Character,
  type OutlineNode,
  type Project,
} from "../api/client";

interface ProjectState {
  project: Project | null;
  characters: Character[];
  outline: OutlineNode[];
  chapters: Chapter[];
  load: (pid: string) => Promise<void>;
  refreshCharacters: () => Promise<void>;
  refreshOutline: () => Promise<void>;
  refreshChapters: () => Promise<void>;
  setPhase: (to: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  project: null,
  characters: [],
  outline: [],
  chapters: [],
  load: async (pid) => {
    const p = (await api.get<Project>(`/projects/${pid}`)).data;
    set({ project: p });
    await Promise.all([
      get().refreshCharacters(),
      get().refreshOutline(),
      get().refreshChapters(),
    ]);
  },
  refreshCharacters: async () => {
    const pid = get().project?.id;
    if (!pid) return;
    set({ characters: (await api.get<Character[]>(`/projects/${pid}/characters`)).data });
  },
  refreshOutline: async () => {
    const pid = get().project?.id;
    if (!pid) return;
    set({ outline: (await api.get<OutlineNode[]>(`/projects/${pid}/outline`)).data });
  },
  refreshChapters: async () => {
    const pid = get().project?.id;
    if (!pid) return;
    set({ chapters: (await api.get<Chapter[]>(`/projects/${pid}/chapters`)).data });
  },
  setPhase: async (to) => {
    const pid = get().project?.id;
    if (!pid) return;
    const p = (await api.post<Project>(`/projects/${pid}/phase`, { to })).data;
    set({ project: p });
  },
}));
