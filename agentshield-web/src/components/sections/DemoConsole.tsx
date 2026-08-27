"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { demoScenarios } from "@/lib/site";
import { cn } from "@/lib/utils";

type Scenario = (typeof demoScenarios)[number];

const decisionStyle: Record<string, { text: string; ring: string; bg: string; dot: string }> = {
  ALLOW: { text: "text-emerald-300", ring: "ring-emerald-400/40", bg: "bg-emerald-400/10", dot: "bg-emerald-400" },
  TRANSFORM: { text: "text-sky-300", ring: "ring-sky-400/40", bg: "bg-sky-400/10", dot: "bg-sky-400" },
  APPROVE: { text: "text-cyan-300", ring: "ring-cyan-400/40", bg: "bg-cyan-400/10", dot: "bg-cyan-400" },
  ESCALATE: { text: "text-amber-300", ring: "ring-amber-400/40", bg: "bg-amber-400/10", dot: "bg-amber-400" },
  DENY: { text: "text-rose-300", ring: "ring-rose-400/40", bg: "bg-rose-400/10", dot: "bg-rose-400" },
};

const postureStyle: Record<string, string> = {
  PASS: "text-emerald-300 border-emerald-400/30 bg-emerald-400/10",
  WARN: "text-amber-300 border-amber-400/30 bg-amber-400/10",
  BLOCK: "text-rose-300 border-rose-400/30 bg-rose-400/10",
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-white/8 py-2 last:border-0">
      <span className="text-xs uppercase tracking-wider text-white/40">{label}</span>
      <span className="text-right font-mono text-sm text-white/80">{value}</span>
    </div>
  );
}

export function DemoConsole() {
  const [active, setActive] = useState<Scenario>(demoScenarios[0]);
  const [ran, setRan] = useState(false);
  const d = decisionStyle[active.decision] ?? decisionStyle.DENY;

  function pick(s: Scenario) {
    setActive(s);
    setRan(false);
  }

  return (
    <section id="demo" className="container-x scroll-mt-28 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Live demo · simulation"
        title={
          <>
            Watch a decision get{" "}
            <span className="text-gradient-neon">governed in real time</span>
          </>
        }
        subtitle="Pick a synthetic agent action and run it through the control plane. Judgement is advisory; only deterministic policy decides the verdict."
      />

      <div className="mt-16 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        {/* Scenario picker */}
        <div className="rounded-2xl glass p-6">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
            <Icon name="Layers" className="h-4 w-4 text-neon-cyan" />
            Choose an agent action
          </div>
          <div className="flex flex-col gap-2.5">
            {demoScenarios.map((s) => {
              const selected = s.id === active.id;
              return (
                <button
                  key={s.id}
                  onClick={() => pick(s)}
                  className={cn(
                    "flex items-center justify-between gap-3 rounded-xl border p-3.5 text-left transition-colors",
                    selected
                      ? "border-neon-blue/40 bg-white/[0.05]"
                      : "border-white/8 bg-white/[0.02] hover:border-white/20"
                  )}
                >
                  <span>
                    <span className="block text-sm font-medium text-white">{s.label}</span>
                    <span className="mt-0.5 block font-mono text-xs text-white/45">
                      {s.request}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold",
                      postureStyle[s.assurance] ?? "text-white/60 border-white/15"
                    )}
                  >
                    {s.assurance}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Console */}
        <div className="relative flex flex-col overflow-hidden rounded-2xl glass-strong p-6">
          <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-neon-violet/15 blur-3xl" />

          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-white/45">
              <span className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
              </span>
              control-plane · console
            </div>
            <span className="rounded-full border border-white/10 px-2.5 py-0.5 text-[10px] font-medium text-white/45">
              simulation only
            </span>
          </div>

          <div className="relative mt-5 rounded-xl border border-white/8 bg-black/25 p-4">
            <Field label="Request" value={active.request} />
            <Field label="Identity" value={active.identity} />
            <Field label="Impact" value={active.impact} />
            <div className="flex items-center justify-between gap-3 py-2">
              <span className="text-xs uppercase tracking-wider text-white/40">
                Assurance posture
              </span>
              <span
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-xs font-semibold",
                  postureStyle[active.assurance] ?? "text-white/60 border-white/15"
                )}
              >
                {active.assurance}
              </span>
            </div>
          </div>

          <button
            onClick={() => setRan(true)}
            className="relative mt-4 inline-flex items-center justify-center gap-2 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition-transform active:scale-[0.98]"
          >
            <Icon name="Play" className="h-4 w-4" />
            Run governance
          </button>

          <div className="relative mt-4 min-h-[172px]">
            <AnimatePresence mode="wait">
              {ran ? (
                <motion.div
                  key={active.id + "-result"}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                  className={cn("rounded-xl p-5 ring-1", d.bg, d.ring)}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className={cn("h-2.5 w-2.5 rounded-full", d.dot)} />
                      <span className={cn("font-display text-2xl font-semibold", d.text)}>
                        {active.decision}
                      </span>
                    </div>
                    <span className="rounded-full border border-white/12 bg-black/20 px-3 py-1 font-mono text-xs text-white/70">
                      {active.control}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-white/75">
                    {active.rationale}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2 border-t border-white/10 pt-3 text-[11px]">
                    <span className="rounded-md bg-white/5 px-2 py-1 text-white/60">
                      evidence coverage:{" "}
                      <span className="text-white/85">{active.evidence.coverage}</span>
                    </span>
                    <span className="rounded-md bg-white/5 px-2 py-1 text-white/60">
                      confidence:{" "}
                      <span className="text-white/85">{active.evidence.confidence}</span>
                    </span>
                    <span className="rounded-md bg-white/5 px-2 py-1 text-white/60">
                      missing:{" "}
                      <span className="text-white/85">{active.evidence.missing}</span>
                    </span>
                  </div>
                  <p className="mt-3 text-[11px] text-white/40">
                    Recorded as an immutable evidence entry — including this outcome.
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key={active.id + "-idle"}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex h-[172px] items-center justify-center rounded-xl border border-dashed border-white/10 text-sm text-white/40"
                >
                  Press “Run governance” to evaluate this action.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
