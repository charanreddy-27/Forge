// The Forge wordmark: an ember-gradient anvil-spark glyph + name. Reused in nav,
// footer, and dashboard shell so the brand reads identically everywhere.
export function LogoMark({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="forge-mark" x1="12" y1="10" x2="52" y2="54" gradientUnits="userSpaceOnUse">
          <stop stopColor="#FF7A3D" />
          <stop offset="0.5" stopColor="#FF6A2B" />
          <stop offset="1" stopColor="#FFB020" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="#0D131C" />
      <rect x="0.5" y="0.5" width="63" height="63" rx="14.5" stroke="#FF6A2B" strokeOpacity="0.35" />
      <path
        d="M16 33 H48 C46 40 41 44 33 44 H31 V50 H37 V54 H23 V50 H27 V44 C21 43 17 39 16 33 Z"
        fill="url(#forge-mark)"
      />
      <rect x="18" y="27" width="28" height="6" rx="2" fill="url(#forge-mark)" />
      <path d="M40 12 L36 24 L42 22 L38 32 L48 20 L42 22 L46 12 Z" fill="#FFC24B" />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <LogoMark className="h-8 w-8" />
      <span className="font-display text-lg font-bold tracking-tight text-ink">Forge</span>
    </span>
  );
}
