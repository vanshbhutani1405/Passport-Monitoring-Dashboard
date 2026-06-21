import type { CountItem } from "../api/types";

type BarListProps = {
  title: string;
  items: CountItem[];
};

export default function BarList({ title, items }: BarListProps) {
  const max = Math.max(...items.map((item) => item.count), 1);

  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
      <h2 className="text-base font-semibold">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">No data yet.</p>
        ) : (
          items.map((item) => (
            <div key={item.name}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="truncate capitalize text-slate-700">{item.name.replace(/_/g, " ")}</span>
                <span className="font-medium">{item.count}</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-teal"
                  style={{ width: `${Math.max((item.count / max) * 100, 6)}%` }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
