import Link from "next/link";
import { Reveal } from "@/components/ui/Reveal";
import { Section, SectionHeading } from "./primitives";
import { ArrowUpRight } from "@/components/ui/icons";

// A faithful, self-contained mock of the dashboard — no data fetch, so it reads
// as a "screenshot" on the marketing page while the real thing lives at /dashboard.
const rows = [
  { name: "ml-jobs-outreach", ver: 3, rate: 98, status: "healthy" },
  { name: "rss-digest-email", ver: 1, rate: 100, status: "healthy" },
  { name: "hourly-health-check", ver: 5, rate: 82, status: "degraded" },
  { name: "webhook-slack-alert", ver: 2, rate: 61, status: "failing" },
];

const bars = [3, 5, 4, 6, 8, 5, 7, 9, 6, 8, 11, 9, 12, 10];

const dot: Record<string, string> = {
  healthy: "bg-run-500",
  degraded: "bg-amber-500",
  failing: "bg-ember-500",
};

export default function DemoPreview() {
  return (
    <Section>
      <SectionHeading
        kicker="See it live"
        title={
          <>
            The whole thing runs in your browser — <span className="text-gradient-cool">no backend required.</span>
          </>
        }
        blurb="The live demo is seeded with realistic workflows, runs, incidents, and cost data so you can click through every surface exactly as it behaves in production."
      />

      <Reveal className="mt-14">
        <div className="glass-strong overflow-hidden rounded-4xl p-2 shadow-lift">
          <div className="rounded-[1.6rem] border border-white/8 bg-base-950/80 p-5 sm:p-7">
            {/* stat row */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Workflows", value: "12" },
                { label: "Open incidents", value: "2", warn: true },
                { label: "Spend today", value: "$3.41 / $8.00" },
              ].map((s) => (
                <div key={s.label} className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
                  <p className="text-xs text-ink-faint">{s.label}</p>
                  <p
                    className={`mt-1 font-display text-lg font-semibold sm:text-xl ${
                      s.warn ? "text-amber-400" : "text-ink"
                    }`}
                  >
                    {s.value}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-5 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
              {/* workflow list */}
              <div className="rounded-2xl border border-white/8">
                {rows.map((r, i) => (
                  <div
                    key={r.name}
                    className={`flex items-center justify-between px-4 py-3 ${
                      i !== rows.length - 1 ? "border-b border-white/6" : ""
                    }`}
                  >
                    <div>
                      <p className="font-mono text-sm text-ink">{r.name}</p>
                      <p className="mt-0.5 text-xs text-ink-faint">v{r.ver} · active</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-ink-muted">{r.rate}% ok</span>
                      <span className={`h-2.5 w-2.5 rounded-full ${dot[r.status]}`} />
                    </div>
                  </div>
                ))}
              </div>

              {/* cost chart */}
              <div className="rounded-2xl border border-white/8 p-4">
                <p className="text-xs text-ink-faint">LLM spend · 14 days</p>
                <div className="mt-4 flex h-28 items-end gap-1.5">
                  {bars.map((b, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-t bg-ember-grad"
                      style={{ height: `${(b / 12) * 100}%`, opacity: 0.55 + (i / bars.length) * 0.45 }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-center">
          <Link href="/dashboard" className="btn-primary px-6 py-3 text-base">
            Open the live demo
            <ArrowUpRight className="h-5 w-5" />
          </Link>
        </div>
      </Reveal>
    </Section>
  );
}
