import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Forge",
  description: "Personal AI operations platform",
};

const nav = [
  { href: "/", label: "Workflows" },
  { href: "/incidents", label: "Incidents" },
  { href: "/costs", label: "Costs" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <header className="border-b border-zinc-800">
          <div className="mx-auto flex max-w-5xl items-center gap-8 px-6 py-4">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              <span className="text-orange-500">⚒</span> Forge
            </Link>
            <nav className="flex gap-5 text-sm text-zinc-400">
              {nav.map((item) => (
                <Link key={item.href} href={item.href} className="hover:text-zinc-100">
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
