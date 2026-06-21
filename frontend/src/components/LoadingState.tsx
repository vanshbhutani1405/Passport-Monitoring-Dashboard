export default function LoadingState({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="rounded-lg border border-line bg-white p-6 text-sm text-slate-600 shadow-soft">
      {label}...
    </div>
  );
}
