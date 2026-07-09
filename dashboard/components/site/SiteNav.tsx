"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Wordmark } from "./Logo";
import { ArrowUpRight, Menu, X } from "@/components/ui/icons";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/#how", label: "How it works" },
  { href: "/#architecture", label: "Architecture" },
  { href: "/about-project", label: "The project" },
  { href: "/about", label: "About me" },
];

/**
 * Floating glass nav. Gains a stronger backdrop once the page is scrolled, and
 * collapses to a sheet on mobile. Kept off the very top edge (top-3) per the
 * design-system rule about floating navbars needing breathing room.
 */
export default function SiteNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="pointer-events-none fixed inset-x-0 top-3 z-50 flex justify-center px-3">
      <nav
        className={`pointer-events-auto flex w-full max-w-5xl items-center justify-between gap-4 rounded-2xl border px-4 py-2.5 transition-all duration-300 ${
          scrolled
            ? "border-white/10 bg-base-900/80 shadow-lift backdrop-blur-xl"
            : "border-white/[0.06] bg-white/[0.02] backdrop-blur-md"
        }`}
      >
        <Link href="/" aria-label="Forge home">
          <Wordmark />
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-full px-3 py-1.5 text-sm text-ink-muted transition-colors duration-200 hover:bg-white/5 hover:text-ink"
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Link href="/dashboard" className="btn-ghost hidden px-4 py-2 text-sm sm:inline-flex">
            Live demo
            <ArrowUpRight className="h-4 w-4" />
          </Link>
          <button
            type="button"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="btn-ghost h-10 w-10 !px-0 md:hidden"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="pointer-events-auto absolute inset-x-3 top-[68px] rounded-2xl border border-white/10 bg-base-900/95 p-2 shadow-lift backdrop-blur-xl md:hidden">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="block rounded-xl px-4 py-3 text-sm text-ink-muted transition-colors hover:bg-white/5 hover:text-ink"
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/dashboard"
            className="mt-1 block rounded-xl bg-ember-grad px-4 py-3 text-center text-sm font-semibold text-base-950"
          >
            Open the live demo
          </Link>
        </div>
      )}
    </div>
  );
}
