import axios from "axios";

export const api = axios.create({ baseURL: "/api", timeout: 30000 });

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.data?.detail) {
      err.message =
        typeof err.response.data.detail === "string"
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail);
    }
    return Promise.reject(err);
  },
);

export interface Project {
  id: string;
  name: string;
  logline: string;
  genre: string;
  style_notes: string;
  current_phase: string;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  role: string;
  profile_md: string;
  updated_at: string;
}

export interface OutlineNode {
  id: string;
  project_id: string;
  parent_id: string | null;
  order: number;
  title: string;
  summary_md: string;
  chapter_id: string | null;
}

export interface Chapter {
  id: string;
  project_id: string;
  outline_node_id: string | null;
  order: number;
  title: string;
  content_md: string;
  word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}
