import Hero from "@/components/site/sections/Hero";
import Features from "@/components/site/sections/Features";
import HowItWorks from "@/components/site/sections/HowItWorks";
import Architecture from "@/components/site/sections/Architecture";
import DemoPreview from "@/components/site/sections/DemoPreview";
import Closing from "@/components/site/sections/Closing";

const stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "n8n", "Next.js", "Anthropic", "Docker"];

export default function LandingPage() {
  return (
    <>
      <Hero />

      {/* tech strip */}
      <div className="relative mx-auto mt-20 max-w-5xl px-5">
        <p className="text-center text-xs uppercase tracking-[0.2em] text-ink-faint">
          Built on a production stack
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-x-3 gap-y-2">
          {stack.map((s) => (
            <span
              key={s}
              className="rounded-full border border-white/8 bg-white/[0.02] px-4 py-1.5 font-mono text-sm text-ink-muted"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      <Features />
      <HowItWorks />
      <Architecture />
      <DemoPreview />
      <Closing />
    </>
  );
}
