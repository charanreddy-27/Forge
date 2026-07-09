import CostChart from "@/components/CostChart";
import { fetchCosts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CostsPage() {
  const summary = await fetchCosts(14);
  const budgetUsed = Math.min(summary.spend_today_usd / summary.budget_usd, 1);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">LLM costs</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Every model call flows through one gateway that logs tokens, latency, and dollars — and
          hard-stops at the daily budget.
        </p>
      </div>

      <section className="rounded-2xl border border-white/8 bg-white/[0.02] p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-ink-muted">Today&apos;s budget</h2>
          <p className="text-sm text-ink-muted">
            ${summary.spend_today_usd.toFixed(2)} of ${summary.budget_usd.toFixed(2)}
          </p>
        </div>
        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/8">
          <div
            className={`h-full rounded-full transition-all ${
              budgetUsed >= 1 ? "bg-ember-500" : budgetUsed > 0.8 ? "bg-amber-500" : "bg-run-500"
            }`}
            style={{ width: `${budgetUsed * 100}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-ink-faint">
          Calls are refused once the budget is reached (hard stop, resets at UTC midnight).
        </p>
      </section>

      <section className="rounded-2xl border border-white/8 bg-white/[0.02] p-5">
        <h2 className="mb-4 text-sm font-semibold text-ink-muted">
          Daily spend (last {summary.days} days)
        </h2>
        <CostChart summary={summary} />
      </section>

      <section className="rounded-2xl border border-white/8 bg-white/[0.02] p-5">
        <h2 className="mb-3 text-sm font-semibold text-ink-muted">By service</h2>
        {summary.by_service.length === 0 ? (
          <p className="text-sm text-ink-faint">No LLM calls yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-faint">
                <th className="pb-2 font-normal">Service</th>
                <th className="pb-2 text-right font-normal">Calls</th>
                <th className="pb-2 text-right font-normal">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/6">
              {summary.by_service.map((row) => (
                <tr key={row.service}>
                  <td className="py-2.5 font-mono text-xs text-ink">{row.service}</td>
                  <td className="py-2.5 text-right text-ink-muted">{row.calls}</td>
                  <td className="py-2.5 text-right text-ink">${row.cost_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
