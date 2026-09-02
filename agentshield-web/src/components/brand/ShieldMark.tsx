"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

/**
 * AgentShield brand mark, hand-built as inline SVG so it is crisp at any size
 * and — in `mode="draw"` — can stroke-animate ("forge") itself. Geometry echoes
 * the logo: a shield, a two-bar "A" (cyan leg + violet leg), a keyhole lock and
 * an orbital ring. In `mode="static"` it renders filled for navbar/footer use.
 *
 * Animation is driven by framer-motion variants that PROPAGATE from a parent
 * `motion` element (see LogoIntro), so the parent's `initial`/`animate` state
 * controls the whole forge sequence.
 */

const draw = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: (i: number) => ({
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: { delay: i * 0.16, duration: 0.7, ease: [0.22, 1, 0.36, 1] },
      opacity: { delay: i * 0.16, duration: 0.15 },
    },
  }),
};

const fillIn = {
  hidden: { opacity: 0 },
  visible: (i: number) => ({
    opacity: 1,
    transition: { delay: 0.75 + i * 0.12, duration: 0.5, ease: "easeOut" },
  }),
};

const SHIELD = "M50 5 L91 19 L91 58 C91 87 73 104 50 113 C27 104 9 87 9 58 L9 19 Z";
const LEG_L = "M33 86 L50 30";
const LEG_R = "M50 30 L67 86";
const RING = "M14 66 C14 52 30 44 50 44 C70 44 86 52 86 66 C86 80 70 88 50 88 C30 88 14 80 14 66 Z";

export function ShieldMark({
  className,
  mode = "static",
  strokeWidth = 2.4,
}: {
  className?: string;
  mode?: "static" | "draw";
  strokeWidth?: number;
}) {
  const isDraw = mode === "draw";
  const pathProps = isDraw
    ? { variants: draw, initial: "hidden" as const }
    : {};

  return (
    <svg
      viewBox="0 0 100 118"
      className={cn("h-full w-full", className)}
      fill="none"
      aria-hidden
    >
      <defs>
        <linearGradient id="asm-cyan" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#5eead4" />
          <stop offset="55%" stopColor="#38e1ff" />
          <stop offset="100%" stopColor="#4f7cff" />
        </linearGradient>
        <linearGradient id="asm-violet" x1="1" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#e94bd0" />
          <stop offset="55%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#4f7cff" />
        </linearGradient>
        <linearGradient id="asm-ring" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#38e1ff" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        <linearGradient id="asm-shield" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#4f7cff" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        <radialGradient id="asm-fill" cx="50%" cy="42%" r="70%">
          <stop offset="0%" stopColor="#0d1426" />
          <stop offset="100%" stopColor="#070b16" />
        </radialGradient>
      </defs>

      {/* Orbital ring behind the shield */}
      <motion.path
        d={RING}
        stroke="url(#asm-ring)"
        strokeWidth={strokeWidth * 0.9}
        strokeLinecap="round"
        opacity={0.85}
        transform="rotate(-18 50 66)"
        custom={4}
        {...pathProps}
      />

      {/* Shield fill (only meaningful once drawn) */}
      {isDraw ? (
        <motion.path d={SHIELD} fill="url(#asm-fill)" custom={0} variants={fillIn} initial="hidden" />
      ) : (
        <path d={SHIELD} fill="url(#asm-fill)" />
      )}

      {/* Shield outline */}
      <motion.path
        d={SHIELD}
        stroke="url(#asm-shield)"
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
        custom={0}
        {...pathProps}
      />

      {/* "A" legs */}
      <motion.path
        d={LEG_L}
        stroke="url(#asm-cyan)"
        strokeWidth={strokeWidth * 3}
        strokeLinecap="round"
        custom={1}
        {...pathProps}
      />
      <motion.path
        d={LEG_R}
        stroke="url(#asm-violet)"
        strokeWidth={strokeWidth * 3}
        strokeLinecap="round"
        custom={2}
        {...pathProps}
      />

      {/* Apex spark */}
      {isDraw ? (
        <motion.path d="M45 46 L50 36 L55 46 Z" fill="url(#asm-cyan)" custom={1} variants={fillIn} initial="hidden" />
      ) : (
        <path d="M45 46 L50 36 L55 46 Z" fill="url(#asm-cyan)" />
      )}

      {/* Keyhole lock */}
      {isDraw ? (
        <motion.g custom={3} variants={fillIn} initial="hidden">
          <circle cx="50" cy="70" r="6" fill="url(#asm-ring)" />
          <path d="M47 72 L53 72 L55 84 L45 84 Z" fill="url(#asm-ring)" />
        </motion.g>
      ) : (
        <g>
          <circle cx="50" cy="70" r="6" fill="url(#asm-ring)" />
          <path d="M47 72 L53 72 L55 84 L45 84 Z" fill="url(#asm-ring)" />
        </g>
      )}
    </svg>
  );
}
