import type { Metadata, Viewport } from "next";
import { DM_Sans, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

// Self-hosted at build time (no runtime Google request, no layout shift).
const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});
const sans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-sans",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

const SITE = "https://forge-ops.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: {
    default: "Forge — the AI operations platform that repairs its own workflows",
    template: "%s · Forge",
  },
  description:
    "Forge is a self-hosted AI operations platform. Describe an automation in plain English; an agent layer generates it, validates it, deploys it to n8n, watches every run, and repairs failures on its own.",
  keywords: [
    "AI operations",
    "workflow automation",
    "n8n",
    "LLM agents",
    "self-healing workflows",
    "FastAPI",
    "Next.js",
  ],
  authors: [{ name: "Chanda Charan Reddy", url: "https://www.charanreddy.dev" }],
  creator: "Chanda Charan Reddy",
  openGraph: {
    type: "website",
    url: SITE,
    title: "Forge — the AI operations platform that repairs its own workflows",
    description:
      "Describe an automation in plain English. An agent layer generates it, validates it, deploys it, and repairs failures on its own.",
    siteName: "Forge",
  },
  twitter: {
    card: "summary_large_image",
    title: "Forge — AI operations platform",
    description:
      "Describe an automation in plain English. Forge's agent layer generates, deploys, monitors, and repairs it.",
    creator: "@charanreddy_27",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#0A0E15",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
