"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Overview", exact: true },
  { href: "/dashboard/incidents", label: "Incidents" },
  { href: "/dashboard/costs", label: "Costs" },
];

export default function DashboardNav() {
  const pathname = usePathname();
  return (
    <nav className="flex items-center gap-1 text-sm">
      {nav.map((item) => {
        const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-full px-3 py-1.5 transition-colors duration-200 ${
              active ? "bg-white/8 text-ink" : "text-ink-muted hover:bg-white/5 hover:text-ink"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
