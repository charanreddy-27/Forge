const styles: Record<string, string> = {
  // run statuses
  success: "text-emerald-400",
  failed: "text-red-400",
  running: "text-sky-400",
  canceled: "text-zinc-500",
  // workflow statuses
  active: "text-emerald-400",
  inactive: "text-zinc-500",
  draft: "text-zinc-500",
  error: "text-red-400",
  // incident statuses
  open: "text-amber-400",
  awaiting_approval: "text-orange-400",
  resolved: "text-emerald-400",
  dismissed: "text-zinc-500",
};

export default function StatusPill({ status }: { status: string }) {
  return (
    <span className={`text-xs font-medium ${styles[status] ?? "text-zinc-400"}`}>
      {status.replace("_", " ")}
    </span>
  );
}
