import axios from "axios";

import type { Analytics, Cluster, ClusterPost, HealthStatus, Paginated, Post } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
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
};
