import IncidentActions from "@/components/IncidentActions";
import StatusPill from "@/components/StatusPill";
import { fetchIncidents, isDemo } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function IncidentsPage() {
  const incidents = await fetchIncidents();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Incidents</h1>
        <p className="mt-1 text-sm text-ink-muted">
          The diagnostician files a report when a run fails — with a root cause and, where it can, a
          proposed patch.
        </p>
      </div>

      {incidents.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-white/12 p-8 text-center text-sm text-ink-faint">
          Nothing has gone wrong yet.
        </p>
      ) : (
        <ul className="space-y-3">
          {incidents.map((incident) => (
            <li
              key={incident.id}
              className="rounded-2xl border border-white/8 bg-white/[0.02] p-5 transition-colors hover:border-white/14"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">{incident.summary}</p>
                  {incident.root_cause && (
                    <p className="mt-1.5 text-sm text-ink-muted">
                      <span className="text-ink-faint">Root cause: </span>
                      {incident.root_cause}
                    </p>
                  )}
                  <p className="mt-2.5 flex flex-wrap items-center gap-x-2 text-xs text-ink-faint">
                    <StatusPill status={incident.status} />
                    <span>·</span>
                    <span>severity {incident.severity}</span>
                    <span>·</span>
                    <span>{new Date(incident.created_at).toLocaleString()}</span>
                  </p>
                </div>
                {incident.status === "awaiting_approval" && (
                  <IncidentActions incidentId={incident.id} demo={isDemo} />
                )}
              </div>
              {incident.proposed_patch && incident.status === "awaiting_approval" && (
                <details className="mt-3 group">
                  <summary className="cursor-pointer text-xs font-medium text-ember-400 transition-colors hover:text-ember-300">
                    View proposed patch
                  </summary>
                  <pre className="mt-2 max-h-72 overflow-auto rounded-xl border border-white/8 bg-base-950 p-3 font-mono text-xs text-ink-muted">
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
