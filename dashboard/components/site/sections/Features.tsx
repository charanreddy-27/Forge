import { Reveal } from "@/components/ui/Reveal";
import { Section, SectionHeading } from "./primitives";
import {
  Bot,
  Database,
  GitBranch,
  Gauge,
  ShieldCheck,
  Wrench,
} from "@/components/ui/icons";

const features = [
  {
    Icon: Bot,
    title: "Natural-language generator",
    body: "Describe an automation in a sentence. The agent turns it into schema-valid n8n workflow JSON — never hand-edited in the UI.",
    accent: "ember" as const,
    span: "lg:col-span-2",
  },
  {
    Icon: ShieldCheck,
    title: "Static validator",
    body: "Every generated workflow is checked before deploy: node types exist, connections resolve, credentials are referenced right, and destructive actions are blocked without an explicit approval flag.",
    accent: "cyan" as const,
    span: "lg:row-span-2",
  },
  {
    Icon: GitBranch,
    title: "Versioned registry",
    body: "Each deploy is an immutable version. Rollback to any previous one is a single API call — with a backup and audit entry written first.",
    accent: "ember" as const,
    span: "",
  },
  {
    Icon: Gauge,
    title: "Run monitor",
    body: "Executions are ingested and health is computed per workflow — success rate, streaks, last-run status — so failing automations surface instantly.",
    accent: "cyan" as const,
    span: "",
  },
  {
    Icon: Wrench,
    title: "Self-healing diagnostician",
    body: "On failure it pulls logs plus the workflow definition, writes a root-cause analysis, and proposes a patch. Low-risk fixes auto-apply; risky ones wait for you.",
    accent: "ember" as const,
    span: "lg:col-span-2",
  },
  {
    Icon: Database,
    title: "LLM gateway",
    body: "Every model call flows through one module: cost + token logging, a hard daily budget, exponential-backoff retries, and a local Ollama fallback.",
    accent: "cyan" as const,
    span: "",
  },
];

export default function Features() {
  return (
    <Section id="features">
      <SectionHeading
        kicker="What's inside"
        title={
          <>
            Six systems that turn intent into{" "}
            <span className="text-gradient-ember">running, monitored</span> automation.
          </>
        }
        blurb="n8n executes workflows. Forge is the brain on top — it decides what to build, whether it's safe, and what to do when it breaks."
      />

      <div className="mt-14 grid auto-rows-fr gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f, i) => (
          <Reveal
            key={f.title}
            delay={i * 60}
            className={`group relative overflow-hidden rounded-3xl border border-white/8 bg-white/[0.02] p-6 transition-colors duration-300 hover:border-white/16 hover:bg-white/[0.04] ${f.span}`}
          >
            <div
              className={`mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl ${
                f.accent === "ember"
                  ? "bg-ember-500/12 text-ember-400"
                  : "bg-cyan-500/12 text-cyan-400"
              }`}
            >
              <f.Icon className="h-6 w-6" />
            </div>
            <h3 className="font-display text-lg font-semibold text-ink">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">{f.body}</p>
            <div
              className={`pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100 ${
                f.accent === "ember" ? "bg-ember-500/20" : "bg-cyan-500/20"
              }`}
            />
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
