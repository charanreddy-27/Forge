import type { Metadata } from "next";
import { Reveal } from "@/components/ui/Reveal";
import ContactCard from "@/components/site/ContactCard";
import { LogoMark } from "@/components/site/Logo";
import { profile } from "@/lib/profile";
import { ArrowUpRight, Calendar, Github, Globe, Linkedin } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "About the developer",
  description:
    "Chanda Charan Reddy — AI & Automation Engineer in Bangalore. Springer-published medical imaging, document pipelines that run themselves, and real-time control code for jet engines at DRDO.",
};

const learned = [
  {
    h: "Generation is the easy 20%.",
    p: "Getting an LLM to emit workflow JSON took an afternoon. The other 80% — validating it, versioning it, catching destructive actions, and rolling back cleanly — is where the real system lives.",
  },
  {
    h: "A failing automation should page a machine first, not a human.",
    p: "The diagnostician exists because I got tired of being the on-call for my own scripts. Root-cause and a proposed patch, computed automatically, with a human gate only when the risk is real.",
  },
  {
    h: "Cost is a first-class metric, not an afterthought.",
    p: "Every LLM call goes through one gateway that logs tokens, latency, and dollars, and hard-stops at a daily budget. You can't optimize what you don't measure — and you can't sleep if you can't cap it.",
  },
  {
    h: "Stateless is a design decision you make on day one.",
    p: "Push every bit of state into Postgres and Redis early and horizontal scale is free later. Retrofit it and you're rewriting.",
  },
  {
    h: "The boring parts are the product.",
    p: "Audit trails, backups, idempotent jobs. Nobody demos them. They're the difference between a weekend hack and something you'd actually let run unattended.",
  },
];

const links = [
  { href: profile.github, label: "GitHub", Icon: Github },
  { href: profile.linkedin, label: "LinkedIn", Icon: Linkedin },
  { href: profile.cal, label: "Book a call", Icon: Calendar },
  { href: profile.portfolio, label: "Portfolio", Icon: Globe },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-5 pb-24 pt-36 sm:pt-40">
      <Reveal>
        <span className="kicker">About the developer</span>
        <h1 className="mt-5 font-display text-4xl font-bold tracking-tight sm:text-5xl">
          Hi, I&apos;m Charan.
        </h1>
        <div className="mt-6 space-y-4 text-lg leading-relaxed text-ink-muted">
          <p>
            I&apos;m an AI &amp; automation engineer in Bangalore who ships production LLM systems —
            from a Springer-published model that reads chest X-rays well enough for a radiologist to
            take seriously, to document pipelines that quietly run themselves.
          </p>
          <p>
            Before any of that, I wrote real-time control code for jet engines at DRDO. That job
            teaches you a specific kind of paranoia: a millisecond of lag isn&apos;t a bug — it&apos;s
            a flameout. I brought that instinct to Forge. An automation that fails silently at 3am is
            its own kind of flameout, so I built the thing to notice, diagnose, and fix itself before
            I wake up.
          </p>
          <p>
            Forge is what happens when you&apos;re tired of being the on-call engineer for your own
            side projects and decide to hand that job to an agent instead.
          </p>
        </div>
      </Reveal>

      {/* quick facts */}
      <Reveal delay={80} className="mt-10 grid gap-3 sm:grid-cols-3">
        {[
          { k: "Based in", v: profile.location },
          { k: "Focus", v: "AI systems & automation" },
          { k: "Past life", v: "Jet-engine control · DRDO" },
        ].map((f) => (
          <div key={f.k} className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
            <p className="text-xs uppercase tracking-wider text-ink-faint">{f.k}</p>
            <p className="mt-1 text-sm font-medium text-ink">{f.v}</p>
          </div>
        ))}
      </Reveal>

      {/* what I learned */}
      <div className="mt-16">
        <Reveal>
          <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            What I learned building this
          </h2>
        </Reveal>
        <div className="mt-6 space-y-3">
          {learned.map((l, i) => (
            <Reveal
              key={l.h}
              delay={i * 60}
              className="rounded-2xl border border-white/8 bg-white/[0.02] p-5"
            >
              <h3 className="font-display text-lg font-semibold text-ink">{l.h}</h3>
              <p className="mt-1.5 text-ink-muted">{l.p}</p>
            </Reveal>
          ))}
        </div>
      </div>

      {/* collaboration line + links */}
      <Reveal delay={60} className="mt-16 flex flex-col items-start gap-6 rounded-4xl border border-white/10 bg-white/[0.02] p-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <LogoMark className="h-12 w-12" />
          <div>
            <p className="font-display text-lg font-semibold text-ink">
              Want to build something — or break something interesting?
            </p>
            <p className="text-ink-muted">Let&apos;s talk.</p>
          </div>
        </div>
      </Reveal>

      <Reveal delay={80} className="mt-4 flex flex-wrap gap-2.5">
        {links.map(({ href, label, Icon }) => (
          <a key={label} href={href} target="_blank" rel="noreferrer" className="btn-ghost">
            <Icon className="h-4 w-4" />
            {label}
            <ArrowUpRight className="h-3.5 w-3.5 opacity-60" />
          </a>
        ))}
      </Reveal>

      <div className="mt-20">
        <ContactCard />
      </div>
    </div>
  );
}
