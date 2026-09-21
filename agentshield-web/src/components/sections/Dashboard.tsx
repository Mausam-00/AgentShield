"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { Reveal } from "@/components/ui/Reveal";
import { dashboard } from "@/lib/site";
import { cn } from "@/lib/utils";

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

const REPLAY_MS = 6000;

function useBenchmarkReplay() {
  const ref = useRef<HTMLDivElement>(null);
  const visible = useInView(ref, { amount: .12 });
  const [reduce, setReduce] = useState(false);
  const elapsed = useRef(0);
  const [progress, setProgress] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(false);
  const complete = progress >= 1;

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduce(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const update = () => setHidden(document.hidden);
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);

  useEffect(() => {
    if (reduce) {
      elapsed.current = REPLAY_MS;
      setProgress(1);
    }
  }, [reduce]);

  useEffect(() => {
    if (!visible || hidden || reduce || paused || complete) return;
    let previous = performance.now();
    let raf = 0;
    const frame = (now: number) => {
      elapsed.current = Math.min(REPLAY_MS, elapsed.current + Math.min(now - previous, 100));
      previous = now;
      setProgress(elapsed.current / REPLAY_MS);
      if (elapsed.current < REPLAY_MS) raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [visible, hidden, reduce, paused, complete]);

  return {
    ref,
    progress: reduce ? 1 : progress,
    running: visible && !hidden && !reduce && !paused && !complete,
    paused,
    reduced: !!reduce,
    toggle: () => {
      if (complete) {
        elapsed.current = 0;
        setProgress(0);
        setPaused(false);
      } else setPaused(value => !value);
    },
  };
}

function MetricBar({
  label,
  before,
  after,
  unit,
  change,
  detail,
  progress,
}: {
  label: string;
  before: number;
  after: number;
  unit: string;
  change: string;
  detail: string;
  progress: number;
}) {
  const [open, setOpen] = useState(false);
  const afterPct = Math.max(6, Math.round((after / before) * 100));
  const baseline = Math.min(1, progress / .25);
  const optimized = Math.max(0, Math.min(1, (progress - .25) / .6));
  const value = Math.round(before + (after - before) * optimized);

  return (
    <div className="instrument-panel benchmark-metric relative overflow-hidden rounded-2xl p-6">
      {progress > 0 && progress < 1 && <span aria-hidden className="benchmark-scan" style={{ left: `${progress * 100}%` }} />}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-medium text-white/70">{label}</div>
          <div className="mt-1 font-display text-2xl font-semibold text-white">
            <span className="sr-only">{fmt(after)}</span>
            <span aria-hidden data-testid="replay-value" className="tabular-nums">{fmt(value)}</span>
            <span className="text-base text-white/40">{unit}</span>
          </div>
        </div>
        <span className="rounded-full border border-neon-teal/30 bg-neon-teal/10 px-3 py-1 text-sm font-semibold text-neon-teal">
          {change}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        <div>
          <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wider text-white/40">
            <span>Before</span>
            <span>
              {fmt(before)}
              {unit}
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-white/8">
            <div
              className="h-full rounded-full bg-gradient-to-r from-rose-500 to-orange-400"
              data-testid="baseline-bar"
              style={{ width: `${baseline * 100}%` }}
            />
          </div>
        </div>
        <div>
          <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wider text-white/40">
            <span>After</span>
            <span>
              {fmt(after)}
              {unit}
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-white/8">
            <div
              className="h-full rounded-full bg-gradient-to-r from-neon-teal to-neon-cyan"
              data-testid="optimized-bar"
              style={{ width: `${baseline * (100 + (afterPct - 100) * optimized)}%` }}
            />
          </div>
        </div>
      </div>

      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-neon-cyan/80 hover:text-neon-cyan"
      >
        <Icon name={open ? "Minus" : "Plus"} className="h-3.5 w-3.5" />
        {open ? "Show less" : "Click for more info"}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.p
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden text-sm leading-relaxed text-white/70"
          >
            <span className="mt-3 block border-t border-white/10 pt-3">{detail}</span>
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Dashboard() {
  const [openSaving, setOpenSaving] = useState<number | null>(0);
  const replay = useBenchmarkReplay();
  const phase = replay.progress < .25 ? 0 : replay.progress < .85 ? 1 : 2;

  return (
    <section id="dashboard" className="container-x scroll-mt-28 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Efficiency dashboard"
        title={
          <>
            Measured results,{" "}
            <span className="text-gradient-neon">before vs after</span>
          </>
        }
        subtitle="A non-invasive optimization layer measured across a 12-task governance workload. The engine is byte-identical — every decision was re-verified against the recorded baseline."
      />

      <div ref={replay.ref} className="benchmark-replay mt-12 grid gap-5 lg:grid-cols-[1.15fr_1fr]" data-running={replay.running} data-complete={replay.progress === 1}>
        <div className="instrument-panel rounded-2xl p-5 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-xs leading-relaxed text-white/60">
              Recorded benchmark replay — illustrative animation, not a live engine run.
            </p>
            <button onClick={replay.toggle} disabled={replay.reduced}
              className="rounded-lg border border-neon-cyan/30 px-4 py-2 text-xs font-medium text-neon-cyan hover:bg-neon-cyan/10 disabled:cursor-default disabled:opacity-50">
              {replay.reduced ? "Recorded results" : replay.progress === 1 ? "Replay benchmark" : replay.paused ? "Resume replay" : "Pause replay"}
            </button>
          </div>
          <ol className="mt-5 grid grid-cols-3 gap-3 text-[11px] sm:text-xs" aria-label="Benchmark replay stages">
            {["Recorded baseline", "Optimization replay", "Preserved results"].map((label, i) => (
              <li key={label} aria-current={phase === i ? "step" : undefined}
                className={cn("border-t-2 pt-3 transition-colors", i <= phase ? "border-neon-cyan text-neon-cyan" : "border-white/10 text-white/40")}>
                <span className="mr-2 font-mono opacity-60">0{i + 1}</span>{label}
              </li>
            ))}
          </ol>
          <div aria-hidden className="mt-4 h-0.5 overflow-hidden rounded bg-white/8">
            <div className="h-full bg-neon-cyan" style={{ width: `${replay.progress * 100}%` }} />
          </div>
        </div>
        {/* Left: metric bars + preserved */}
        <div className="grid gap-5">
          <div className="grid gap-5 sm:grid-cols-2">
            {dashboard.metrics.map((m) => (
              <MetricBar key={m.label} {...m} progress={replay.progress} />
            ))}
          </div>

          <Reveal>
            <div className="benchmark-preserved rounded-2xl glass-strong p-6" data-highlighted={phase === 2}>
              <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
                <Icon name="ShieldCheck" className="h-4 w-4 text-neon-teal" />
                Preserved — unchanged after optimization
              </div>
              <div className="grid grid-cols-2 gap-4">
                {dashboard.preserved.map((p) => (
                  <div
                    key={p.label}
                    className="rounded-xl border border-white/8 bg-white/[0.02] p-4"
                  >
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-neon-teal shadow-[0_0_10px_2px_rgba(94,234,212,0.7)]" />
                      <span className="font-display text-lg font-semibold text-white">
                        {p.value}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-white/55">{p.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
        </div>

        {/* Right: savings sources, expandable */}
        <Reveal delay={0.1}>
          <div className="flex h-full flex-col rounded-2xl glass p-6">
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <Icon name="Layers" className="h-4 w-4 text-neon-cyan" />
              Where the savings come from
            </div>
            <div className="flex flex-col gap-2.5">
              {dashboard.savings.map((s, i) => {
                const isOpen = openSaving === i;
                return (
                  <button
                    key={s.title}
                    onClick={() => setOpenSaving(isOpen ? null : i)}
                    aria-expanded={isOpen}
                    className={cn(
                      "rounded-xl border p-4 text-left transition-colors",
                      isOpen
                        ? "border-neon-blue/40 bg-white/[0.04]"
                        : "border-white/8 bg-white/[0.02] hover:border-white/20"
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-white">
                        {s.title}
                      </span>
                      <span className="shrink-0 rounded-full border border-neon-cyan/25 bg-neon-cyan/10 px-2.5 py-0.5 text-[11px] font-medium text-neon-cyan">
                        {s.tag}
                      </span>
                    </div>
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.p
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden text-sm leading-relaxed text-white/65"
                        >
                          <span className="mt-2 block">{s.detail}</span>
                        </motion.p>
                      )}
                    </AnimatePresence>
                  </button>
                );
              })}
            </div>
            <p className="mt-4 border-t border-white/10 pt-3 text-[11px] leading-relaxed text-white/40">
              {dashboard.disclaimer}
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
