"use client";

// Approve / dismiss buttons for awaiting_approval incidents.
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function IncidentActions({ incidentId }: { incidentId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function act(action: "approve" | "dismiss") {
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/forge/incidents/${incidentId}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: action === "approve" ? JSON.stringify({ actor: "human:dashboard" }) : undefined,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      setError(String(body.detail ?? "request failed"));
      setBusy(false);
      return;
    }
    router.refresh();
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => act("approve")}
        disabled={busy}
        className="rounded-md bg-emerald-700 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-40"
      >
        Approve patch
      </button>
      <button
        onClick={() => act("dismiss")}
        disabled={busy}
        className="rounded-md border border-zinc-700 px-3 py-1 text-xs font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
      >
        Dismiss
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}
