"use client";

import { useEffect, useRef, useState } from "react";

const AGENTS = [[72, 104], [62, 276], [320, 72], [342, 272]] as const;

export function SecurityPerimeter() {
  const ref = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(false);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    let visible = false;
    const update = () => setActive(visible && !document.hidden);
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      update();
    });
    observer.observe(element);
    document.addEventListener("visibilitychange", update);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  return (
    <div ref={ref} className="security-perimeter relative mx-auto aspect-square w-full max-w-[400px]" data-active={active} aria-hidden="true">
      <div className="neural-aura" />
      <svg viewBox="0 0 400 400" fill="none" className="relative h-full w-full">
        <ellipse cx="200" cy="214" rx="172" ry="104" stroke="var(--neon-blue)" strokeOpacity=".35" transform="rotate(-24 200 214)" />
        <g className="perimeter-ring">
          <circle cx="200" cy="200" r="145" stroke="var(--neon-cyan)" strokeOpacity=".2" strokeDasharray="2 9" />
          <path d="M200 55 A145 145 0 0 1 345 200" stroke="var(--neon-cyan)" strokeOpacity=".55" />
        </g>
        {AGENTS.map(([x, y], i) => {
          const path = `M${x} ${y} H${x < 200 ? 118 : 282} V200 H200`;
          return (
            <g key={i}>
              <path d={path} stroke="var(--neon-blue)" strokeOpacity=".45" />
              <path d={path} pathLength="100" className="neural-signal" style={{ animationDelay: `${-i * 1.2}s` }} />
              <g transform={`translate(${x - 22} ${y - 22})`}>
                <rect width="44" height="44" rx="12" fill="var(--surface)" stroke="var(--edge-active)" />
                <rect x="13" y="13" width="18" height="18" rx="4" stroke="var(--neon-cyan)" />
                <path d="M17 9 V13 M27 9 V13 M17 31 V35 M27 31 V35 M9 17 H13 M9 27 H13 M31 17 H35 M31 27 H35" stroke="var(--neon-cyan)" strokeOpacity=".6" />
                <circle cx="22" cy="22" r="3" fill="var(--neon-cyan)" />
              </g>
            </g>
          );
        })}
        <path d="M200 120 L264 145 V214 Q264 260 200 290 Q136 260 136 214 V145 Z" transform="translate(0 10)" fill="var(--surface)" stroke="var(--neon-blue)" strokeOpacity=".5" />
        <path d="M200 120 L264 145 V214 Q264 260 200 290 Q136 260 136 214 V145 Z" fill="var(--surface-raised)" stroke="var(--neon-cyan)" strokeWidth="1.5" />
        <path d="M200 135 L252 155 V212 Q252 248 200 274 Q148 248 148 212 V155 Z" stroke="var(--edge-active)" />
        <rect x="179" y="194" width="42" height="35" rx="7" fill="var(--circuit)" stroke="var(--neon-cyan)" strokeWidth="2" />
        <path d="M186 194 V182 A14 14 0 0 1 214 182 V194" stroke="var(--neon-cyan)" strokeWidth="3" />
        <circle cx="200" cy="207" r="3" fill="var(--neon-cyan)" />
        <path d="M200 209 V217" stroke="var(--neon-cyan)" strokeWidth="2" />
        <g transform="translate(277 178)">
          <rect width="42" height="54" rx="8" fill="var(--surface)" stroke="var(--neon-violet)" />
          <path d="M11 15 H30 M11 24 H30 M11 33 H24 M11 42 H20" stroke="var(--neon-violet)" strokeOpacity=".8" />
        </g>
      </svg>
    </div>
  );
}
