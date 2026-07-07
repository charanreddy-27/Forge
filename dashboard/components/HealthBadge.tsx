const styles: Record<string, string> = {
  healthy: "bg-emerald-950 text-emerald-400 ring-emerald-800",
  degraded: "bg-amber-950 text-amber-400 ring-amber-800",
  failing: "bg-red-950 text-red-400 ring-red-800",
  unknown: "bg-zinc-900 text-zinc-500 ring-zinc-700",
};

export default function HealthBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${styles[status] ?? styles.unknown}`}
    >
      {status}
    </span>
  );
}
