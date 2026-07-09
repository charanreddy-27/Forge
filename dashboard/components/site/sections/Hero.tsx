import Link from "next/link";
import HeroCanvas from "@/components/site/HeroCanvas";
import { ArrowRight, Github, Sparkles } from "@/components/ui/icons";
import { profile } from "@/lib/profile";

export default function Hero() {
  return (
    <section className="relative isolate overflow-hidden pt-36 sm:pt-40">
      {/* animated 3D workflow constellation */}
      <div className="absolute inset-0 -z-10">
        <HeroCanvas />
        <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-b from-transparent to-base-950" />
      </div>

      <div className="mx-auto max-w-5xl px-5 text-center">
        <div className="flex justify-center animate-fade-up">
          <span className="kicker">
            <Sparkles className="h-3.5 w-3.5 text-ember-400" />
            Agentic workflow operations
          </span>
        </div>

        <h1
          className="mx-auto mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] tracking-tight animate-fade-up sm:text-6xl md:text-7xl"
          style={{ animationDelay: "60ms" }}
        >
          Automations that{" "}
          <span className="text-gradient-ember">write, deploy, and repair</span> themselves.
        </h1>

        <p
          className="mx-auto mt-6 max-w-2xl text-lg text-ink-muted animate-fade-up sm:text-xl"
          style={{ animationDelay: "120ms" }}
        >
          Forge is a self-hosted AI operations platform. Describe what you want in plain English —
          an agent layer generates a valid workflow, validates it, deploys it to n8n, watches every
          run, and fixes failures before you notice.
        </p>

        <div
          className="mt-9 flex flex-col items-center justify-center gap-3 animate-fade-up sm:flex-row"
          style={{ animationDelay: "180ms" }}
        >
          <Link href="/dashboard" className="btn-primary px-6 py-3 text-base">
            Explore the live demo
            <ArrowRight className="h-5 w-5" />
          </Link>
          <a
            href={profile.repo}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost px-6 py-3 text-base"
          >
            <Github className="h-5 w-5" />
            View the source
          </a>
        </div>

        <p
          className="mt-4 text-xs text-ink-faint animate-fade-up"
          style={{ animationDelay: "220ms" }}
        >
          No login. The demo runs on realistic sample data.
        </p>
      </div>

      {/* instruction → workflow terminal */}
      <div
        className="mx-auto mt-16 max-w-3xl px-5 animate-fade-up"
        style={{ animationDelay: "280ms" }}
      >
        <TerminalCard />
      </div>
    </section>
  );
}

function TerminalCard() {
  return (
    <div className="glass-strong overflow-hidden rounded-2xl shadow-card">
      <div className="flex items-center gap-2 border-b border-white/8 px-4 py-3">
        <span className="h-3 w-3 rounded-full bg-ember-500/80" />
        <span className="h-3 w-3 rounded-full bg-amber-500/70" />
        <span className="h-3 w-3 rounded-full bg-run-500/70" />
        <span className="ml-2 font-mono text-xs text-ink-faint">forge · agent layer</span>
      </div>
      <div className="space-y-3 p-5 text-left font-mono text-sm leading-relaxed">
        <p className="text-ink-muted">
          <span className="text-ember-400">you ›</span> watch for new ML job posts daily and draft
          cold emails to the hiring managers
        </p>
        <div className="hairline" />
        <ul className="space-y-1.5 text-ink-muted">
          <li>
            <span className="text-run-400">✓ generated</span> workflow{" "}
            <span className="text-ink">ml-jobs-outreach</span> · 5 nodes
          </li>
          <li>
            <span className="text-run-400">✓ validated</span> node types, connections, credentials
          </li>
          <li>
            <span className="text-run-400">✓ deployed</span> to n8n · version{" "}
            <span className="text-ink">v1</span> · scheduled daily 09:00
          </li>
          <li>
            <span className="text-cyan-400">◷ monitoring</span> runs — auto-repair armed
          </li>
        </ul>
      </div>
    </div>
  );
}
