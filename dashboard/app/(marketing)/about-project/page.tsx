import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/components/ui/Reveal";
import { Section, SectionHeading } from "@/components/site/sections/primitives";
import { profile } from "@/lib/profile";
import { ArrowUpRight, Check, Github, Linkedin } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "About the project",
  description:
    "Why Forge exists, how it was built, the technical decisions behind it, and the part that broke everything.",
};

const timeline = [
  {
    date: "January 2026",
    title: "The 3am flameout",
    body: "A scraping automation died silently for a week and I only noticed when the data went stale. The itch: what if the automation could notice — and fix itself?",
  },
  {
    date: "February 2026",
    title: "Scoping & the four layers",
    body: "Wrote the first ADRs. Picked n8n as a swappable engine rather than building an executor from scratch. Drew the boundary: dashboard, stateless agent layer, data, engine.",
  },
  {
    date: "March 2026",
    title: "Foundation + the LLM gateway",
    body: "Docker Compose stack, Postgres schema with Alembic, and the single gateway every model call flows through — cost logging, retries, and a hard daily budget from day one.",
  },
  {
    date: "April 2026",
    title: "The generator — and the week validation ate me alive",
    body: "Turning English into workflow JSON was quick. Trusting that JSON was not. Half-valid graphs, phantom node types, a delete step with no approval flag. The validator became the real project.",
    hard: true,
  },
  {
    date: "May 2026",
    title: "Monitor + diagnostician",
    body: "Run ingestion, health computation, and the agent that reads a failure, writes a root cause, and proposes a patch — gated by a risk rubric so risky fixes wait for a human.",
  },
  {
    date: "June 2026",
    title: "Dashboard + hardening",
    body: "The Next.js control surface, then the unglamorous parts: rate limits, backups, structured logs, and a load test to prove the stateless design actually scales.",
  },
  {
    date: "July 2026",
    title: "Polish & launch",
    body: "Docs, a demo mode that runs with zero backend, and the site you're reading now.",
  },
];

const challenges = [
  {
    h: "Never trust generated JSON",
    p: "The validator statically checks node types against the engine, resolves every connection, verifies credential references, and blocks destructive actions unless an explicit approval flag is set. Generation without validation is a liability, not a feature.",
  },
  {
    h: "Repair without recklessness",
    p: "Auto-repair is gated by a risk rubric (ADR-004). Low-risk patches apply automatically; anything that touches credentials, deletes data, or rewrites logic waits for one-click human approval. Every action hits the audit trail first.",
  },
  {
    h: "Generation can't block the API",
    p: "Workflow generation is an LLM round-trip — too slow to hold a request open. It runs as a Redis-queued background job, so the API stays snappy and the work survives a restart.",
  },
  {
    h: "Nothing is ever silently destroyed",
    p: "Overwriting or deleting a workflow always writes a versioned backup and an audit entry first. Rollback to any prior version is a single API call.",
  },
];

const stack = [
  { name: "n8n", why: "Mature execution engine — kept swappable behind an adapter so the brain never depends on it." },
  { name: "FastAPI + Pydantic v2", why: "Typed, async, and self-documenting; schemas double as validation." },
  { name: "PostgreSQL + Redis", why: "Durable state and audit in Postgres; the job queue and cache in Redis." },
  { name: "Next.js 14 + Tailwind", why: "One codebase for the marketing site and the dashboard, deployable to Vercel." },
  { name: "Anthropic + Ollama", why: "A capable default with a local fallback — and one gateway costing every call." },
  { name: "Docker Compose", why: "The whole platform comes up with a single command." },
];

export default function AboutProjectPage() {
  return (
    <div className="pt-36 sm:pt-40">
      {/* why */}
      <Section className="!py-0">
        <Reveal className="mx-auto max-w-3xl text-center">
          <span className="kicker">About the project</span>
          <h1 className="mt-5 font-display text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            The automation that refuses to <span className="text-gradient-ember">fail quietly.</span>
          </h1>
          <div className="mt-6 space-y-4 text-left text-lg leading-relaxed text-ink-muted sm:text-center">
            <p>
              n8n already runs workflows. The itch Forge scratches is everything around that: deciding
              what to build from a sentence, proving it&apos;s safe before it ships, and — the part I
              actually cared about — noticing when a run breaks and repairing it without me.
            </p>
            <p>
              It&apos;s a platform for people who&apos;d rather supervise a system than babysit a pile
              of cron jobs.
            </p>
          </div>
        </Reveal>
      </Section>

      {/* timeline */}
      <Section>
        <SectionHeading kicker="How it came together" title="A build in seven beats" />
        <div className="relative mx-auto mt-14 max-w-3xl">
          <div className="absolute left-[19px] top-2 bottom-2 w-px bg-gradient-to-b from-ember-500/50 via-white/10 to-cyan-500/40 sm:left-1/2" />
          <div className="space-y-6">
            {timeline.map((t, i) => (
              <Reveal
                key={t.title}
                delay={i * 40}
                className={`relative flex gap-5 sm:w-1/2 sm:gap-0 ${
                  i % 2 === 0 ? "sm:ml-auto sm:pl-10" : "sm:mr-auto sm:flex-row-reverse sm:pr-10 sm:text-right"
                }`}
              >
                <span
                  className={`absolute top-1.5 z-10 flex h-10 w-10 items-center justify-center rounded-full border bg-base-900 ${
                    t.hard ? "border-ember-500/50 text-ember-400" : "border-white/12 text-cyan-400"
                  } left-0 sm:left-auto ${i % 2 === 0 ? "sm:-left-5" : "sm:-right-5"}`}
                >
                  <span className="font-mono text-xs">{String(i + 1).padStart(2, "0")}</span>
                </span>
                <div
                  className={`ml-14 flex-1 rounded-2xl border p-5 sm:ml-0 ${
                    t.hard
                      ? "border-ember-500/25 bg-ember-500/[0.05]"
                      : "border-white/8 bg-white/[0.02]"
                  }`}
                >
                  <p className="font-mono text-xs text-ink-faint">{t.date}</p>
                  <h3 className="mt-1 font-display text-lg font-semibold text-ink">{t.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{t.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* challenges */}
      <Section>
        <SectionHeading
          kicker="Interesting decisions"
          title={<>The problems worth <span className="text-gradient-cool">solving twice.</span></>}
        />
        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          {challenges.map((c, i) => (
            <Reveal
              key={c.h}
              delay={i * 60}
              className="rounded-3xl border border-white/8 bg-white/[0.02] p-6"
            >
              <h3 className="font-display text-lg font-semibold text-ink">{c.h}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">{c.p}</p>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* stack */}
      <Section>
        <SectionHeading kicker="The stack" title="Why each piece is here" />
        <div className="mx-auto mt-12 max-w-3xl divide-y divide-white/8 overflow-hidden rounded-3xl border border-white/8">
          {stack.map((s, i) => (
            <Reveal
              key={s.name}
              delay={i * 40}
              className="flex flex-col gap-1 p-5 sm:flex-row sm:items-baseline sm:gap-6"
            >
              <div className="flex shrink-0 items-center gap-2 sm:w-56">
                <Check className="h-4 w-4 text-run-400" />
                <span className="font-mono text-sm font-medium text-ink">{s.name}</span>
              </div>
              <p className="text-sm text-ink-muted">{s.why}</p>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* project links + CTA */}
      <Section>
        <Reveal className="relative overflow-hidden rounded-4xl border border-white/10 bg-mesh p-10 text-center sm:p-14">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Want to build something — or collaborate?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-ink-muted">
            The source is on GitHub. If you&apos;re working on agentic systems, workflow tooling, or
            just want to trade notes, I&apos;m easy to reach.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <a href={profile.repo} target="_blank" rel="noreferrer" className="btn-primary px-6 py-3">
              <Github className="h-5 w-5" />
              GitHub repo
            </a>
            {/* LinkedIn post — placeholder until the write-up is live. */}
            <a
              href={profile.linkedin}
              target="_blank"
              rel="noreferrer"
              className="btn-ghost px-6 py-3"
            >
              <Linkedin className="h-5 w-5" />
              LinkedIn write-up
            </a>
            <Link href="/about" className="btn-ghost px-6 py-3">
              About the developer
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>
        </Reveal>
      </Section>
    </div>
  );
}
