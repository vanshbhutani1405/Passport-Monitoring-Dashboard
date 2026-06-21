import axios from "axios";

import type { Analytics, Cluster, ClusterPost, HealthStatus, Paginated, Post } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export type PostFilters = {
  platform?: string;
  category?: string;
  sentiment?: string;
  language?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
};

export type SearchFilters = {
  q: string;
  platform?: string;
  category?: string;
  sentiment?: string;
  page?: number;
  page_size?: number;
};

export type PipelineStatus = {
  [key: string]: string | number | boolean | undefined;
  success: boolean;
  error?: string;
  status?: string;
  total_pending?: number;
  found?: number;
  processed?: number;
  failed?: number;
  successful?: number;
  remaining?: number;
  eligible_posts?: number;
  cluster_count?: number;
  cluster_memberships?: number;
};

export type TranslateRequest = {
  target_language: string;
  translate_summary_only?: boolean;
};

export type TranslateResponse = {
  post_id: string;
  language: string;
  translated_text: string;
};

export const api = {
  async getHealth() {
    const response = await apiClient.get<HealthStatus>("/health");
    return response.data;
  },
  async getAnalytics() {
    const response = await apiClient.get<Analytics>("/analytics");
    return response.data;
  },
  async getPosts(params: PostFilters = {}) {
    const response = await apiClient.get<Paginated<Post>>("/posts", { params });
    return response.data;
  },
  async getPost(id: string) {
    const response = await apiClient.get<Post>(`/posts/${id}`);
    return response.data;
  },
  async getClusters(params: { page?: number; page_size?: number } = {}) {
    const response = await apiClient.get<Paginated<Cluster>>("/clusters", { params });
    return response.data;
  },
  async getCluster(id: string) {
    const response = await apiClient.get<Cluster>(`/clusters/${id}`);
    return response.data;
  },
  async getClusterPosts(id: string, params: { page?: number; page_size?: number } = {}) {
    const response = await apiClient.get<Paginated<ClusterPost>>(`/clusters/${id}/posts`, {
      params,
    });
    return response.data;
  },
  async search(params: SearchFilters) {
    const response = await apiClient.get<Paginated<Post>>("/search", { params });
    return response.data;
  },
  async runIngest() {
    const response = await apiClient.post<PipelineStatus>("/pipeline/ingest");
    return response.data;
  },
  async runAnalyze() {
    const response = await apiClient.post<PipelineStatus>("/pipeline/analyze");
    return response.data;
  },
  async getAnalysisStatus() {
    const response = await apiClient.get<PipelineStatus>("/pipeline/analyze/status");
    return response.data;
  },
  async runEmbed() {
    const response = await apiClient.post<PipelineStatus>("/pipeline/embed");
    return response.data;
  },
  async runCluster() {
    const response = await apiClient.post<PipelineStatus>("/pipeline/cluster");
    return response.data;
  },
  async runAll() {
    const response = await apiClient.post<PipelineStatus>("/pipeline/run-all");
    return response.data;
  },
  async translatePost(postId: string, targetLanguage: string, translateSummaryOnly: boolean = false) {
    const response = await apiClient.post<TranslateResponse>(`/translate/${postId}`, {
      target_language: targetLanguage,
      translate_summary_only: translateSummaryOnly,
    });
    return response.data;
  },
  async exportCSV(params: PostFilters = {}) {
    const response = await apiClient.get("/export/csv", { params, responseType: "blob" });
    return response.data;
  },
};
