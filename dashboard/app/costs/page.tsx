import CostChart from "@/components/CostChart";
import { fetchCosts } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CostsPage() {
  const summary = await fetchCosts(14);
  const budgetUsed = Math.min(summary.spend_today_usd / summary.budget_usd, 1);

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">LLM costs</h1>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-zinc-300">Today&apos;s budget</h2>
          <p className="text-sm text-zinc-400">
            ${summary.spend_today_usd.toFixed(2)} of ${summary.budget_usd.toFixed(2)}
          </p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-800">
          <div
            className={`h-full ${budgetUsed >= 1 ? "bg-red-500" : budgetUsed > 0.8 ? "bg-amber-500" : "bg-emerald-500"}`}
            style={{ width: `${budgetUsed * 100}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-zinc-600">
          Calls are refused once the budget is reached (hard stop, resets at UTC midnight).
        </p>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="mb-4 text-sm font-semibold text-zinc-300">
          Daily spend (last {summary.days} days)
        </h2>
        <CostChart summary={summary} />
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">By service</h2>
        {summary.by_service.length === 0 ? (
          <p className="text-sm text-zinc-500">No LLM calls yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-zinc-500">
                <th className="pb-2 font-normal">Service</th>
                <th className="pb-2 text-right font-normal">Calls</th>
                <th className="pb-2 text-right font-normal">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {summary.by_service.map((row) => (
                <tr key={row.service}>
                  <td className="py-2 font-mono text-xs">{row.service}</td>
                  <td className="py-2 text-right text-zinc-400">{row.calls}</td>
                  <td className="py-2 text-right">${row.cost_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
