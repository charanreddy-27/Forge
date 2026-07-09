import Link from "next/link";
import { profile } from "@/lib/profile";
import { Wordmark } from "./Logo";
import { Calendar, Github, Globe, Linkedin, Mail } from "@/components/ui/icons";

const social = [
  { href: profile.github, label: "GitHub", Icon: Github },
  { href: profile.linkedin, label: "LinkedIn", Icon: Linkedin },
  { href: profile.cal, label: "Book a call", Icon: Calendar },
  { href: `mailto:${profile.email}`, label: "Email", Icon: Mail },
  { href: profile.portfolio, label: "Portfolio", Icon: Globe },
];

const cols = [
  {
    title: "Product",
    links: [
      { href: "/#features", label: "Features" },
      { href: "/#how", label: "How it works" },
      { href: "/#architecture", label: "Architecture" },
      { href: "/dashboard", label: "Live demo" },
    ],
  },
  {
    title: "Project",
    links: [
      { href: "/about-project", label: "About the project" },
      { href: "/about", label: "About the developer" },
      { href: profile.repo, label: "Source on GitHub" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative mt-32 border-t border-white/8">
      <div className="mx-auto max-w-6xl px-5 py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <Wordmark />
            <p className="mt-4 max-w-xs text-sm text-ink-muted">
              A self-hosted AI operations platform that generates, deploys, monitors, and repairs its
              own workflows. Crafted with intent.
            </p>
            <div className="mt-5 flex gap-2">
              {social.map(({ href, label, Icon }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={label}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-ink-muted transition-colors duration-200 hover:border-white/25 hover:text-ink"
                >
                  <Icon className="h-[18px] w-[18px]" />
                </a>
              ))}
            </div>
          </div>

          {cols.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                {col.title}
              </h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-sm text-ink-muted transition-colors duration-200 hover:text-ink"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-white/8 pt-6 text-xs text-ink-faint sm:flex-row">
          <p>© {new Date().getFullYear()} {profile.name}. Crafted with intent.</p>
          <p>
            Built with Next.js, TypeScript & Tailwind — designed & shipped by{" "}
            <a href={profile.portfolio} target="_blank" rel="noreferrer" className="text-ink-muted hover:text-ink">
              {profile.short}
            </a>
            .
          </p>
        </div>
      </div>
    </footer>
  );
}
