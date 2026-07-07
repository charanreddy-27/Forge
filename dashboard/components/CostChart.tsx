// Pure-Tailwind bar chart — no chart library, per "nothing beyond Tailwind".
import type { CostSummary } from "@/lib/api";

export default function CostChart({ summary }: { summary: CostSummary }) {
  const max = Math.max(...summary.daily.map((day) => day.cost_usd), 0.0001);

  return (
    <div>
      <div className="flex h-40 items-end gap-1.5">
        {summary.daily.map((day) => (
          <div key={day.date} className="group relative flex-1">
            <div
              className="w-full rounded-t bg-orange-600/80 transition-colors group-hover:bg-orange-500"
              style={{ height: `${Math.max((day.cost_usd / max) * 160, 3)}px` }}
            />
            <div className="pointer-events-none absolute -top-10 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-200 group-hover:block">
              {day.date}: ${day.cost_usd.toFixed(4)} ({day.calls} calls)
            </div>
          </div>
        ))}
        {summary.daily.length === 0 && (
          <p className="text-sm text-zinc-500">No LLM calls in this window yet.</p>
        )}
      </div>
      {summary.daily.length > 0 && (
        <div className="mt-2 flex justify-between text-xs text-zinc-600">
          <span>{summary.daily[0].date}</span>
          <span>{summary.daily[summary.daily.length - 1].date}</span>
        </div>
      )}
    </div>
  );
}
