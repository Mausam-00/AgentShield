"use client";

import { useEffect, useRef } from "react";

/** Bounded, 30fps decorative network. No telemetry or assessment data is used. */
export function ParticleField({
  density = 0.00006,
  className = "",
}: {
  density?: number;
  className?: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) {
      console.warn("AgentShield: decorative canvas unavailable; retaining CSS background.");
      return;
    }
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const styles = getComputedStyle(document.documentElement);
    const colors = ["--neon-blue", "--neon-cyan"].map(name => styles.getPropertyValue(name).trim());
    type Point = { x: number; y: number; vx: number; vy: number; depth: number };
    let points: Point[] = [];
    let w = 0;
    let h = 0;
    let raf = 0;
    let last = 0;
    let phase = 0;
    let visible = false;
    const mouse = { x: -1000, y: -1000 };

    function draw(dt = 0) {
      phase += dt * .00013;
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        p.x = (p.x + p.vx * dt + w) % w;
        p.y = (p.y + p.vy * dt + h) % h;
        ctx.fillStyle = colors[i % colors.length];
        ctx.globalAlpha = .3 + p.depth * .35;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1 + p.depth, 0, Math.PI * 2);
        ctx.fill();
        for (let j = i + 1; j < points.length; j++) {
          const q = points[j];
          const distance = Math.hypot(p.x - q.x, p.y - q.y);
          if (distance > 160) continue;
          ctx.strokeStyle = colors[i % colors.length];
          ctx.globalAlpha = (1 - distance / 160) * .24;
          ctx.lineWidth = .7;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.stroke();
          if (i % 7 === 0) {
            const travel = (phase + i * .17) % 1;
            ctx.globalAlpha = (1 - distance / 160) * .7;
            ctx.beginPath();
            ctx.arc(p.x + (q.x - p.x) * travel, p.y + (q.y - p.y) * travel, 1.5, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        if (!reduced.matches && Math.hypot(mouse.x - p.x, mouse.y - p.y) < 150) {
          ctx.globalAlpha = .15;
          ctx.strokeStyle = colors[1];
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;
    }

    function frame(now: number) {
      if (!visible || document.hidden || reduced.matches) return;
      if (now - last >= 1000 / 30) {
        draw(last ? Math.min(now - last, 60) : 0);
        last = now;
      }
      raf = requestAnimationFrame(frame);
    }

    function sync() {
      cancelAnimationFrame(raf);
      last = 0;
      canvas.dataset.motion = reduced.matches ? "static" : visible && !document.hidden ? "animated" : "paused";
      if (visible && !document.hidden && !reduced.matches) raf = requestAnimationFrame(frame);
      else if (reduced.matches) draw();
    }

    function resize() {
      const parent = canvas.parentElement;
      w = Math.max(1, parent?.clientWidth ?? window.innerWidth);
      h = Math.max(1, parent?.clientHeight ?? window.innerHeight);
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(w < 640 ? 32 : 72, Math.max(18, Math.floor(w * h * density)));
      points = Array.from({ length: count }, (_, i) => ({
        x: ((i * .61803398875) % 1) * w,
        y: ((i * .41421356237 + .13) % 1) * h,
        vx: Math.sin(i * 2.3) * .012,
        vy: Math.cos(i * 1.7) * .009,
        depth: (i % 5) / 5,
      }));
      draw();
      sync();
    }

    function onMove(event: PointerEvent) {
      if (event.pointerType !== "mouse" || reduced.matches) return;
      const rect = canvas.getBoundingClientRect();
      mouse.x = event.clientX - rect.left;
      mouse.y = event.clientY - rect.top;
    }
    function onLeave() { mouse.x = mouse.y = -1000; }

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      sync();
    });
    const resizeObserver = new ResizeObserver(resize);
    resize();
    observer.observe(canvas);
    if (canvas.parentElement) resizeObserver.observe(canvas.parentElement);
    reduced.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    window.addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("pointerleave", onLeave);
    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      resizeObserver.disconnect();
      reduced.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerleave", onLeave);
    };
  }, [density]);

  return <canvas ref={ref} aria-hidden className={`pointer-events-none absolute inset-0 h-full w-full ${className}`} />;
}
