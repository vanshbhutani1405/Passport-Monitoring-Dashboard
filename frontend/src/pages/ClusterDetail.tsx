import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { Cluster, ClusterPost, Paginated } from "../api/types";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import PostTable from "../components/PostTable";
import StatCard from "../components/StatCard";
import { humanize } from "../utils/labels";

export default function ClusterDetail() {
  const { clusterId } = useParams();
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [posts, setPosts] = useState<Paginated<ClusterPost> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCluster() {
      if (!clusterId) return;
      try {
        setLoading(true);
        const [clusterData, postsData] = await Promise.all([
          api.getCluster(clusterId),
          api.getClusterPosts(clusterId, { page: 1, page_size: 25 }),
        ]);
        setCluster(clusterData);
        setPosts(postsData);
        setError(null);
      } catch {
        setError("Unable to load cluster details.");
      } finally {
        setLoading(false);
      }
    }

    void loadCluster();
  }, [clusterId]);

  const platforms = useMemo(() => {
    const unique = new Set(posts?.items.map((post) => post.platform) ?? []);
    return Array.from(unique).join(", ") || "Unknown";
  }, [posts]);

  if (loading) return <LoadingState label="Loading cluster" />;
  if (error || !cluster || !posts) return <ErrorState message={error ?? "Cluster unavailable."} />;

  return (
    <div className="space-y-6">
      <Link className="text-sm font-medium text-teal hover:underline" to="/clusters">
        Back to clusters
      </Link>

      <div>
        <h2 className="text-2xl font-semibold">{cluster.name}</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          {cluster.description ?? "No cluster summary available."}
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Posts" value={cluster.post_count} />
        <StatCard label="Category" value={humanize(cluster.dominant_category)} />
        <StatCard label="Sentiment" value={humanize(cluster.dominant_sentiment)} />
        <StatCard label="Source Platforms" value={platforms} />
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Related Posts</h3>
        <PostTable posts={posts.items} />
      </section>
    </div>
  );
}
