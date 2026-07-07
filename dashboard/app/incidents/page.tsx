import IncidentActions from "@/components/IncidentActions";
import StatusPill from "@/components/StatusPill";
import { fetchIncidents } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function IncidentsPage() {
  const incidents = await fetchIncidents();

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Incidents</h1>
      {incidents.length === 0 ? (
        <p className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
          Nothing has gone wrong yet. The diagnostician files incidents here when runs fail.
        </p>
      ) : (
        <ul className="space-y-3">
          {incidents.map((incident) => (
            <li key={incident.id} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm">{incident.summary}</p>
                  {incident.root_cause && (
                    <p className="mt-1 text-xs text-zinc-500">Root cause: {incident.root_cause}</p>
                  )}
                  <p className="mt-2 text-xs text-zinc-600">
                    <StatusPill status={incident.status} /> · severity {incident.severity} ·{" "}
                    {new Date(incident.created_at).toLocaleString()}
                  </p>
                </div>
                {incident.status === "awaiting_approval" && (
                  <IncidentActions incidentId={incident.id} />
                )}
              </div>
              {incident.proposed_patch && incident.status === "awaiting_approval" && (
                <details className="mt-3">
                  <summary className="cursor-pointer text-xs text-orange-400 hover:text-orange-300">
                    View proposed patch
                  </summary>
                  <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-zinc-950 p-3 text-xs text-zinc-400">
                    {JSON.stringify(incident.proposed_patch, null, 2)}
                  </pre>
                </details>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
