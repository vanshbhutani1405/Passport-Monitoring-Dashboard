export type Analysis = {
  language: string;
  category: string;
  sentiment: string;
  summary: string | null;
  is_gibberish: boolean;
  is_duplicate: boolean;
};

export type Post = {
  id: string;
  platform: string;
  platform_post_id?: string;
  title: string | null;
  content: string;
  url: string | null;
  author_name?: string | null;
  content_type?: string;
  posted_at: string | null;
  collected_at?: string;
  like_count?: number;
  comment_count?: number;
  share_count?: number;
  view_count?: number;
  analysis?: Analysis | null;
  category?: string | null;
  sentiment?: string | null;
  summary?: string | null;
};

export type Paginated<T> = {
  total: number;
  page: number;
  page_size: number;
  items: T[];
};

export type CountItem = {
  name: string;
  count: number;
};

export type Analytics = {
  total_posts: number;
  clusters_count: number;
  posts_by_platform: CountItem[];
  posts_by_sentiment: CountItem[];
  posts_by_category: CountItem[];
  top_categories: CountItem[];
  top_clusters: Cluster[];
};

export type Cluster = {
  id: string;
  name: string;
  description: string | null;
  dominant_category: string | null;
  dominant_sentiment: string | null;
  post_count: number;
  created_at?: string;
  updated_at?: string;
};

export type ClusterPost = Post & {
  similarity_score: number | null;
};

export type HealthStatus = {
  api_status: string;
  database_status: string;
};
