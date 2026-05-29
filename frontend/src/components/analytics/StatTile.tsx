export function StatTile({
  label,
  value,
  sublabel,
  accent,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 relative overflow-hidden">
      {accent && (
        <div
          className="absolute inset-x-0 top-0 h-0.5"
          style={{ backgroundColor: accent }}
        />
      )}
      <div className="text-[11px] uppercase tracking-wider text-zinc-500">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-zinc-100">{value}</div>
      {sublabel && (
        <div className="mt-0.5 text-xs text-zinc-500">{sublabel}</div>
      )}
    </div>
  );
}
