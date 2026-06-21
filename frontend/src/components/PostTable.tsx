
import { useState } from "react";

import { api } from "../api/client";
import type { Post } from "../api/types";
import { useToastContext } from "../App";

type PostTableProps = {
  posts: Post[];
  onPostUpdated?: (postId: string) => void;
};

const SUPPORTED_LANGUAGES = [
  "English",
  "Hindi",
  "Punjabi",
  "Spanish",
  "French",
  "German",
  "Arabic",
  "Chinese",
  "Russian",
  "Japanese",
];

type TranslationState = {
  summary?: string;
  full?: string;
};

export default function PostTable({ posts, onPostUpdated }: PostTableProps) {
  const { showToast } = useToastContext();
  const [expandedPosts, setExpandedPosts] = useState<Set<string>>(new Set());
  const [selectedSummaryLanguages, setSelectedSummaryLanguages] = useState<Record<string, string>>({});
  const [selectedFullLanguages, setSelectedFullLanguages] = useState<Record<string, string>>({});
  const [isTranslatingSummary, setIsTranslatingSummary] = useState<Record<string, boolean>>({});
  const [isTranslatingFull, setIsTranslatingFull] = useState<Record<string, boolean>>({});
  const [isAnalyzingPost, setIsAnalyzingPost] = useState<Record<string, boolean>>({});
  const [translations, setTranslations] = useState<Record<string, TranslationState>>({});

  const toggleExpanded = (postId: string) => {
    const newExpanded = new Set(expandedPosts);
    if (newExpanded.has(postId)) {
      newExpanded.delete(postId);
    } else {
      newExpanded.add(postId);
    }
    setExpandedPosts(newExpanded);
  };

  const handleAnalyzePost = async (postId: string) => {
    setIsAnalyzingPost((prev) => ({ ...prev, [postId]: true }));
    try {
      await api.analyzePost(postId);
      showToast("Post analyzed successfully!", "success");
      if (onPostUpdated) {
        onPostUpdated(postId);
      }
    } catch (e) {
      showToast("Failed to analyze post", "error");
    } finally {
      setIsAnalyzingPost((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleTranslateSummary = async (postId: string) => {
    const lang = selectedSummaryLanguages[postId] || "English";
    setIsTranslatingSummary((prev) => ({ ...prev, [postId]: true }));
    try {
      const result = await api.translatePost(postId, lang, true);
      setTranslations((prev) => ({
        ...prev,
        [postId]: { ...prev[postId], summary: result.translated_text },
      }));
      showToast("Summary translated successfully!", "success");
    } catch (e) {
      showToast("Failed to translate summary", "error");
    } finally {
      setIsTranslatingSummary((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleTranslateFull = async (postId: string) => {
    const lang = selectedFullLanguages[postId] || "English";
    setIsTranslatingFull((prev) => ({ ...prev, [postId]: true }));
    try {
      const result = await api.translatePost(postId, lang, false);
      setTranslations((prev) => ({
        ...prev,
        [postId]: { ...prev[postId], full: result.translated_text },
      }));
      showToast("Post translated successfully!", "success");
    } catch (e) {
      showToast("Failed to translate post", "error");
    } finally {
      setIsTranslatingFull((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "youtube":
        return "bg-red-100 text-red-800";
      case "google_news":
        return "bg-blue-100 text-blue-800";
      case "reddit":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    const s = sentiment?.toLowerCase();
    if (s === "positive") return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (s === "negative") return "text-red-600 bg-red-50 border-red-200";
    if (s === "neutral") return "text-slate-600 bg-slate-50 border-slate-200";
    if (s === "mixed") return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-slate-600 bg-slate-50 border-slate-200";
  };

  return (
    <div className="space-y-4">
      {posts.map((post) => (
        <article
          key={post.id}
          className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"
        >
          <div className="p-5">
            <div className="mb-3 flex items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${getPlatformColor(
                  post.platform
                )}`}
              >
                {post.platform.replace("_", " ").toUpperCase()}
              </span>
              <span className="text-xs text-slate-500">
                {post.posted_at ? new Date(post.posted_at).toLocaleDateString() : "Unknown Date"}
              </span>
            </div>

            <h3 className="text-lg font-semibold text-slate-900 mb-3">
              <a
                href={post.url || "#"}
                target="_blank"
                rel="noreferrer"
                className="hover:text-indigo-600 transition-colors"
              >
                {post.title || (post.content.length > 80 ? post.content.slice(0, 80) + "..." : post.content)}
              </a>
            </h3>

            {!post.analysis && (
              <button
                onClick={() => handleAnalyzePost(post.id)}
                disabled={isAnalyzingPost[post.id]}
                className="mb-4 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-slate-400"
              >
                {isAnalyzingPost[post.id] ? "Analyzing..." : "⚡ Generate AI Analysis"}
              </button>
            )}

            {post.analysis && (
              <div className="mb-4">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-2xl">🧠</span>
                  <span className="text-sm font-semibold text-indigo-700">AI Summary</span>
                </div>
                <div className="rounded-lg border-2 border-indigo-100 bg-indigo-50 p-4">
                  <p className="text-sm text-slate-700">
                    {translations[post.id]?.summary || post.analysis.summary || "No summary available."}
                  </p>

                  {post.analysis.summary && (
                    <div className="mt-3 flex items-center gap-2">
                      <select
                        className="rounded border border-slate-300 bg-white px-2 py-1 text-xs"
                        value={selectedSummaryLanguages[post.id] || "English"}
                        onChange={(e) =>
                          setSelectedSummaryLanguages((prev) => ({
                            ...prev,
                            [post.id]: e.target.value,
                          }))
                        }
                      >
                        {SUPPORTED_LANGUAGES.map((lang) => (
                          <option key={lang} value={lang}>
                            {lang}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleTranslateSummary(post.id)}
                        disabled={isTranslatingSummary[post.id]}
                        className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:bg-slate-400"
                      >
                        {isTranslatingSummary[post.id] ? "Translating..." : "Translate Summary"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {post.analysis && (
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span
                  className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 border-indigo-200`}
                >
                  {post.analysis.category ? post.analysis.category.replace("_", " ") : "Category: Pending"}
                </span>
                <span
                  className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium ${getSentimentColor(
                    post.analysis.sentiment
                  )}`}
                >
                  {post.analysis.sentiment || "Sentiment: Pending"}
                </span>
                {post.analysis.language && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 border border-slate-200">
                    {post.analysis.language}
                  </span>
                )}
                {post.analysis.is_gibberish && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-yellow-50 px-3 py-1 text-xs font-medium text-yellow-800 border border-yellow-200">
                    🚨 Potential Spam/Gibberish
                  </span>
                )}
              </div>
            )}

            <button
              onClick={() => toggleExpanded(post.id)}
              className="flex items-center gap-1 text-sm text-slate-600 hover:text-indigo-600 mb-3"
            >
              {expandedPosts.has(post.id) ? "Hide Original Post" : "Show Original Post"}
              <span className="text-lg">{expandedPosts.has(post.id) ? "▲" : "▼"}</span>
            </button>

            {expandedPosts.has(post.id) && (
              <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm text-slate-700 mb-3">{post.content}</p>
                <div className="flex items-center gap-2">
                  <select
                    className="rounded border border-slate-300 bg-white px-2 py-1 text-xs"
                    value={selectedFullLanguages[post.id] || "English"}
                    onChange={(e) =>
                      setSelectedFullLanguages((prev) => ({
                        ...prev,
                        [post.id]: e.target.value,
                      }))
                    }
                  >
                    {SUPPORTED_LANGUAGES.map((lang) => (
                      <option key={lang} value={lang}>
                        {lang}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => handleTranslateFull(post.id)}
                    disabled={isTranslatingFull[post.id]}
                    className="rounded bg-slate-600 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700 disabled:bg-slate-400"
                  >
                    {isTranslatingFull[post.id] ? "Translating..." : "Translate Full Post"}
                  </button>
                </div>

                {translations[post.id]?.full && (
                  <div className="mt-4 rounded-lg border border-purple-200 bg-purple-50 p-3">
                    <p className="text-xs font-semibold text-purple-800 mb-1">Translated Post:</p>
                    <p className="text-sm text-purple-900">{translations[post.id].full}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </article>
      ))}

      {posts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-500">No posts found.</p>
        </div>
      )}
    </div>
  );
}

