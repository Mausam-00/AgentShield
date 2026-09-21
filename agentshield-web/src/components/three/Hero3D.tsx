"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

const HeroScene = dynamic(() => import("./HeroScene"), {
  ssr: false,
  loading: () => null,
});

/**
 * Lazy-loads the depth-layered SVG scene and pauses it offscreen or in a hidden tab.
 */
export function Hero3D() {
  const ref = useRef<HTMLDivElement>(null);
  const [show, setShow] = useState(false);
  const [active, setActive] = useState(false);

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
    <div ref={ref} className="neural-viewport relative aspect-square w-full" data-active={active}>
      {show && <HeroScene />}
    </div>
  );
}
