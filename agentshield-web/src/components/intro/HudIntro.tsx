"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ShieldMark } from "@/components/brand/ShieldMark";

const SESSION_KEY = "as_intro_played_v1";
const GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"];
const ASSEMBLE_MS = 1200;
const MARK_H = 200;

const TELEMETRY: { label: string; status: string }[] = [
  { label: "Booting deterministic policy engine", status: "OK" },
  { label: "Verifying gate signatures G0–G7", status: "OK" },
  { label: "Mounting red-team corpus · 9 families", status: "OK" },
  { label: "Calibrating Responsible-AI pillars", status: "OK" },
  { label: "Sealing action interceptor", status: "ARMED" },
];

// Build radial tick marks around a circle (centre 200,200).
function ticks(r: number, len: number, count: number) {
  return Array.from({ length: count }, (_, i) => {
    const a = (i * 360) / count;
    const rad = (a * Math.PI) / 180;
    const c = Math.cos(rad);
    const s = Math.sin(rad);
    return {
      x1: 200 + c * r,
      y1: 200 + s * r,
      x2: 200 + c * (r + len),
      y2: 200 + s * (r + len),
    };
  });
}
const TICKS = ticks(150, 8, 48);
const TICKS2 = ticks(118, 5, 24);

const LABELS = [
  { a: -62, t: "POLICY v1.0" },
  { a: 28, t: "GATES 8/8" },
  { a: 118, t: "RAI · 6" },
  { a: 208, t: "REDTEAM · 9" },
];
function labelPos(a: number, r: number) {
  const rad = (a * Math.PI) / 180;
  return { x: 200 + Math.cos(rad) * r, y: 200 + Math.sin(rad) * r };
}

export function HudIntro() {
  const [show, setShow] = useState(false);
  const [assembled, setAssembled] = useState(false);
  const [online, setOnline] = useState(false);
  const [revealed, setRevealed] = useState(0);
  const [resolved, setResolved] = useState(0);
  const [armed, setArmed] = useState(-1);
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

  const handleAssembled = useCallback(() => {
    if (armedOnce.current) return;
    armedOnce.current = true;
    setAssembled(true);
    schedule(() => setOnline(true), 260);
    GATES.forEach((_, i) => schedule(() => setArmed(i), 320 + i * 70));
    schedule(finish, 1500);
  }, [finish, schedule]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_KEY)) return;
    setShow(true);
    document.documentElement.style.overflow = "hidden";
    const scheduled = timers.current;

    if (reduce) {
      setRevealed(TELEMETRY.length);
      setResolved(TELEMETRY.length);
      setAssembled(true);
      setOnline(true);
      setArmed(GATES.length - 1);
      scheduled.push(setTimeout(finish, 900));
    } else {
      // Stream boot telemetry, then reveal the logo at the reticle centre.
      TELEMETRY.forEach((_, i) => {
        schedule(() => setRevealed(i + 1), 200 + i * 170);
        schedule(() => setResolved(i + 1), 200 + i * 170 + 120);
      });
      schedule(handleAssembled, ASSEMBLE_MS);
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape" || e.key === "Enter" || e.key === " ") finish();
      };
      window.addEventListener("keydown", onKey);
      scheduled.push(
        setTimeout(() => window.removeEventListener("keydown", onKey), 7000) as unknown as ReturnType<
          typeof setTimeout
        >
      );
    }

    return () => {
      scheduled.forEach(clearTimeout);
      document.documentElement.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const spin = (dur: number, dir = 1) =>
    reduce
      ? {}
      : {
          animate: { rotate: 360 * dir },
          transition: { duration: dur, ease: "linear" as const, repeat: Infinity },
        };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="hud-intro"
          onClick={finish}
          className="fixed inset-0 z-[100] flex cursor-pointer items-center justify-center overflow-hidden bg-ink-950"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, filter: "blur(8px)" }}
          transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
        >
          {/* Ambient */}
          <div className="pointer-events-none absolute inset-0 bg-radial-hero opacity-60" />
          <div className="pointer-events-none absolute inset-0 bg-grid-fade opacity-[0.12]" />

          {/* Boot telemetry (JARVIS log) */}
          <div className="pointer-events-none absolute left-6 top-6 hidden w-72 font-mono text-[11px] leading-relaxed text-neon-cyan/80 sm:block">
            <div className="mb-2 tracking-[0.3em] text-white/50">AGENTSHIELD SECURE BOOT</div>
            {TELEMETRY.map((line, i) => (
              <motion.div
                key={line.label}
                className="flex items-center justify-between gap-3"
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: i < revealed ? 1 : 0, x: i < revealed ? 0 : -6 }}
                transition={{ duration: 0.2 }}
              >
                <span className="truncate text-white/65">{line.label}</span>
                <span
                  className={
                    i < resolved
                      ? line.status === "ARMED"
                        ? "text-neon-magenta"
                        : "text-neon-teal"
                      : "text-white/30"
                  }
                >
                  {i < resolved ? `[ ${line.status} ]` : "[ ·· ]"}
                </span>
              </motion.div>
            ))}
          </div>

          {/* HUD core */}
          <motion.div
            className="relative"
            style={{ width: "min(84vmin, 520px)", height: "min(84vmin, 520px)" }}
            exit={{ scale: 0.7, opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.7, 0, 0.84, 0] }}
          >
            {/* Reticle rings */}
            <svg viewBox="0 0 400 400" className="absolute inset-0 h-full w-full text-neon-cyan">
              <defs>
                <radialGradient id="hud-core" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#38e1ff" stopOpacity="0.12" />
                  <stop offset="70%" stopColor="#38e1ff" stopOpacity="0" />
                </radialGradient>
              </defs>
              <circle cx="200" cy="200" r="196" fill="url(#hud-core)" />

              {/* Outer dashed ring (slow CCW) */}
              <motion.circle
                cx="200" cy="200" r="190" fill="none"
                stroke="currentColor" strokeOpacity="0.28" strokeWidth="1"
                strokeDasharray="2 8"
                style={{ transformOrigin: "200px 200px" }}
                {...spin(60, -1)}
              />
              {/* Segmented ring (medium CW) */}
              <motion.circle
                cx="200" cy="200" r="168" fill="none"
                stroke="currentColor" strokeOpacity="0.5" strokeWidth="2"
                strokeDasharray="150 90"
                style={{ transformOrigin: "200px 200px" }}
                {...spin(24)}
              />
              {/* Tick ring (slow CW) */}
              <motion.g
                style={{ transformOrigin: "200px 200px" }}
                stroke="currentColor" strokeOpacity="0.4" strokeWidth="1"
                {...spin(40)}
              >
                {TICKS.map((t, i) => (
                  <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} />
                ))}
              </motion.g>
              {/* Inner tick ring (medium CCW) */}
              <motion.g
                style={{ transformOrigin: "200px 200px" }}
                stroke="currentColor" strokeOpacity="0.3" strokeWidth="1"
                {...spin(18, -1)}
              >
                {TICKS2.map((t, i) => (
                  <line key={i} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} />
                ))}
              </motion.g>
              {/* Thin inner ring */}
              <circle cx="200" cy="200" r="100" fill="none" stroke="currentColor" strokeOpacity="0.35" strokeWidth="1" />

              {/* Orbiting labels */}
              {LABELS.map((l) => {
                const p = labelPos(l.a, 178);
                return (
                  <motion.text
                    key={l.t}
                    x={p.x} y={p.y}
                    textAnchor="middle" dominantBaseline="middle"
                    className="fill-white/45 font-mono"
                    style={{ fontSize: 8, letterSpacing: 1 }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0, 0.7, 0.4, 0.7] }}
                    transition={{ duration: 2.2, repeat: Infinity, delay: Math.random() }}
                  >
                    {l.t}
                  </motion.text>
                );
              })}
            </svg>

            {/* Radar sweep */}
            {!reduce && (
              <motion.div
                aria-hidden
                className="absolute left-1/2 top-1/2 rounded-full"
                style={{
                  width: "70%",
                  height: "70%",
                  translateX: "-50%",
                  translateY: "-50%",
                  background:
                    "conic-gradient(from 0deg, rgba(56,225,255,0) 0deg, rgba(56,225,255,0.32) 42deg, rgba(56,225,255,0) 60deg)",
                }}
                animate={{ rotate: 360, opacity: assembled ? 0 : 1 }}
                transition={{
                  rotate: { duration: 1.6, ease: "linear", repeat: Infinity },
                  opacity: { duration: 0.4 },
                }}
              />
            )}

            {/* Ignite ring on lock */}
            {!reduce && assembled && (
              <motion.span
                aria-hidden
                className="absolute left-1/2 top-1/2 rounded-full border border-neon-cyan/50"
                style={{ width: "34%", height: "34%", translateX: "-50%", translateY: "-50%" }}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: [0.5, 2.2], opacity: [0, 0.7, 0] }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            )}

            {/* Crisp shield mark at the core (static wrapper centres it; inner
                motion only fades/scales so it can't clobber the translate) */}
            <div
              className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 drop-shadow-[0_0_40px_rgba(79,124,255,0.45)]"
              style={{ height: MARK_H, width: MARK_H * (100 / 118) }}
            >
              <motion.div
                className="h-full w-full"
                initial={{ opacity: reduce ? 1 : 0 }}
                animate={{ opacity: assembled ? 1 : 0, scale: assembled ? [0.94, 1] : 0.94 }}
                transition={{ duration: 0.45, delay: assembled && !reduce ? 0.2 : 0 }}
              >
                <ShieldMark mode="static" strokeWidth={2.2} />
              </motion.div>
            </div>

            {/* Corner targeting brackets */}
            {[
              "left-[6%] top-[6%] border-l-2 border-t-2",
              "right-[6%] top-[6%] border-r-2 border-t-2",
              "left-[6%] bottom-[6%] border-l-2 border-b-2",
              "right-[6%] bottom-[6%] border-r-2 border-b-2",
            ].map((pos, i) => (
              <motion.span
                key={i}
                className={`absolute h-8 w-8 border-neon-cyan/60 ${pos}`}
                initial={{ opacity: 0, scale: 1.3 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: reduce ? 0 : 0.2 + i * 0.08, duration: 0.4 }}
              />
            ))}

            {/* Wordmark + status, anchored below the core */}
            <div className="absolute left-1/2 top-1/2 w-max -translate-x-1/2 translate-y-[130px] text-center">
              <motion.div
                className="font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: assembled ? 1 : 0, y: assembled ? 0 : 10 }}
                transition={{ duration: 0.5 }}
              >
                AgentShield <span className="text-gradient-neon">AI</span>
              </motion.div>

              {/* Gate-arming row */}
              <div className="mt-4 flex items-center justify-center gap-1.5">
                {GATES.map((g, i) => (
                  <motion.span
                    key={g}
                    className="h-1.5 w-1.5 rounded-full"
                    animate={{
                      backgroundColor: reduce || i <= armed ? "#38e1ff" : "rgba(255,255,255,0.14)",
                      boxShadow:
                        reduce || i <= armed ? "0 0 10px rgba(56,225,255,0.85)" : "0 0 0 rgba(0,0,0,0)",
                    }}
                    transition={{ duration: 0.2 }}
                  />
                ))}
              </div>

              {/* SYSTEMS ONLINE stamp */}
              <motion.div
                className="mt-3 font-mono text-[11px] uppercase tracking-[0.35em] text-neon-teal"
                initial={{ opacity: 0 }}
                animate={{ opacity: online || reduce ? [0, 1, 0.6, 1] : 0 }}
                transition={{ duration: 0.6 }}
              >
                Systems online · seven gates armed
              </motion.div>
            </div>
          </motion.div>

          {/* Glitch flash on lock */}
          {!reduce && assembled && (
            <motion.div
              aria-hidden
              className="pointer-events-none absolute inset-0 bg-white"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0.35, 0] }}
              transition={{ duration: 0.22, times: [0, 0.4, 1] }}
            />
          )}

          {/* Scanline overlay */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-[0.06]"
            style={{
              backgroundImage:
                "repeating-linear-gradient(0deg, rgba(255,255,255,0.5) 0px, rgba(255,255,255,0.5) 1px, transparent 1px, transparent 3px)",
            }}
          />

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
        </motion.div>
      )}
    </AnimatePresence>
  );
}
