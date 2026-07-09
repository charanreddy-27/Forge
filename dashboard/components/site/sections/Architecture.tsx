import { Reveal } from "@/components/ui/Reveal";
import { Section, SectionHeading } from "./primitives";
import { Layers, Cpu, Database, Workflow } from "@/components/ui/icons";

const layers = [
  {
    Icon: Layers,
    name: "Dashboard",
    tech: "Next.js 14 · TypeScript · Tailwind",
    body: "The control surface — workflow health, run timelines, the incident feed, cost charts, and the chat box that drives the agent.",
    accent: "text-cyan-400 border-cyan-500/25 bg-cyan-500/[0.06]",
  },
  {
    Icon: Cpu,
    name: "Agent layer",
    tech: "FastAPI · Pydantic v2 · Python 3.11",
    body: "Stateless brain: generator, validator, run-monitor, diagnostician. Scales horizontally because all state lives below it.",
    accent: "text-ember-400 border-ember-500/25 bg-ember-500/[0.06]",
  },
  {
    Icon: Database,
    name: "Data layer",
    tech: "PostgreSQL 16 · Redis 7",
    body: "Versioned workflow registry, run history, incidents, the full LLM cost log, and an audit trail — plus Redis for the job queue and cache.",
    accent: "text-violet-400 border-violet-500/25 bg-violet-500/[0.06]",
  },
  {
    Icon: Workflow,
    name: "Execution engine",
    tech: "n8n (self-hosted)",
    body: "The runtime, driven only through its REST API and isolated behind an engine adapter — so it's swappable without touching the brain.",
    accent: "text-run-400 border-run-500/25 bg-run-500/[0.06]",
  },
];

export default function Architecture() {
  return (
    <Section id="architecture">
      <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
        <SectionHeading
          align="left"
          kicker="Under the hood"
          title={
            <>
              Four clean layers. The engine is{" "}
              <span className="text-gradient-ember">swappable.</span>
            </>
          }
          blurb="Built stateless and horizontally scalable from day one: the API holds no state, generation runs off a Redis queue, and no n8n-specific logic leaks outside the adapter."
        />

        <div className="relative space-y-3">
          {/* connecting spine */}
          <div className="absolute left-[26px] top-6 bottom-6 w-px bg-gradient-to-b from-cyan-500/40 via-ember-500/40 to-run-500/40" />
          {layers.map((l, i) => (
            <Reveal
              key={l.name}
              delay={i * 80}
              className={`relative flex gap-4 rounded-2xl border p-5 backdrop-blur-sm ${l.accent}`}
            >
              <span className="relative z-10 flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl border border-white/10 bg-base-900">
                <l.Icon className="h-6 w-6" />
              </span>
              <div>
                <div className="flex flex-wrap items-baseline gap-x-3">
                  <h3 className="font-display text-lg font-semibold text-ink">{l.name}</h3>
                  <span className="font-mono text-xs text-ink-faint">{l.tech}</span>
                </div>
                <p className="mt-1 text-sm leading-relaxed text-ink-muted">{l.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </Section>
  );
}
