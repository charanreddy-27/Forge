import type { Config } from "tailwindcss";

/**
 * Forge design system — "fire + steel".
 *
 * A deep slate canvas (steel) lit by an ember/amber brand accent (the forge heat)
 * against a cool cyan→violet accent (the AI/agent layer). Every token below is
 * consumed by both the marketing site and the dashboard so the two read as one
 * product. Colors are exposed as CSS variables in globals.css so the same scale
 * can theme canvas/WebGL code too.
 */
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Steel — the canvas
        ink: {
          DEFAULT: "#E7ECF3",
          muted: "#9AA7B8",
          faint: "#64748B",
        },
        base: {
          950: "#080B11",
          900: "#0A0E15",
          850: "#0D131C",
          800: "#111925",
          700: "#18212F",
        },
        // Ember — the forge heat (brand)
        ember: {
          50: "#FFF3ED",
          100: "#FFE1D0",
          200: "#FFC1A1",
          300: "#FF9A6B",
          400: "#FF7A3D",
          500: "#FF6A2B", // primary
          600: "#F0510F",
          700: "#C43D0A",
          800: "#8F2D08",
          900: "#5E1F07",
        },
        amber: {
          400: "#FFC24B",
          500: "#FFB020",
        },
        // Cool — the agent layer
        cyan: {
          400: "#38E1F0",
          500: "#22D3EE",
          600: "#0EA5C4",
        },
        violet: {
          400: "#A78BFA",
          500: "#8B5CF6",
        },
        run: {
          400: "#4ADE80",
          500: "#34D399",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(255,106,43,0.25), 0 8px 40px -8px rgba(255,106,43,0.35)",
        "glow-cyan": "0 0 0 1px rgba(34,211,238,0.25), 0 8px 40px -8px rgba(34,211,238,0.30)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 20px 50px -20px rgba(0,0,0,0.7)",
        lift: "0 30px 80px -30px rgba(0,0,0,0.8)",
      },
      backgroundImage: {
        "ember-grad": "linear-gradient(135deg, #FF7A3D 0%, #FF6A2B 40%, #FFB020 100%)",
        "cool-grad": "linear-gradient(135deg, #22D3EE 0%, #8B5CF6 100%)",
        "mesh": "radial-gradient(60% 60% at 20% 0%, rgba(255,106,43,0.16) 0%, transparent 60%), radial-gradient(50% 50% at 90% 10%, rgba(34,211,238,0.14) 0%, transparent 55%), radial-gradient(60% 60% at 60% 100%, rgba(139,92,246,0.12) 0%, transparent 60%)",
        "grid": "linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "glow-pulse": {
          "0%,100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
        "gradient-pan": {
          "0%,100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.22,1,0.36,1) both",
        float: "float 6s ease-in-out infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "gradient-pan": "gradient-pan 6s ease infinite",
        marquee: "marquee 32s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
