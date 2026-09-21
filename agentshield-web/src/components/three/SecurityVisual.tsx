"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";

const HeroScene = dynamic(() => import("./HeroScene"), {
  ssr: false,
  loading: () => null,
});
const SecurityScene = dynamic(() => import("./SecurityScene"), { ssr: false, loading: () => null });
const SectionSceneFallback = dynamic(() => import("./SectionSceneFallback"), { ssr: false, loading: () => null });

export type SceneVariant = "shield" | "capabilities" | "gates";

/**
 * The SVG remains the fallback; desktop WebGL is loaded only when eligible.
 */
export function SecurityVisual({ variant = "shield", activeIndex = -1 }: {
  variant?: SceneVariant; activeIndex?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [show, setShow] = useState(false);
  const [active, setActive] = useState(false);
  const [eligible, setEligible] = useState(false);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  const onFailure = useCallback(() => { setFailed(true); setReady(false); }, []);

  useEffect(() => {
    const media = window.matchMedia("(min-width: 1024px) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    const update = () => { setEligible(media.matches); setReady(false); };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let visible = false;
    const update = () => setActive(visible && !document.hidden);
    const io = new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting;
        if (visible) setShow(true);
        update();
      },
      { threshold: 0.05 }
    );
    io.observe(el);
    document.addEventListener("visibilitychange", update);
    return () => {
      io.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  return (
    <div ref={ref} className="neural-viewport relative aspect-square w-full" data-variant={variant} data-selected={activeIndex} data-active={active} data-renderer={eligible && ready && !failed ? "webgl" : "svg"}>
      {show && (variant === "shield" ? <HeroScene /> : <SectionSceneFallback variant={variant} activeIndex={activeIndex} />)}
      {show && eligible && !failed && <SecurityScene variant={variant} activeIndex={activeIndex} active={active} onReady={onReady} onFailure={onFailure} />}
    </div>
  );
}
