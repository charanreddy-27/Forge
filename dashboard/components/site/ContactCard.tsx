"use client";

import { useState } from "react";
import { profile } from "@/lib/profile";
import { ArrowUpRight, Calendar, Github, Globe, Linkedin, Mail } from "@/components/ui/icons";

/**
 * Contact card mirroring the portfolio's energy. The message form has no backend
 * on Vercel, so it composes a mailto: — honest and functional without a server.
 */
export default function ContactCard() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  const mailto = `mailto:${profile.email}?subject=${encodeURIComponent(
    `Hello from ${name || "someone"} (via Forge)`,
  )}&body=${encodeURIComponent(`${message}\n\n— ${name}${email ? ` (${email})` : ""}`)}`;

  const actions = [
    { href: profile.cal, label: "Book a call", Icon: Calendar, primary: true },
    { href: `mailto:${profile.email}`, label: "Email", Icon: Mail },
    { href: profile.github, label: "GitHub", Icon: Github },
    { href: profile.linkedin, label: "LinkedIn", Icon: Linkedin },
    { href: profile.portfolio, label: "Portfolio", Icon: Globe },
  ];

  return (
    <div className="glass-strong overflow-hidden rounded-4xl p-8 shadow-card sm:p-10">
      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <h3 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Have an idea? <span className="text-gradient-ember">Let&apos;s talk.</span>
          </h3>
          <p className="mt-3 max-w-md text-ink-muted">
            Want to build something — or break something interesting? I&apos;m around. The fastest
            path is booking a call; the form works too.
          </p>

          <div className="mt-6 flex flex-wrap gap-2.5">
            {actions.map(({ href, label, Icon, primary }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                className={primary ? "btn-primary" : "btn-ghost"}
              >
                <Icon className="h-4 w-4" />
                {label}
              </a>
            ))}
          </div>

          <div className="mt-8 flex items-center gap-2 text-sm text-run-400">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-run-400 opacity-60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-run-500" />
            </span>
            Available for new projects
          </div>
        </div>

        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            window.location.href = mailto;
          }}
        >
          <Field label="Name" htmlFor="c-name">
            <input
              id="c-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="field"
              required
            />
          </Field>
          <Field label="Email" htmlFor="c-email">
            <input
              id="c-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="field"
            />
          </Field>
          <Field label="Message" htmlFor="c-msg">
            <textarea
              id="c-msg"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="What are we building?"
              rows={4}
              className="field resize-none"
              required
            />
          </Field>
          <button type="submit" className="btn-primary w-full">
            Send message
            <ArrowUpRight className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-ink-faint">
        {label}
      </span>
      {children}
    </label>
  );
}
