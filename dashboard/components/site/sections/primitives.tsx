import { Reveal } from "@/components/ui/Reveal";

// Consistent section rhythm (48px+ gaps per the design system) and a shared
// heading treatment so every section on the site reads as one family.
export function Section({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`mx-auto max-w-6xl scroll-mt-24 px-5 py-20 sm:py-28 ${className}`}>
      {children}
    </section>
  );
}

export function SectionHeading({
  kicker,
  title,
  blurb,
  align = "center",
}: {
  kicker: string;
  title: React.ReactNode;
  blurb?: React.ReactNode;
  align?: "center" | "left";
}) {
  return (
    <Reveal className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <span className="kicker">{kicker}</span>
      <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
        {title}
      </h2>
      {blurb && <p className="mt-4 text-lg text-ink-muted">{blurb}</p>}
    </Reveal>
  );
}
