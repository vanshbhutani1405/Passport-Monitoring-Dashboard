import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { Cluster, Paginated } from "../api/types";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { humanize } from "../utils/labels";

export default function Clusters() {
  const [data, setData] = useState<Paginated<Cluster> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadClusters() {
      try {
        setLoading(true);
        setData(await api.getClusters({ page, page_size: 12 }));
        setError(null);
      } catch {
        setError("Unable to load clusters.");
      } finally {
        setLoading(false);
      }
    }

    void loadClusters();
  }, [page]);

  if (loading) return <LoadingState label="Loading clusters" />;
  if (error || !data) return <ErrorState message={error ?? "Clusters unavailable."} />;

  const totalPages = Math.max(Math.ceil(data.total / data.page_size), 1);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Clusters</h2>
        <p className="mt-1 text-sm text-slate-600">Semantically grouped passport discussions.</p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.items.map((cluster) => (
          <Link
            key={cluster.id}
            to={`/clusters/${cluster.id}`}
            className="rounded-lg border border-line bg-white p-4 shadow-soft transition hover:-translate-y-0.5 hover:border-teal"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-lg font-semibold">{cluster.name}</h3>
              <span className="rounded-md bg-slate-100 px-2 py-1 text-sm font-medium">
                {cluster.post_count}
              </span>
            </div>
            <p className="mt-3 line-clamp-3 text-sm text-slate-600">
              {cluster.description ?? "No summary available."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs font-medium capitalize">
              <span className="rounded-md bg-teal/10 px-2 py-1 text-teal">
                {humanize(cluster.dominant_category)}
              </span>
              <span className="rounded-md bg-coral/10 px-2 py-1 text-coral">
                {humanize(cluster.dominant_sentiment)}
              </span>
            </div>
          </Link>
        ))}
      </section>

      <div className="flex items-center justify-between">
        <button
          className="rounded-md border border-line bg-white px-3 py-2 text-sm disabled:opacity-50"
          disabled={page <= 1}
          onClick={() => setPage((value) => Math.max(value - 1, 1))}
        >
          Previous
        </button>
        <span className="text-sm text-slate-600">
          Page {page} of {totalPages}
        </span>
        <button
          className="rounded-md border border-line bg-white px-3 py-2 text-sm disabled:opacity-50"
          disabled={page >= totalPages}
          onClick={() => setPage((value) => value + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
