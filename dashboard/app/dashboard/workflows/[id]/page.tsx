import Link from "next/link";
import HealthBadge from "@/components/HealthBadge";
import StatusPill from "@/components/StatusPill";
import { fetchHealth, fetchRuns, fetchVersions, fetchWorkflow } from "@/lib/api";
import { ArrowRight } from "@/components/ui/icons";

export const dynamic = "force-dynamic";

export default async function WorkflowPage({ params }: { params: { id: string } }) {
  const [workflow, health, runs, versions] = await Promise.all([
    fetchWorkflow(params.id),
    fetchHealth(params.id),
    fetchRuns(params.id),
    fetchVersions(params.id),
  ]);

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1 text-xs text-ink-faint transition-colors hover:text-ink-muted"
        >
          <ArrowRight className="h-3.5 w-3.5 rotate-180" />
          Overview
        </Link>
        <header className="mt-3 flex items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight">{workflow.name}</h1>
            <p className="mt-1 text-xs text-ink-faint">
              v{workflow.current_version} · <StatusPill status={workflow.status} /> · engine id{" "}
              <span className="font-mono">{workflow.engine_workflow_id ?? "—"}</span>
            </p>
          </div>
          <HealthBadge status={health.status} />
        </header>
      </div>

      <section>
        <h2 className="mb-4 text-sm font-semibold text-ink-muted">
          Run timeline{" "}
          <span className="font-normal text-ink-faint">
            ({health.consecutive_failures} consecutive failure
            {health.consecutive_failures === 1 ? "" : "s"})
          </span>
        </h2>
        {runs.length === 0 ? (
          <p className="text-sm text-ink-faint">No runs recorded yet.</p>
        ) : (
          <ol className="relative space-y-0 border-l border-white/10 pl-5">
            {runs.map((run) => (
              <li key={run.id} className="relative py-2.5">
                <span
                  className={`absolute -left-[26px] top-4 h-2.5 w-2.5 rounded-full ring-4 ring-base-950 ${
                    run.status === "success"
                      ? "bg-run-500"
                      : run.status === "failed"
                        ? "bg-ember-500"
                        : "bg-cyan-500"
                  }`}
                />
                <div className="flex items-baseline justify-between gap-3">
                  <p className="text-sm">
                    <StatusPill status={run.status} />{" "}
                    <span className="font-mono text-xs text-ink-faint">
                      #{run.engine_execution_id}
                    </span>
                  </p>
                  <time className="text-xs text-ink-faint">
                    {new Date(run.started_at).toLocaleString()}
                  </time>
                </div>
                {run.error_message && (
                  <p className="mt-1 font-mono text-xs text-ember-300/80">{run.error_message}</p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-muted">Versions</h2>
        <ul className="overflow-hidden rounded-2xl border border-white/8 text-sm">
          {versions.map((version, i) => (
            <li
              key={version.id}
              className={`flex items-baseline justify-between gap-3 px-4 py-3 ${
                i !== 0 ? "border-t border-white/6" : ""
              }`}
            >
              <div className="min-w-0">
                <span
                  className={
                    version.version === workflow.current_version
                      ? "font-semibold text-ember-400"
                      : "text-ink"
                  }
                >
                  v{version.version}
                </span>
                <span className="ml-3 text-xs text-ink-faint">
                  by {version.created_by}
                  {version.comment ? ` — ${version.comment}` : ""}
                </span>
              </div>
              <time className="shrink-0 text-xs text-ink-faint">
                {new Date(version.created_at).toLocaleString()}
              </time>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
