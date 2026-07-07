import HealthBadge from "@/components/HealthBadge";
import StatusPill from "@/components/StatusPill";
import { fetchHealth, fetchRuns, fetchVersions, fetchWorkflow } from "@/lib/api";

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
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{workflow.name}</h1>
          <p className="mt-1 text-xs text-zinc-500">
            v{workflow.current_version} · <StatusPill status={workflow.status} /> · engine id{" "}
            <span className="font-mono">{workflow.engine_workflow_id ?? "—"}</span>
          </p>
        </div>
        <HealthBadge status={health.status} />
      </header>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">
          Run timeline{" "}
          <span className="font-normal text-zinc-500">
            ({health.consecutive_failures} consecutive failure
            {health.consecutive_failures === 1 ? "" : "s"})
          </span>
        </h2>
        {runs.length === 0 ? (
          <p className="text-sm text-zinc-500">No runs recorded yet.</p>
        ) : (
          <ol className="relative space-y-0 border-l border-zinc-800 pl-5">
            {runs.map((run) => (
              <li key={run.id} className="relative py-2">
                <span
                  className={`absolute -left-[26px] top-3.5 h-2.5 w-2.5 rounded-full ${
                    run.status === "success"
                      ? "bg-emerald-500"
                      : run.status === "failed"
                        ? "bg-red-500"
                        : "bg-sky-500"
                  }`}
                />
                <div className="flex items-baseline justify-between">
                  <p className="text-sm">
                    <StatusPill status={run.status} />{" "}
                    <span className="font-mono text-xs text-zinc-500">
                      #{run.engine_execution_id}
                    </span>
                  </p>
                  <time className="text-xs text-zinc-500">
                    {new Date(run.started_at).toLocaleString()}
                  </time>
                </div>
                {run.error_message && (
                  <p className="mt-1 text-xs text-red-400/80">{run.error_message}</p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">Versions</h2>
        <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 text-sm">
          {versions.map((version) => (
            <li key={version.id} className="flex items-baseline justify-between px-4 py-2.5">
              <div>
                <span
                  className={
                    version.version === workflow.current_version
                      ? "font-semibold text-orange-400"
                      : "text-zinc-300"
                  }
                >
                  v{version.version}
                </span>
                <span className="ml-3 text-xs text-zinc-500">
                  by {version.created_by}
                  {version.comment ? ` — ${version.comment}` : ""}
                </span>
              </div>
              <time className="text-xs text-zinc-600">
                {new Date(version.created_at).toLocaleString()}
              </time>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
