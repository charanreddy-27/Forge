const styles: Record<string, string> = {
  // run statuses
  success: "text-run-400",
  failed: "text-ember-400",
  running: "text-cyan-400",
  canceled: "text-ink-faint",
  // workflow statuses
  active: "text-run-400",
  inactive: "text-ink-faint",
  draft: "text-ink-faint",
  error: "text-ember-400",
  // incident statuses
  open: "text-amber-400",
  awaiting_approval: "text-ember-400",
  resolved: "text-run-400",
  dismissed: "text-ink-faint",
};

export default function StatusPill({ status }: { status: string }) {
  return (
    <span className={`text-xs font-medium ${styles[status] ?? "text-ink-muted"}`}>
      {status.replace("_", " ")}
    </span>
  );
}
