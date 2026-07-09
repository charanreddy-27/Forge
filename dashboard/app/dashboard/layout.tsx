import Link from "next/link";
import { Wordmark } from "@/components/site/Logo";
import DashboardNav from "@/components/DashboardNav";
import { isDemo } from "@/lib/api";
import { ArrowUpRight } from "@/components/ui/icons";

// The dashboard's own shell — distinct from the marketing chrome. A slim top bar
// with the wordmark, section nav, and (in demo mode) a banner making clear the
// data is seeded.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/8 bg-base-950/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-3">
          <div className="flex items-center gap-8">
            <Link href="/" aria-label="Back to Forge home">
              <Wordmark />
            </Link>
            <DashboardNav />
          </div>
          <Link
            href="/"
            className="hidden items-center gap-1 text-sm text-ink-muted transition-colors hover:text-ink sm:inline-flex"
          >
            Back to site
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      {isDemo && (
        <div className="border-b border-ember-500/20 bg-ember-500/[0.06]">
          <div className="mx-auto flex max-w-6xl items-center gap-2 px-5 py-2 text-xs text-ember-200/90">
            <span className="inline-flex h-1.5 w-1.5 rounded-full bg-ember-400" />
            <span className="font-medium text-ember-300">Demo mode</span>
            <span className="text-ink-faint">
              — seeded data, no backend. Point <code className="font-mono">FORGE_API_URL</code> at a
              live agent layer to see real workflows.
            </span>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
    </div>
  );
}
