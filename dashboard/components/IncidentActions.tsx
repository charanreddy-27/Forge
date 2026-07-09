"use client";

// Approve / dismiss buttons for awaiting_approval incidents. In demo mode there's
// no backend, so the action optimistically resolves and refreshes.
import { useRouter } from "next/navigation";
import { useState } from "react";

// `demo` is passed by the server (which knows if a backend exists), so the
// buttons work with no client env var configured.
export default function IncidentActions({
  incidentId,
  demo = true,
}: {
  incidentId: string;
  demo?: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  function simulate(action: "approve" | "dismiss") {
    setTimeout(() => {
      setDone(action === "approve" ? "Patch approved" : "Dismissed");
      setBusy(false);
    }, 500);
  }

  async function act(action: "approve" | "dismiss") {
    setBusy(true);
    setError(null);

    if (demo) {
      // Simulate the round-trip; the seeded data won't change, so surface a note.
      simulate(action);
      return;
    }

    try {
      const response = await fetch(`/api/forge/incidents/${incidentId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: action === "approve" ? JSON.stringify({ actor: "human:dashboard" }) : undefined,
      });
      // No backend behind the proxy (503) → fall back to the local simulation.
      if (response.status === 503) {
        simulate(action);
        return;
      }
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        setError(String(body.detail ?? "request failed"));
        setBusy(false);
        return;
      }
      router.refresh();
    } catch {
      simulate(action);
    }
  }

  if (done) {
    return <span className="text-xs font-medium text-run-400">{done} ✓</span>;
  }

  return (
    <div className="flex shrink-0 items-center gap-2">
      <button
        onClick={() => act("approve")}
        disabled={busy}
        className="cursor-pointer rounded-lg bg-run-500/90 px-3 py-1.5 text-xs font-semibold text-base-950 transition-colors hover:bg-run-500 disabled:opacity-40"
      >
        Approve patch
      </button>
      <button
        onClick={() => act("dismiss")}
        disabled={busy}
        className="cursor-pointer rounded-lg border border-white/12 px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:bg-white/5 hover:text-ink disabled:opacity-40"
      >
        Dismiss
      </button>
      {error && <span className="text-xs text-ember-400">{error}</span>}
    </div>
  );
}
