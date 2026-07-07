import Link from "next/link";
import ChatPanel from "@/components/ChatPanel";
import HealthBadge from "@/components/HealthBadge";
import StatusPill from "@/components/StatusPill";
import { fetchCosts, fetchHealth, fetchIncidents, fetchWorkflows } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const [workflows, incidents, costs] = await Promise.all([
    fetchWorkflows(),
    fetchIncidents(),
    fetchCosts(),
  ]);
  const healths = await Promise.all(workflows.map((workflow) => fetchHealth(workflow.id)));
  const healthById = new Map(healths.map((health) => [health.workflow_id, health]));
  const needsAttention = incidents.filter((incident) =>
    ["open", "awaiting_approval"].includes(incident.status),
  );

  return (
    <div className="space-y-8">
      <ChatPanel />

      <div className="grid grid-cols-3 gap-4">
        <Stat label="Workflows" value={String(workflows.length)} />
        <Stat
          label="Open incidents"
          value={String(needsAttention.length)}
          tone={needsAttention.length > 0 ? "warn" : "ok"}
        />
        <Stat
          label="Spend today"
          value={`$${costs.spend_today_usd.toFixed(2)} / $${costs.budget_usd.toFixed(2)}`}
          tone={costs.spend_today_usd >= costs.budget_usd ? "warn" : "ok"}
        />
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">Workflows</h2>
        {workflows.length === 0 ? (
          <p className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
            No workflows yet — describe one in the box above.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800">
            {workflows.map((workflow) => {
              const health = healthById.get(workflow.id);
              return (
                <li key={workflow.id}>
                  <Link
                    href={`/workflows/${workflow.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-zinc-900"
                  >
                    <div>
                      <p className="text-sm font-medium">{workflow.name}</p>
                      <p className="mt-0.5 text-xs text-zinc-500">
                        v{workflow.current_version} · <StatusPill status={workflow.status} />
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-zinc-500">
                      {health && health.success_rate !== null && (
                        <span>{Math.round(health.success_rate * 100)}% ok</span>
                      )}
                      <HealthBadge status={health?.status ?? "unknown"} />
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value, tone = "ok" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <p className="text-xs text-zinc-500">{label}</p>
      <p
        className={`mt-1 text-xl font-semibold ${tone === "warn" ? "text-amber-400" : "text-zinc-100"}`}
      >
        {value}
      </p>
    </div>
  );
}
