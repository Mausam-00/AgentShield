"use client";

import type { CSSProperties } from "react";
import { ShieldMark } from "@/components/brand/ShieldMark";

// Fixed geometry keeps this conceptual illustration stable across server/client renders.
const NODES = [
  [92, 168], [172, 98], [296, 64], [428, 104], [514, 174],
  [548, 294], [494, 422], [406, 504], [278, 540], [144, 482],
  [62, 366], [52, 266],
] as const;
const SHIELD = "M300 174 L395 210 L395 308 Q395 379 300 420 Q205 379 205 308 L205 210 Z";

export default function HeroScene() {
  return (
    <div className="neural-scene" aria-hidden="true">
      <div className="neural-aura" />
      <svg viewBox="0 0 600 600" fill="none" className="neural-topology">
        <defs>
          <linearGradient id="neural-shield" x1="205" y1="174" x2="395" y2="420" gradientUnits="userSpaceOnUse">
            <stop stopColor="var(--neon-cyan)" stopOpacity=".65" />
            <stop offset="1" stopColor="var(--neon-blue)" stopOpacity=".15" />
          </linearGradient>
          <radialGradient id="neural-fill">
            <stop stopColor="var(--neon-blue)" stopOpacity=".16" />
            <stop offset="1" stopColor="var(--bg)" stopOpacity=".9" />
          </radialGradient>
        </defs>
        <g className="neural-orbit">
          <circle cx="300" cy="300" r="245" stroke="currentColor" strokeDasharray="2 12" opacity=".35" />
          <circle cx="300" cy="300" r="210" stroke="currentColor" opacity=".12" />
          <path d="M300 90 A210 210 0 0 1 510 300" stroke="currentColor" opacity=".55" strokeWidth="2" />
        </g>
        <ellipse cx="300" cy="324" rx="276" ry="114" stroke="currentColor" opacity=".13" transform="rotate(-32 300 300)" />
        {NODES.map(([x, y], i) => {
          const next = NODES[(i + 1) % NODES.length];
          const innerX = 300 + (x - 300) * .52;
          const innerY = 300 + (y - 300) * .52;
          const path = `M${x} ${y} L${innerX} ${y} L${innerX} ${innerY}`;
          return (
            <g key={i} style={{ "--signal-delay": `${-i * .61}s` } as CSSProperties}>
              <path d={`M${x} ${y} L${next[0]} ${next[1]}`} stroke="currentColor" opacity=".12" />
              <path d={path} stroke="currentColor" opacity=".25" />
              <path d={path} pathLength="100" className="neural-signal" />
              <circle cx={x} cy={y} r="17" fill="var(--bg)" stroke="currentColor" strokeOpacity=".35" />
              <circle cx={x} cy={y} r="6" fill="currentColor" fillOpacity=".12" stroke="currentColor" strokeOpacity=".75" />
              <circle cx={innerX} cy={innerY} r="3" fill="currentColor" opacity=".6" />
            </g>
          );
        })}
        <path d={SHIELD} transform="translate(0 14)" fill="var(--bg)" stroke="var(--neon-blue)" strokeOpacity=".25" />
        <path d={SHIELD} fill="url(#neural-fill)" stroke="url(#neural-shield)" strokeWidth="1.5" />
        <path d="M205 210 L205 224 M395 210 L395 224 M300 420 L300 434" stroke="var(--neon-cyan)" strokeOpacity=".5" />
        <path d={SHIELD} pathLength="100" className="neural-boundary" />
        <g stroke="currentColor" opacity=".35">
          <path d="M70 114 V82 H102 M498 82 H530 V114 M530 486 V518 H498 M102 518 H70 V486" />
          <path d="M290 28 H310 M300 18 V38 M290 572 H310 M300 562 V582" />
        </g>
      </svg>
      <div className="neural-mark"><ShieldMark mode="static" strokeWidth={1.8} /></div>
    </div>
  );
}
