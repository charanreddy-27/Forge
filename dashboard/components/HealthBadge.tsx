const styles: Record<string, string> = {
  healthy: "bg-run-500/12 text-run-400 ring-run-500/25",
  degraded: "bg-amber-500/12 text-amber-400 ring-amber-500/25",
  failing: "bg-ember-500/12 text-ember-400 ring-ember-500/30",
  unknown: "bg-white/5 text-ink-faint ring-white/12",
};

export default function HealthBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
        styles[status] ?? styles.unknown
      }`}
    >
      {status}
    </span>
  );
}
