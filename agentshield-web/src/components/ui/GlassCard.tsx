"use client";

import { motion, useMotionTemplate, useMotionValue, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ReactNode, MouseEvent } from "react";

export function GlassCard({
  children,
  className,
  interactive = true,
  glow = "rgba(79,124,255,0.18)",
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  glow?: string;
}) {
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const background = useMotionTemplate`radial-gradient(220px circle at ${mx}px ${my}px, ${glow}, transparent 70%)`;

  // Subtle 3D tilt that follows the cursor.
  const rx = useSpring(useMotionValue(0), { stiffness: 220, damping: 20 });
  const ry = useSpring(useMotionValue(0), { stiffness: 220, damping: 20 });

  function onMove(e: MouseEvent<HTMLDivElement>) {
    if (!interactive) return;
    const r = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - r.left;
    const py = e.clientY - r.top;
    mx.set(px);
    my.set(py);
    ry.set(((px / r.width) - 0.5) * 9);
    rx.set(-((py / r.height) - 0.5) * 9);
  }

  function onLeave() {
    rx.set(0);
    ry.set(0);
  }

  return (
    <motion.div
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      whileHover={interactive ? { y: -6 } : undefined}
      whileTap={interactive ? { scale: 0.99 } : undefined}
      style={
        interactive
          ? { rotateX: rx, rotateY: ry, transformPerspective: 900 }
          : undefined
      }
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      className={cn(
        "group relative overflow-hidden rounded-2xl glass p-6 shadow-card [transform-style:preserve-3d]",
        className
      )}
    >
      {interactive && (
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{ background }}
        />
      )}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
