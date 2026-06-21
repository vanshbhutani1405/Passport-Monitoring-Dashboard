import { useEffect, useState } from "react";

import { api, type PipelineStatus } from "../api/client";
import type { Analytics, HealthStatus, Post } from "../api/types";
import BarList from "../components/BarList";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import PostTable from "../components/PostTable";
import StatCard from "../components/StatCard";
import { useToastContext } from "../App";

export default function Dashboard() {
  const { showToast } = useToastContext();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isClustering, setIsClustering] = useState(false);
  const [isRunningAll, setIsRunningAll] = useState(false);

  const loadDashboard = async () => {
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
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  const handleIngest = async () => {
    setIsIngesting(true);
    try {
      const result = await api.runIngest();
      setPipelineStatus(result);
      if (result.success) {
        showToast("Ingestion completed successfully!", "success");
      } else {
        showToast(`Ingestion failed: ${result.error}`, "error");
      }
      await loadDashboard();
    } catch (e) {
      showToast("Failed to start ingestion", "error");
    } finally {
      setIsIngesting(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const result = await api.runAnalyze();
      setPipelineStatus(result);
      if (result.success) {
        showToast("Analysis completed successfully!", "success");
      } else {
        showToast(`Analysis failed: ${result.error}`, "error");
      }
      await loadDashboard();
    } catch (e) {
      showToast("Failed to start analysis", "error");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleEmbed = async () => {
    setIsEmbedding(true);
    try {
      const result = await api.runEmbed();
      setPipelineStatus(result);
      if (result.success) {
        showToast("Embeddings generated successfully!", "success");
      } else {
        showToast(`Embedding failed: ${result.error}`, "error");
      }
      await loadDashboard();
    } catch (e) {
      showToast("Failed to start embedding", "error");
    } finally {
      setIsEmbedding(false);
    }
  };

  const handleCluster = async () => {
    setIsClustering(true);
    try {
      const result = await api.runCluster();
      setPipelineStatus(result);
      if (result.success) {
        showToast("Clustering completed successfully!", "success");
      } else {
        showToast(`Clustering failed: ${result.error}`, "error");
      }
      await loadDashboard();
    } catch (e) {
      showToast("Failed to start clustering", "error");
    } finally {
      setIsClustering(false);
    }
  };

  const handleRunAll = async () => {
    setIsRunningAll(true);
    try {
      const result = await api.runAll();
      setPipelineStatus(result);
      if (result.success) {
        showToast("Full pipeline completed successfully!", "success");
      } else {
        showToast(`Pipeline failed: ${result.error}`, "error");
      }
      await loadDashboard();
    } catch (e) {
      showToast("Failed to start full pipeline", "error");
    } finally {
      setIsRunningAll(false);
    }
  };

  if (loading) return <LoadingState label="Loading dashboard" />;
  if (error || !analytics) return <ErrorState message={error ?? "Dashboard data unavailable."} />;

  const databaseOk = health?.database_status === "ok";
  const anyLoading = isIngesting || isAnalyzing || isEmbedding || isClustering || isRunningAll;

  const getStatusBadge = (status: string) => {
    if (status === "success") {
      return <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800">Success</span>;
    }
    if (status === "failed") {
      return <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">Failed</span>;
    }
    if (status === "running") {
      return <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">Running</span>;
    }
    if (status === "pending") {
      return <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">Pending</span>;
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-600">
          Current passport discussion volume, categories, sentiment, and collection health.
        </p>
      </div>

      {/* Pipeline Controls */}
      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Pipeline Controls</h3>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleIngest}
              disabled={anyLoading}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                isIngesting
                  ? "bg-slate-300 cursor-not-allowed text-slate-600"
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              {isIngesting ? "Ingesting..." : "Refresh Data"}
            </button>
            <button
              onClick={handleAnalyze}
              disabled={anyLoading}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                isAnalyzing
                  ? "bg-slate-300 cursor-not-allowed text-slate-600"
                  : "bg-indigo-600 text-white hover:bg-indigo-700"
              }`}
            >
              {isAnalyzing ? "Analyzing..." : "Run Analysis"}
            </button>
            <button
              onClick={handleEmbed}
              disabled={anyLoading}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                isEmbedding
                  ? "bg-slate-300 cursor-not-allowed text-slate-600"
                  : "bg-purple-600 text-white hover:bg-purple-700"
              }`}
            >
              {isEmbedding ? "Generating..." : "Generate Embeddings"}
            </button>
            <button
              onClick={handleCluster}
              disabled={anyLoading}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                isClustering
                  ? "bg-slate-300 cursor-not-allowed text-slate-600"
                  : "bg-pink-600 text-white hover:bg-pink-700"
              }`}
            >
              {isClustering ? "Clustering..." : "Rebuild Clusters"}
            </button>
            <button
              onClick={handleRunAll}
              disabled={anyLoading}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                isRunningAll
                  ? "bg-slate-300 cursor-not-allowed text-slate-600"
                  : "bg-emerald-600 text-white hover:bg-emerald-700"
              }`}
            >
              {isRunningAll ? "Running Full Pipeline..." : "Run Full Pipeline"}
            </button>
          </div>

          {/* Pipeline Status */}
          {pipelineStatus && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h4 className="mb-3 text-sm font-semibold text-slate-900">Pipeline Status</h4>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {typeof pipelineStatus.ingestion === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">Ingestion</span>
                    {getStatusBadge(pipelineStatus.ingestion)}
                  </div>
                )}
                {typeof pipelineStatus.google_news === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">Google News</span>
                    {getStatusBadge(pipelineStatus.google_news)}
                  </div>
                )}
                {typeof pipelineStatus.youtube === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">YouTube</span>
                    {getStatusBadge(pipelineStatus.youtube)}
                  </div>
                )}
                {typeof pipelineStatus.analysis === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">Analysis</span>
                    {getStatusBadge(pipelineStatus.analysis)}
                  </div>
                )}
                {typeof pipelineStatus.embeddings === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">Embeddings</span>
                    {getStatusBadge(pipelineStatus.embeddings)}
                  </div>
                )}
                {typeof pipelineStatus.clustering === 'string' && (
                  <div className="flex items-center justify-between rounded-md bg-white p-3">
                    <span className="text-sm font-medium text-slate-700">Clustering</span>
                    {getStatusBadge(pipelineStatus.clustering)}
                  </div>
                )}
              </div>
              {pipelineStatus.error && (
                <p className="mt-3 text-sm text-red-600">Error: {pipelineStatus.error}</p>
              )}
              {pipelineStatus.found !== undefined && (
                <p className="mt-2 text-sm text-slate-600">Found {pipelineStatus.found} items to process</p>
              )}
              {pipelineStatus.processed !== undefined && (
                <p className="text-sm text-slate-600">Processed {pipelineStatus.processed} items</p>
              )}
              {pipelineStatus.cluster_count !== undefined && (
                <p className="text-sm text-slate-600">Created {pipelineStatus.cluster_count} clusters</p>
              )}
            </div>
          )}
        </div>
      </section>

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
          value={analytics.top_categories[0]?.name.replace(/_/g, " ") ?? "None"}
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
