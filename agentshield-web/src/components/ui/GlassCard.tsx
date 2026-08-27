"use client";

import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
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

  function onMove(e: MouseEvent<HTMLDivElement>) {
    if (!interactive) return;
    const r = e.currentTarget.getBoundingClientRect();
    mx.set(e.clientX - r.left);
    my.set(e.clientY - r.top);
  }

  return (
    <motion.div
      onMouseMove={onMove}
      whileHover={interactive ? { y: -6 } : undefined}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      className={cn(
        "group relative overflow-hidden rounded-2xl glass p-6 shadow-card",
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
