import Link from "next/link";
import ChatPanel from "@/components/ChatPanel";
import HealthBadge from "@/components/HealthBadge";
import StatusPill from "@/components/StatusPill";
import { fetchCosts, fetchHealth, fetchIncidents, fetchWorkflows, isDemo } from "@/lib/api";

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
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Overview</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Describe an automation and watch the agent generate, deploy, and monitor it.
        </p>
      </div>

      <ChatPanel demo={isDemo} />

      <div className="grid gap-4 sm:grid-cols-3">
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
        <h2 className="mb-3 text-sm font-semibold text-ink-muted">Workflows</h2>
        {workflows.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-white/12 p-8 text-center text-sm text-ink-faint">
            No workflows yet — describe one in the box above.
          </p>
        ) : (
          <ul className="overflow-hidden rounded-2xl border border-white/8">
            {workflows.map((workflow, i) => {
              const health = healthById.get(workflow.id);
              return (
                <li key={workflow.id} className={i !== 0 ? "border-t border-white/6" : ""}>
                  <Link
                    href={`/dashboard/workflows/${workflow.id}`}
                    className="flex items-center justify-between gap-4 px-4 py-3.5 transition-colors duration-200 hover:bg-white/[0.03]"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-mono text-sm font-medium text-ink">
                        {workflow.name}
                      </p>
                      <p className="mt-0.5 text-xs text-ink-faint">
                        v{workflow.current_version} · <StatusPill status={workflow.status} />
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3 text-xs text-ink-muted">
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
    <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
      <p className="text-xs text-ink-faint">{label}</p>
      <p
        className={`mt-1 font-display text-xl font-semibold ${
          tone === "warn" ? "text-amber-400" : "text-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
