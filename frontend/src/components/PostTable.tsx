import type { Post } from "../api/types";

type PostTableProps = {
  posts: Post[];
};

export default function PostTable({ posts }: PostTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-white shadow-soft">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Post</th>
              <th className="px-4 py-3 text-left font-semibold">Platform</th>
              <th className="px-4 py-3 text-left font-semibold">Category</th>
              <th className="px-4 py-3 text-left font-semibold">Sentiment</th>
              <th className="px-4 py-3 text-left font-semibold">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {posts.map((post) => (
              <tr key={post.id} className="align-top">
                <td className="max-w-xl px-4 py-3">
                  <a
                    className="font-medium text-teal hover:underline"
                    href={post.url ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {post.title || post.content.slice(0, 80)}
                  </a>
                  <p className="mt-1 line-clamp-2 text-slate-600">{post.content}</p>
                </td>
                <td className="px-4 py-3 capitalize">{post.platform}</td>
                <td className="px-4 py-3 capitalize">
                  {(post.analysis?.category ?? post.category)?.replace(/_/g, " ") ?? "Pending"}
                </td>
                <td className="px-4 py-3 capitalize">
                  {post.analysis?.sentiment ?? post.sentiment ?? "Pending"}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {post.posted_at ? new Date(post.posted_at).toLocaleDateString() : "Unknown"}
                </td>
              </tr>
            ))}
            {posts.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-center text-slate-500" colSpan={5}>
                  No posts found.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
