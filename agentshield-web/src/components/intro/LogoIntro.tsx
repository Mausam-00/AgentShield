"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ShieldMark } from "@/components/brand/ShieldMark";
import { ParticleShield } from "@/components/intro/ParticleShield";

const SESSION_KEY = "as_intro_played_v1";
const GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"];
const ASSEMBLE_MS = 1500;
const MARK_H = 240; // px height of the mark/canvas stage

export function LogoIntro() {
  const [show, setShow] = useState(false);
  const [assembled, setAssembled] = useState(false);
  const [armed, setArmed] = useState(-1); // index of last-armed gate
  const [ready, setReady] = useState(false);
  const reduce = useReducedMotion();
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const armedOnce = useRef(false);

  const finish = useCallback(() => {
    sessionStorage.setItem(SESSION_KEY, "1");
    document.documentElement.style.overflow = "";
    setShow(false);
  }, []);

  const schedule = useCallback((fn: () => void, ms: number) => {
    timers.current.push(setTimeout(fn, ms));
  }, []);

  // Runs when the particle cloud has converged into the logo.
  const handleAssembled = useCallback(() => {
    if (armedOnce.current) return;
    armedOnce.current = true;
    setAssembled(true);
    GATES.forEach((_, i) => schedule(() => setArmed(i), i * 110));
    schedule(() => setReady(true), GATES.length * 110 + 120);
    schedule(finish, 1500);
  }, [finish, schedule]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_KEY)) return; // once per session
    setShow(true);
    document.documentElement.style.overflow = "hidden";

    const scheduled = timers.current;
    if (reduce) {
      // Motion-safe path: no particles; brief hold then reveal.
      setAssembled(true);
      scheduled.push(setTimeout(finish, 700));
    } else {
      // Allow skipping the intro.
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape" || e.key === "Enter" || e.key === " ") finish();
      };
      window.addEventListener("keydown", onKey);
      timers.current.push(
        setTimeout(() => window.removeEventListener("keydown", onKey), 6000) as unknown as ReturnType<typeof setTimeout>
      );
    }

    return () => {
      scheduled.forEach(clearTimeout);
      document.documentElement.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="logo-intro"
          onClick={finish}
          className="fixed inset-0 z-[100] flex cursor-pointer flex-col items-center justify-center bg-ink-950"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, filter: "blur(6px)" }}
          transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
        >
          {/* Ambient glow */}
          <div className="pointer-events-none absolute inset-0 bg-radial-hero opacity-60" />

          {/* Forge stage */}
          <motion.div
            className="relative"
            exit={{ scale: 0.7, y: -40, opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
          >
            {/* Expanding ignite ring, fired on convergence */}
            {!reduce && assembled && (
              <motion.span
                aria-hidden
                className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-neon-cyan/40"
                initial={{ scale: 0.4, opacity: 0 }}
                animate={{ scale: [0.4, 1.9], opacity: [0, 0.7, 0] }}
                transition={{ duration: 1.1, ease: "easeOut" }}
              />
            )}

            <div
              className="relative drop-shadow-[0_0_40px_rgba(79,124,255,0.45)]"
              style={{ height: MARK_H, width: MARK_H * (100 / 118) }}
            >
              {/* Particle cloud (assembles the silhouette) */}
              {!reduce && (
                <motion.div
                  className="absolute inset-0 grid place-items-center"
                  animate={{ opacity: assembled ? 0 : 1 }}
                  transition={{ duration: 0.5, delay: assembled ? 0.15 : 0 }}
                >
                  <ParticleShield size={MARK_H} assembleMs={ASSEMBLE_MS} onAssembled={handleAssembled} />
                </motion.div>
              )}
              {/* Crisp vector mark crossfades in once converged */}
              <motion.div
                className="absolute inset-0"
                initial={{ opacity: reduce ? 1 : 0 }}
                animate={{ opacity: assembled ? 1 : 0, scale: assembled ? [0.96, 1] : 0.96 }}
                transition={{ duration: 0.5 }}
              >
                <ShieldMark mode="static" strokeWidth={2.2} />
              </motion.div>
            </div>
          </motion.div>

          {/* Wordmark */}
          <motion.div
            className="mt-8 text-center"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: assembled ? 1 : 0, y: assembled ? 0 : 12 }}
            transition={{ duration: 0.5 }}
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

          {/* Skip hint */}
          {!reduce && (
            <motion.div
              className="absolute bottom-8 text-[10px] font-medium uppercase tracking-[0.3em] text-white/30"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.4, duration: 0.6 }}
            >
              Click or press any key to skip
            </motion.div>
          )}

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
