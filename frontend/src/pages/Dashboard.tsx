import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Analytics, HealthStatus, Post } from "../api/types";
import BarList from "../components/BarList";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import PostTable from "../components/PostTable";
import StatCard from "../components/StatCard";

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        const [analyticsData, healthData, postsData] = await Promise.all([
          api.getAnalytics(),
          api.getHealth(),
          api.getPosts({ page: 1, page_size: 8 }),
        ]);
        setAnalytics(analyticsData);
        setHealth(healthData);
        setRecentPosts(postsData.items);
        setError(null);
      } catch {
        setError("Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (loading) return <LoadingState label="Loading dashboard" />;
  if (error || !analytics) return <ErrorState message={error ?? "Dashboard data unavailable."} />;

  const databaseOk = health?.database_status === "ok";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-600">
          Current passport discussion volume, categories, sentiment, and collection health.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Posts" value={analytics.total_posts} detail="Collected conversations" />
        <StatCard label="Total Clusters" value={analytics.clusters_count} detail="Semantic topic groups" />
        <StatCard
          label="API Status"
          value={health?.api_status ?? "unknown"}
          detail={databaseOk ? "Database connected" : "Database unavailable"}
        />
        <StatCard
          label="Top Category"
          value={analytics.top_categories[0]?.name.replaceAll("_", " ") ?? "None"}
          detail={`${analytics.top_categories[0]?.count ?? 0} posts`}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <BarList title="Posts by Platform" items={analytics.posts_by_platform} />
        <BarList title="Posts by Sentiment" items={analytics.posts_by_sentiment} />
        <BarList title="Top Categories" items={analytics.top_categories} />
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">Recent Posts</h2>
          <span className="rounded-md bg-white px-3 py-1 text-sm text-slate-600">
            {recentPosts.length} shown
          </span>
        </div>
        <PostTable posts={recentPosts} />
      </section>
    </div>
  );
}
