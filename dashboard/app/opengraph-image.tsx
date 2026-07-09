import { ImageResponse } from "next/og";

// Rendered at build time into the OG/Twitter card. Uses system fonts only so
// it never depends on a runtime font fetch.
export const runtime = "edge";
export const alt = "Forge — the AI operations platform that repairs its own workflows";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px",
          background:
            "radial-gradient(1000px 500px at 15% -10%, rgba(255,106,43,0.35), transparent 60%), radial-gradient(900px 500px at 100% 120%, rgba(139,92,246,0.30), transparent 60%), #0A0E15",
          fontFamily: "sans-serif",
          color: "#E7ECF3",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: "linear-gradient(135deg,#FF7A3D,#FFB020)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 34,
              fontWeight: 800,
              color: "#0A0E15",
            }}
          >
            ⚒
          </div>
          <div style={{ fontSize: 34, fontWeight: 700, letterSpacing: -0.5 }}>Forge</div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div
            style={{
              fontSize: 68,
              fontWeight: 800,
              lineHeight: 1.05,
              letterSpacing: -2,
              maxWidth: 900,
            }}
          >
            The AI operations platform that{" "}
            <span style={{ color: "#FF7A3D" }}>repairs its own workflows.</span>
          </div>
          <div style={{ fontSize: 30, color: "#9AA7B8", maxWidth: 860 }}>
            Describe an automation in plain English. An agent layer generates it, deploys it to n8n,
            and fixes failures on its own.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 24, color: "#9AA7B8" }}>
          <span>Chanda Charan Reddy</span>
          <span style={{ color: "#334155" }}>•</span>
          <span>charanreddy.dev</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
