"use client";

import { useEffect, useRef } from "react";

/**
 * Particle-convergence intro. We rasterise the AgentShield silhouette (shield +
 * two-bar "A" + keyhole) to an offscreen canvas, sample its opaque pixels as
 * target points, then fly a glowing particle for each target from the edges
 * inward so the logo *assembles* out of noise. After convergence we flash and
 * hand off to the crisp vector mark (rendered on top by the parent).
 */

const VIEW_W = 100;
const VIEW_H = 118;

// Geometry mirrors ShieldMark so the assembled cloud matches the vector logo.
const SHIELD = "M50 5 L91 19 L91 58 C91 87 73 104 50 113 C27 104 9 87 9 58 L9 19 Z";
const LEG_L = "M33 86 L50 30";
const LEG_R = "M50 30 L67 86";

type Particle = {
  sx: number; sy: number; // spawn
  tx: number; ty: number; // target
  delay: number; dur: number;
  color: string; size: number;
};

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

function colorFor(fx: number, fy: number) {
  // Keyhole zone → magenta accent; otherwise cyan→blue→violet across x.
  if (fy > 0.52 && fx > 0.4 && fx < 0.6) return "#e94bd0";
  if (fx < 0.4) return "#38e1ff";
  if (fx < 0.58) return "#4f7cff";
  return "#a855f7";
}

export function ParticleShield({
  logoHeight = 240,
  assembleMs = 1600,
  onAssembled,
}: {
  logoHeight?: number;
  assembleMs?: number;
  onAssembled?: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const doneRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = window.innerWidth;
    const H = window.innerHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = `${W}px`;
    canvas.style.height = `${H}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    // Logo footprint, centred in the viewport.
    const logoH = Math.min(logoHeight, H * 0.6);
    const logoW = logoH * (VIEW_W / VIEW_H);
    const cx = W / 2;
    const cy = H / 2;
    const originX = cx - logoW / 2;
    const originY = cy - logoH / 2;
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    // 1) Rasterise silhouette to sample target points.
    const S = 3; // sampling resolution multiplier
    const off = document.createElement("canvas");
    off.width = VIEW_W * S;
    off.height = VIEW_H * S;
    const octx = off.getContext("2d");
    if (!octx) return;
    octx.scale(S, S);
    octx.fillStyle = "#fff";
    octx.strokeStyle = "#fff";
    octx.lineCap = "round";
    octx.lineJoin = "round";
    octx.fill(new Path2D(SHIELD));
    octx.lineWidth = 7.2;
    octx.stroke(new Path2D(LEG_L));
    octx.stroke(new Path2D(LEG_R));
    // apex + keyhole
    octx.fill(new Path2D("M45 46 L50 36 L55 46 Z"));
    octx.beginPath();
    octx.arc(50, 70, 6, 0, Math.PI * 2);
    octx.fill();
    octx.fill(new Path2D("M47 72 L53 72 L55 84 L45 84 Z"));

    const img = octx.getImageData(0, 0, off.width, off.height).data;
    const targets: { x: number; y: number; fx: number; fy: number }[] = [];
    const step = 2;
    for (let y = 0; y < off.height; y += step) {
      for (let x = 0; x < off.width; x += step) {
        const a = img[(y * off.width + x) * 4 + 3];
        if (a > 128) {
          const fx = x / off.width;
          const fy = y / off.height;
          targets.push({ x: originX + fx * logoW, y: originY + fy * logoH, fx, fy });
        }
      }
    }

    // Subsample to a performant count.
    const MAX = 1600;
    const chosen =
      targets.length > MAX
        ? targets.sort(() => Math.random() - 0.5).slice(0, MAX)
        : targets;

    // 2) Build particles spawning from anywhere across the whole page.
    const particles: Particle[] = chosen.map((t) => {
      const sx = (Math.random() * 1.3 - 0.15) * W;
      const sy = (Math.random() * 1.3 - 0.15) * H;
      const dist = Math.hypot(t.x - sx, t.y - sy);
      return {
        sx,
        sy,
        tx: t.x,
        ty: t.y,
        delay: Math.random() * 300,
        dur: 850 + dist * 0.18 + Math.random() * 260,
        color: colorFor(t.fx, t.fy),
        size: 0.9 + Math.random() * 1.4,
      };
    });

    // 3) Animate.
    let raf = 0;
    const start = performance.now();
    const render = (now: number) => {
      const elapsed = now - start;

      // Trail fade across the whole page.
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "rgba(4,6,13,0.30)";
      ctx.fillRect(0, 0, W, H);

      ctx.globalCompositeOperation = "lighter";
      for (const p of particles) {
        const local = Math.min(Math.max((elapsed - p.delay) / p.dur, 0), 1);
        const e = easeOutCubic(local);
        const x = p.sx + (p.tx - p.sx) * e;
        const y = p.sy + (p.ty - p.sy) * e;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.4 + 0.6 * local;
        ctx.beginPath();
        ctx.arc(x, y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      if (elapsed >= assembleMs && !doneRef.current) {
        doneRef.current = true;
        // Convergence flash centred on the logo.
        ctx.globalCompositeOperation = "lighter";
        const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, logoW * 1.6);
        g.addColorStop(0, "rgba(120,190,255,0.55)");
        g.addColorStop(1, "rgba(120,190,255,0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
        onAssembled?.();
      }

      // Keep rendering briefly past assembly to let the flash settle.
      if (elapsed < assembleMs + 500) raf = requestAnimationFrame(render);
    };
    raf = requestAnimationFrame(render);

    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden />;
}
