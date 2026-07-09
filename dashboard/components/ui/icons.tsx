// Inline, tree-shakeable SVG icons (Lucide-style, 24x24, currentColor stroke).
// Kept local so the site has zero icon-font/CDN dependency.
import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Base({ children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const Sparkles = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3l1.9 4.6L18.5 9.5 13.9 11.4 12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3z" />
    <path d="M19 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8.8-2z" />
  </Base>
);

export const ShieldCheck = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" />
    <path d="M9 12l2 2 4-4" />
  </Base>
);

export const Activity = (p: IconProps) => (
  <Base {...p}>
    <path d="M3 12h4l3 8 4-16 3 8h4" />
  </Base>
);

export const GitBranch = (p: IconProps) => (
  <Base {...p}>
    <circle cx="6" cy="6" r="2.5" />
    <circle cx="6" cy="18" r="2.5" />
    <circle cx="18" cy="8" r="2.5" />
    <path d="M6 8.5v7M18 10.5c0 4-6 2-6 5.5" />
  </Base>
);

export const Bot = (p: IconProps) => (
  <Base {...p}>
    <rect x="4" y="8" width="16" height="11" rx="3" />
    <path d="M12 8V4M8 3.5h8" />
    <circle cx="9" cy="13" r="1" fill="currentColor" stroke="none" />
    <circle cx="15" cy="13" r="1" fill="currentColor" stroke="none" />
  </Base>
);

export const Gauge = (p: IconProps) => (
  <Base {...p}>
    <path d="M4 18a8 8 0 1 1 16 0" />
    <path d="M12 18l4-5" />
  </Base>
);

export const Workflow = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="4" width="7" height="6" rx="1.5" />
    <rect x="14" y="14" width="7" height="6" rx="1.5" />
    <path d="M6.5 10v3a2 2 0 0 0 2 2H14" />
  </Base>
);

export const ArrowRight = (p: IconProps) => (
  <Base {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Base>
);

export const ArrowUpRight = (p: IconProps) => (
  <Base {...p}>
    <path d="M7 17L17 7M8 7h9v9" />
  </Base>
);

export const Check = (p: IconProps) => (
  <Base {...p}>
    <path d="M4 12l5 5L20 6" />
  </Base>
);

export const Cpu = (p: IconProps) => (
  <Base {...p}>
    <rect x="6" y="6" width="12" height="12" rx="2" />
    <rect x="9" y="9" width="6" height="6" rx="1" />
    <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" />
  </Base>
);

export const Database = (p: IconProps) => (
  <Base {...p}>
    <ellipse cx="12" cy="5" rx="8" ry="3" />
    <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
    <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
  </Base>
);

export const Zap = (p: IconProps) => (
  <Base {...p}>
    <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" />
  </Base>
);

export const Terminal = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <path d="M7 9l3 3-3 3M13 15h4" />
  </Base>
);

export const Wrench = (p: IconProps) => (
  <Base {...p}>
    <path d="M15 6a4 4 0 0 1-5.2 5.2L5 16v3h3l4.8-4.8A4 4 0 0 0 18 9l-2 2-2-2 2-2a4 4 0 0 0-1-1z" />
  </Base>
);

export const Github = (p: IconProps) => (
  <Base {...p}>
    <path d="M9 19c-4 1.5-4-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" />
  </Base>
);

export const Linkedin = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <path d="M8 10v7M8 7v.01M12 17v-4a2 2 0 0 1 4 0v4M12 11v6" />
  </Base>
);

export const Calendar = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 9h18M8 3v4M16 3v4" />
  </Base>
);

export const Mail = (p: IconProps) => (
  <Base {...p}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="M4 7l8 6 8-6" />
  </Base>
);

export const Globe = (p: IconProps) => (
  <Base {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3c2.5 2.5 2.5 15 0 18M12 3c-2.5 2.5-2.5 15 0 18" />
  </Base>
);

export const Menu = (p: IconProps) => (
  <Base {...p}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Base>
);

export const X = (p: IconProps) => (
  <Base {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Base>
);

export const Rocket = (p: IconProps) => (
  <Base {...p}>
    <path d="M5 15c-1.5 1-2 5-2 5s4-.5 5-2a2.8 2.8 0 0 0-3-3z" />
    <path d="M9 12c1-5 5-9 11-9 0 6-4 10-9 11l-2-2z" />
    <circle cx="14.5" cy="9.5" r="1.5" />
  </Base>
);

export const Layers = (p: IconProps) => (
  <Base {...p}>
    <path d="M12 3l9 5-9 5-9-5 9-5z" />
    <path d="M3 13l9 5 9-5M3 16.5l9 5 9-5" opacity="0.55" />
  </Base>
);
