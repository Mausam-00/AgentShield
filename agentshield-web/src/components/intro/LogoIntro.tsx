"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ShieldMark } from "@/components/brand/ShieldMark";

const SESSION_KEY = "as_intro_played_v1";
const GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"];

export function LogoIntro() {
  const [show, setShow] = useState(false);
  const [armed, setArmed] = useState(-1); // index of last-armed gate
  const [ready, setReady] = useState(false);
  const reduce = useReducedMotion();
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_KEY)) return; // once per session
    setShow(true);
    document.documentElement.style.overflow = "hidden";

    const scheduled = timers.current;
    const push = (fn: () => void, ms: number) =>
      scheduled.push(setTimeout(fn, ms));

    if (reduce) {
      // Minimal, motion-safe: brief hold then reveal.
      push(() => finish(), 650);
    } else {
      // Arm gates G0..G7 sequentially while the shield forges.
      GATES.forEach((_, i) => push(() => setArmed(i), 850 + i * 120));
      push(() => setReady(true), 850 + GATES.length * 120 + 120);
      push(() => finish(), 2500);
    }

    return () => {
      scheduled.forEach(clearTimeout);
      document.documentElement.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function finish() {
    sessionStorage.setItem(SESSION_KEY, "1");
    document.documentElement.style.overflow = "";
    setShow(false);
  }

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="logo-intro"
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-ink-950"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, filter: "blur(6px)" }}
          transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
        >
          {/* Ambient glow */}
          <div className="pointer-events-none absolute inset-0 bg-radial-hero opacity-60" />

          {/* Forge stage */}
          <motion.div
            className="relative"
            initial="hidden"
            animate="visible"
            exit={{ scale: 0.7, y: -40, opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
          >
            {/* Expanding ignite ring */}
            {!reduce && (
              <motion.span
                aria-hidden
                className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-neon-cyan/40"
                initial={{ scale: 0.4, opacity: 0 }}
                animate={{ scale: [0.4, 1.8], opacity: [0, 0.6, 0] }}
                transition={{ duration: 1.1, delay: 0.9, ease: "easeOut" }}
              />
            )}
            <div className="relative h-36 w-36 drop-shadow-[0_0_40px_rgba(79,124,255,0.45)] sm:h-44 sm:w-44">
              <ShieldMark mode={reduce ? "static" : "draw"} strokeWidth={2.2} />
            </div>
          </motion.div>

          {/* Wordmark */}
          <motion.div
            className="mt-8 text-center"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: reduce ? 0.15 : 1.15, duration: 0.5 }}
          >
            <div className="font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              AgentShield <span className="text-gradient-neon">AI</span>
            </div>

            {/* Gate-arming row */}
            <div className="mt-5 flex items-center justify-center gap-1.5">
              {GATES.map((g, i) => (
                <motion.span
                  key={g}
                  className="h-1.5 w-1.5 rounded-full"
                  animate={{
                    backgroundColor:
                      reduce || i <= armed ? "#38e1ff" : "rgba(255,255,255,0.14)",
                    boxShadow:
                      reduce || i <= armed
                        ? "0 0 10px rgba(56,225,255,0.8)"
                        : "0 0 0 rgba(0,0,0,0)",
                  }}
                  transition={{ duration: 0.25 }}
                />
              ))}
            </div>

            <motion.div
              className="mt-3 h-4 text-[11px] font-medium uppercase tracking-[0.25em] text-white/45"
              animate={{ opacity: 1 }}
            >
              {ready || reduce ? "Seven gates armed" : "Arming seven gates…"}
            </motion.div>
          </motion.div>

          {/* Exit wipe */}
          <motion.div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-neon-blue/10 to-transparent"
            initial={{ height: 0 }}
            exit={{ height: "100%" }}
            transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
