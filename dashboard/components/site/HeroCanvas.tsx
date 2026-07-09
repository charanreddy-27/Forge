"use client";

import { useEffect, useRef } from "react";

/**
 * The hero's 3D "workflow constellation".
 *
 * A graph of nodes floating in a 3D volume, rotated slowly and projected to 2D
 * with perspective. Nearby nodes are wired together; bright "signal" pulses
 * travel along a subset of edges to evoke data flowing through live workflows —
 * the thing Forge actually does. Hand-rolled on a single <canvas> so there's no
 * WebGL/Three.js dependency: tiny bundle, fast first paint, reliable on Vercel.
 *
 * Honors prefers-reduced-motion by drawing one static frame and stopping.
 */

type Node = { x: number; y: number; z: number; hue: number };
type Edge = { a: number; b: number };
type Pulse = { edge: number; t: number; speed: number };

const EMBER = { r: 255, g: 106, b: 43 };
const CYAN = { r: 34, g: 211, b: 238 };

function mix(a: typeof EMBER, b: typeof CYAN, t: number) {
  return {
    r: Math.round(a.r + (b.r - a.r) * t),
    g: Math.round(a.g + (b.g - a.g) * t),
    b: Math.round(a.b + (b.b - a.b) * t),
  };
}

export default function HeroCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (canvasRef.current === null) return;
    // Non-null aliases so the nested render closures don't re-widen to null.
    const canvas: HTMLCanvasElement = canvasRef.current;
    const maybeCtx = canvas.getContext("2d");
    if (maybeCtx === null) return;
    const ctx: CanvasRenderingContext2D = maybeCtx;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const parent = canvas.parentElement as HTMLElement;

    // --- Build the graph -------------------------------------------------
    const COUNT = 44;
    const nodes: Node[] = Array.from({ length: COUNT }, (_, i) => ({
      x: (Math.random() * 2 - 1) * 1.15,
      y: (Math.random() * 2 - 1) * 0.85,
      z: (Math.random() * 2 - 1) * 1.15,
      hue: i / COUNT,
    }));

    const edges: Edge[] = [];
    for (let i = 0; i < COUNT; i++) {
      for (let j = i + 1; j < COUNT; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dz = nodes[i].z - nodes[j].z;
        if (Math.hypot(dx, dy, dz) < 0.62) edges.push({ a: i, b: j });
      }
    }

    const pulses: Pulse[] = Array.from({ length: Math.min(14, edges.length) }, () => ({
      edge: Math.floor(Math.random() * edges.length),
      t: Math.random(),
      speed: 0.14 + Math.random() * 0.22,
    }));

    // --- Sizing ----------------------------------------------------------
    let width = 0;
    let height = 0;
    let dpr = 1;
    function resize() {
      const rect = parent.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(width * dpr));
      canvas.height = Math.max(1, Math.floor(height * dpr));
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(parent);

    // --- Mouse parallax --------------------------------------------------
    const target = { x: 0, y: 0 };
    const cur = { x: 0, y: 0 };
    function onMove(e: MouseEvent) {
      const rect = parent.getBoundingClientRect();
      target.x = ((e.clientX - rect.left) / rect.width - 0.5) * 0.6;
      target.y = ((e.clientY - rect.top) / rect.height - 0.5) * 0.6;
    }
    window.addEventListener("mousemove", onMove);

    // --- Render loop -----------------------------------------------------
    let raf = 0;
    let last = performance.now();
    let rot = 0;

    function project(n: Node, ry: number, rx: number) {
      // rotate around Y then X
      const cosY = Math.cos(ry);
      const sinY = Math.sin(ry);
      let x = n.x * cosY - n.z * sinY;
      let z = n.x * sinY + n.z * cosY;
      const cosX = Math.cos(rx);
      const sinX = Math.sin(rx);
      let y = n.y * cosX - z * sinX;
      z = n.y * sinX + z * cosX;
      const focal = 3.2;
      const scale = focal / (focal - z);
      const min = Math.min(width, height);
      return {
        sx: width / 2 + x * scale * min * 0.34,
        sy: height / 2 + y * scale * min * 0.34,
        depth: (z + 1.6) / 3.2, // 0 (far) .. 1 (near)
        scale,
      };
    }

    function frame(now: number) {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      cur.x += (target.x - cur.x) * 0.05;
      cur.y += (target.y - cur.y) * 0.05;
      if (!reduced) rot += dt * 0.12;

      const ry = rot + cur.x;
      const rx = -0.18 + cur.y;

      ctx.clearRect(0, 0, width, height);

      const P = nodes.map((n) => project(n, ry, rx));

      // edges
      for (const e of edges) {
        const a = P[e.a];
        const b = P[e.b];
        const d = (a.depth + b.depth) / 2;
        ctx.strokeStyle = `rgba(148,163,184,${0.04 + d * 0.14})`;
        ctx.lineWidth = 0.6 + d * 0.6;
        ctx.beginPath();
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.stroke();
      }

      // pulses travelling along edges
      for (const p of pulses) {
        if (!reduced) {
          p.t += p.speed * dt;
          if (p.t > 1) {
            p.t = 0;
            p.edge = Math.floor(Math.random() * edges.length);
          }
        }
        const e = edges[p.edge];
        if (!e) continue;
        const a = P[e.a];
        const b = P[e.b];
        const px = a.sx + (b.sx - a.sx) * p.t;
        const py = a.sy + (b.sy - a.sy) * p.t;
        const c = mix(EMBER, CYAN, (nodes[e.a].hue + nodes[e.b].hue) / 2);
        const r = 2.4;
        const g = ctx.createRadialGradient(px, py, 0, px, py, r * 5);
        g.addColorStop(0, `rgba(${c.r},${c.g},${c.b},0.9)`);
        g.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(px, py, r * 5, 0, Math.PI * 2);
        ctx.fill();
      }

      // nodes (near ones drawn brighter/larger)
      const order = P.map((_, i) => i).sort((i, j) => P[i].depth - P[j].depth);
      for (const i of order) {
        const p = P[i];
        const c = mix(EMBER, CYAN, nodes[i].hue);
        const r = (1.3 + p.depth * 2.6) * p.scale;
        const glow = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, r * 6);
        glow.addColorStop(0, `rgba(${c.r},${c.g},${c.b},${0.25 + p.depth * 0.45})`);
        glow.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0)`);
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, r * 6, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = `rgba(${c.r},${c.g},${c.b},${0.5 + p.depth * 0.5})`;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, r, 0, Math.PI * 2);
        ctx.fill();
      }

      if (!reduced) raf = requestAnimationFrame(frame);
    }

    raf = requestAnimationFrame(frame);
    if (reduced) {
      // draw a single settled frame
      cancelAnimationFrame(raf);
      frame(performance.now());
    }

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden="true"
    />
  );
}
