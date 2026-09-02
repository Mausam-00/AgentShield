"use client";

import Link from "next/link";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";
import { Icon } from "./Icon";
import { useState, type ReactNode, type MouseEvent } from "react";

type Props = {
  children: ReactNode;
  href?: string;
  variant?: "primary" | "ghost";
  className?: string;
  icon?: boolean;
  onClick?: () => void;
  target?: string;
  rel?: string;
};

export function GradientButton({
  children,
  href,
  variant = "primary",
  className,
  icon = true,
  onClick,
  target,
  rel,
}: Props) {
  const [ripples, setRipples] = useState<{ id: number; x: number; y: number }[]>([]);

  // Magnetic pull: the button eases a few px toward the cursor.
  const mvx = useMotionValue(0);
  const mvy = useMotionValue(0);
  const x = useSpring(mvx, { stiffness: 260, damping: 18, mass: 0.4 });
  const y = useSpring(mvy, { stiffness: 260, damping: 18, mass: 0.4 });

  function onMove(e: MouseEvent<HTMLSpanElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    mvx.set((e.clientX - (r.left + r.width / 2)) * 0.28);
    mvy.set((e.clientY - (r.top + r.height / 2)) * 0.35);
  }
  function onLeave() {
    mvx.set(0);
    mvy.set(0);
  }
  function spawnRipple(e: MouseEvent<HTMLSpanElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    const id = Date.now() + Math.random();
    setRipples((rs) => [...rs, { id, x: e.clientX - r.left, y: e.clientY - r.top }]);
    setTimeout(() => setRipples((rs) => rs.filter((rp) => rp.id !== id)), 650);
  }

  const base =
    "group relative inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-semibold tracking-tight transition-colors duration-300";

  const styles =
    variant === "primary"
      ? "text-white shadow-glow hover:shadow-glow-violet"
      : "text-white/85 border border-white/15 bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/25";

  const inner = (
    <motion.span
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onPointerDown={spawnRipple}
      whileTap={{ scale: 0.96 }}
      style={{ x, y }}
      className={cn(base, styles, className)}
    >
      {variant === "primary" && (
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] opacity-100"
        />
      )}
      {variant === "primary" && (
        <span
          aria-hidden
          className="absolute inset-0 overflow-hidden rounded-full"
        >
          <span className="btn-shimmer absolute inset-0 -translate-x-full animate-shimmer" />
        </span>
      )}
      <span className="relative z-10 flex items-center gap-2">
        {children}
        {icon && (
          <Icon
            name="ArrowRight"
            className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1"
          />
        )}
      </span>

      {/* Click ripples */}
      <span aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-full">
        {ripples.map((r) => (
          <motion.span
            key={r.id}
            className="absolute rounded-full bg-white/35"
            style={{ left: r.x, top: r.y, translateX: "-50%", translateY: "-50%" }}
            initial={{ width: 0, height: 0, opacity: 0.5 }}
            animate={{ width: 320, height: 320, opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        ))}
      </span>
    </motion.span>
  );

  if (href) {
    return (
      <Link href={href} onClick={onClick} target={target} rel={rel} className="inline-flex">
        {inner}
      </Link>
    );
  }
  return (
    <button onClick={onClick} className="inline-flex">
      {inner}
    </button>
  );
}
