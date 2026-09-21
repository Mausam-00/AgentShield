"use client";

import type { SceneVariant } from "./SecurityVisual";

export default function SectionSceneFallback({ variant, activeIndex }: {
  variant: Exclude<SceneVariant, "shield">; activeIndex: number;
}) {
  return (
    <svg className="section-scene-fallback h-full w-full" viewBox="0 0 400 400" fill="none" aria-hidden="true">
      {variant === "capabilities" ? (
        <g>
          <ellipse cx="200" cy="200" rx="155" ry="100" stroke="var(--neon-blue)" strokeOpacity=".35" />
          <path d="M200 125 L263 168 L247 242 L200 275 L137 232 L147 158 Z" fill="var(--surface)" stroke="var(--neon-cyan)" />
          <path d="M200 125 V275 M137 232 L263 168 M147 158 L247 242" stroke="var(--neon-cyan)" strokeOpacity=".3" />
          {Array.from({ length: 6 }, (_, i) => {
            const x = 200 + Math.cos(i * Math.PI / 3) * 155;
            const y = 200 + Math.sin(i * Math.PI / 3) * 100;
            return (
              <g key={i}>
                <path d={`M200 200 L${x} ${y}`} stroke="var(--neon-cyan)" strokeOpacity=".2" />
                <rect x={x - 10} y={y - 10} width="20" height="20" rx="4" fill="var(--surface)" stroke={i === activeIndex ? "var(--neon-violet)" : "var(--neon-cyan)"} strokeWidth={i === activeIndex ? 3 : 1} />
              </g>
            );
          })}
        </g>
      ) : (
        <g>
          {Array.from({ length: 8 }, (_, i) => (
            <rect key={i} x={42 + i * 25} y={70 + i * 9} width={140 - i * 9} height={240 - i * 18} rx="18"
              transform={`skewY(-8)`} fill="var(--surface)" fillOpacity=".15"
              stroke={i === activeIndex ? "var(--neon-cyan)" : "var(--neon-blue)"} strokeOpacity={i === activeIndex ? 1 : .4} strokeWidth={i === activeIndex ? 3 : 1} />
          ))}
          <path d="M48 176 L342 150" stroke="var(--neon-cyan)" strokeDasharray="3 7" strokeOpacity=".6" />
        </g>
      )}
    </svg>
  );
}
