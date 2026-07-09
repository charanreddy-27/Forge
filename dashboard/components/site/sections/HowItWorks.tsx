import { Reveal } from "@/components/ui/Reveal";
import { Section, SectionHeading } from "./primitives";
import { Bot, ShieldCheck, Rocket, Activity, Wrench, Terminal } from "@/components/ui/icons";

const steps = [
  {
    Icon: Terminal,
    title: "Describe",
    body: "You type an instruction in plain English from the dashboard chat box.",
  },
  {
    Icon: Bot,
    title: "Generate",
    body: "A background job turns it into n8n workflow JSON via the LLM gateway.",
  },
  {
    Icon: ShieldCheck,
    title: "Validate",
    body: "Static checks confirm the graph is valid and nothing destructive slips through.",
  },
  {
    Icon: Rocket,
    title: "Deploy",
    body: "It's pushed to n8n as an immutable version, ready to run on schedule or webhook.",
  },
  {
    Icon: Activity,
    title: "Monitor",
    body: "Every run is ingested; health, success rate, and failure streaks are tracked.",
  },
  {
    Icon: Wrench,
    title: "Repair",
    body: "On failure the diagnostician finds the cause and patches it — or asks you first.",
  },
];

export default function HowItWorks() {
  return (
    <Section id="how" className="relative">
      <SectionHeading
        kicker="The loop"
        title={
          <>
            One instruction in. A{" "}
            <span className="text-gradient-cool">self-operating</span> workflow out.
          </>
        }
        blurb="The agent layer runs a closed loop. Generation happens as a queued job, so the API never blocks — and the loop keeps turning after you've walked away."
      />

      <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s, i) => (
          <Reveal
            key={s.title}
            delay={i * 70}
            className="relative rounded-3xl border border-white/8 bg-white/[0.02] p-6"
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-ink-faint">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="hairline flex-1" />
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-base-900 text-ember-400">
                <s.Icon className="h-5 w-5" />
              </span>
            </div>
            <h3 className="mt-4 font-display text-lg font-semibold">{s.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{s.body}</p>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
