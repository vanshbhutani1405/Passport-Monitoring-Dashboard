import { FormEvent, useState } from "react";

import { api } from "../api/client";
import type { Paginated, Post } from "../api/types";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import PostTable from "../components/PostTable";
import { CATEGORIES, PLATFORMS, SENTIMENTS, humanize } from "../utils/labels";

export default function Search() {
  const [query, setQuery] = useState("passport");
  const [platform, setPlatform] = useState("");
  const [category, setCategory] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Post> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(nextPage = 1) {
    try {
      setLoading(true);
      const result = await api.search({
        q: query,
        platform: platform || undefined,
        category: category || undefined,
        sentiment: sentiment || undefined,
        page: nextPage,
        page_size: 10,
      });
      setData(result);
      setPage(nextPage);
      setError(null);
    } catch {
      setError("Search failed. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(1);
  }

  const totalPages = data ? Math.max(Math.ceil(data.total / data.page_size), 1) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Search</h2>
        <p className="mt-1 text-sm text-slate-600">
          Search passport conversations across collected posts, translations, and summaries.
        </p>
      </div>

      <form className="grid gap-3 rounded-lg border border-line bg-white p-4 shadow-soft lg:grid-cols-5" onSubmit={handleSubmit}>
        <input
          className="rounded-md border border-line px-3 py-2 text-sm lg:col-span-2"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search keyword"
          required
        />
        <select className="rounded-md border border-line px-3 py-2 text-sm" value={platform} onChange={(event) => setPlatform(event.target.value)}>
          <option value="">All platforms</option>
          {PLATFORMS.map((item) => (
            <option key={item} value={item}>
              {humanize(item)}
            </option>
          ))}
        </select>
        <select className="rounded-md border border-line px-3 py-2 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((item) => (
            <option key={item} value={item}>
              {humanize(item)}
            </option>
          ))}
        </select>
        <div className="flex gap-3">
          <select className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 text-sm" value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
            <option value="">All sentiment</option>
            {SENTIMENTS.map((item) => (
              <option key={item} value={item}>
                {humanize(item)}
              </option>
            ))}
          </select>
          <button className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white" type="submit">
            Search
          </button>
        </div>
      </form>

      {error ? <ErrorState message={error} /> : null}
      {loading ? <LoadingState label="Searching" /> : null}

      {data ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-4">
            <h3 className="text-lg font-semibold">Results</h3>
            <span className="text-sm text-slate-600">{data.total} matches</span>
          </div>
          <PostTable posts={data.items} />
          <div className="flex items-center justify-between">
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-sm disabled:opacity-50"
              disabled={page <= 1 || loading}
              onClick={() => void runSearch(Math.max(page - 1, 1))}
            >
              Previous
            </button>
            <span className="text-sm text-slate-600">
              Page {page} of {totalPages}
            </span>
            <button
              className="rounded-md border border-line bg-white px-3 py-2 text-sm disabled:opacity-50"
              disabled={page >= totalPages || loading}
              onClick={() => void runSearch(page + 1)}
            >
              Next
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
