import Link from "next/link";
import { Reveal } from "@/components/ui/Reveal";
import ContactCard from "@/components/site/ContactCard";
import { Section } from "./primitives";
import { ArrowUpRight } from "@/components/ui/icons";
import { profile } from "@/lib/profile";

export default function Closing() {
  return (
    <Section id="contact">
      {/* Portfolio tease — a door, not a billboard. */}
      <Reveal className="relative mb-16 overflow-hidden rounded-4xl border border-white/10 bg-mesh p-10 text-center sm:p-16">
        <p className="mx-auto max-w-2xl font-display text-2xl font-semibold leading-snug tracking-tight sm:text-3xl">
          Forge is one project. There are 18 more — and a few jet engines —{" "}
          <Link
            href={profile.portfolio}
            className="text-gradient-ember underline-offset-4 hover:underline"
            target="_blank"
            rel="noreferrer"
          >
            over at charanreddy.dev
          </Link>
          .
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <a href={profile.portfolio} target="_blank" rel="noreferrer" className="btn-primary px-6 py-3">
            Visit the portfolio
            <ArrowUpRight className="h-5 w-5" />
          </a>
          <Link href="/about" className="btn-ghost px-6 py-3">
            Meet the developer
          </Link>
        </div>
      </Reveal>

      <ContactCard />
    </Section>
  );
}
