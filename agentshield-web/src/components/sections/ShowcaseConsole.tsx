"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

type Assurance = { posture: string; score: number; coverage: number; confidence: string };
type Finding = { id: string; severity: string; title: string; observation: string; remediation: string };
type RedTeam = { overall_asr: number; refusal_rate: number; injection_resistance: number; posture_signal: string };
type Runtime = { action: string; target: string; environment: string; read_only: boolean; decision: string };
type Side = { source: string; subject: string; assurance: Assurance; findings: Finding[]; redteam: RedTeam; runtime: Runtime };
export type Data = {
  generated_utc: string;
  demo_agent: string;
  before: Side;
  after: Side;
  deltas: { score_gain: number; findings_removed: number; asr_relative_reduction_pct: number; injection_resistance_gain_pct: number };
  auto_remediation: { applied: string[]; skipped: string[]; diff_lines: number; diff: string };
  disclaimer: string;
};

const postureStyle: Record<string, string> = {
  PASS: "text-emerald-300 border-emerald-400/40 bg-emerald-400/10",
  WARN: "text-amber-300 border-amber-400/40 bg-amber-400/10",
  BLOCK: "text-rose-300 border-rose-400/40 bg-rose-400/10",
};
const decisionStyle: Record<string, string> = {
  ALLOW: "text-emerald-300 border-emerald-400/40 bg-emerald-400/10",
  TRANSFORM: "text-sky-300 border-sky-400/40 bg-sky-400/10",
  APPROVE: "text-cyan-300 border-cyan-400/40 bg-cyan-400/10",
  ESCALATE: "text-amber-300 border-amber-400/40 bg-amber-400/10",
  DENY: "text-rose-300 border-rose-400/40 bg-rose-400/10",
};
const sevStyle: Record<string, string> = {
  CRITICAL: "bg-rose-500 text-white",
  HIGH: "bg-orange-500 text-white",
  MEDIUM: "bg-amber-500 text-black",
  LOW: "bg-slate-500 text-white",
  INFO: "bg-slate-500 text-white",
};

function useCountUp(target: number, active: boolean, ms = 900) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!active) { setV(0); return; }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - t, 3);
      setV(target * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, ms]);
  return v;
}

function Bar({ label, value, tone }: { label: string; value: number; tone: "bad" | "good" }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px] text-white/55">
        <span>{label}</span>
        <span className="font-mono text-white/80">{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/8">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className={cn("h-full rounded-full", tone === "bad"
            ? "bg-gradient-to-r from-rose-500 to-orange-400"
            : "bg-gradient-to-r from-emerald-500 to-teal-400")}
        />
      </div>
    </div>
  );
}

function SideCard({ side, label, dim }: { side: Side; label: string; dim?: boolean }) {
  const a = side.assurance;
  const r = side.runtime;
  return (
    <div className={cn("rounded-2xl glass p-6 transition-opacity duration-500", dim && "opacity-45")}>
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">{label}</span>
        <span className="rounded-full border border-white/12 bg-black/20 px-2.5 py-0.5 font-mono text-[11px] text-white/60">
          {side.source}
        </span>
      </div>

      <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-4">
        <span className={cn("rounded-lg border px-4 py-2 text-lg font-bold tracking-wide", postureStyle[a.posture] ?? "text-white/70 border-white/15")}>
          {a.posture}
        </span>
        <div className="flex gap-6">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/40">Score</div>
            <div className="font-display text-2xl font-semibold text-white">{a.score}<span className="text-sm text-white/40">/100</span></div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-white/40">Findings</div>
            <div className="font-display text-2xl font-semibold text-white">{side.findings.length}</div>
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {side.findings.length === 0 ? (
          <div className="rounded-lg border border-emerald-400/25 bg-emerald-400/5 px-3 py-3 text-center text-sm text-emerald-300">
            <Icon name="ShieldCheck" className="mr-1.5 inline h-4 w-4" />
            All findings remediated
          </div>
        ) : (
          side.findings.map((f) => (
            <div key={f.id} className="flex items-center gap-2.5 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
              <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-bold", sevStyle[f.severity] ?? "bg-slate-500 text-white")}>
                {f.severity}
              </span>
              <span className="font-mono text-[11px] text-white/50">{f.id}</span>
              <span className="text-xs text-white/80">{f.title}</span>
            </div>
          ))
        )}
      </div>

      <div className="mt-4 space-y-3 border-t border-white/10 pt-4">
        <Bar label="Attack success rate" value={side.redteam.overall_asr} tone="bad" />
        <Bar label="Injection resistance" value={side.redteam.injection_resistance} tone="good" />
      </div>

      <div className="mt-4 border-t border-white/10 pt-4">
        <div className="mb-2 text-[11px] text-white/50">
          Runtime decision · <span className="font-mono text-white/70">{r.action}</span> on{" "}
          <span className="font-mono text-white/70">{r.target}</span> ({r.environment})
        </div>
        <span className={cn("inline-block rounded-lg border px-4 py-1.5 text-sm font-bold tracking-wide", decisionStyle[r.decision] ?? "text-white/70 border-white/15")}>
          {r.decision}
        </span>
      </div>
    </div>
  );
}

function DeltaTile({ big, label, active }: { big: string; label: string; active: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={active ? { opacity: 1, y: 0 } : { opacity: 0.2, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-2xl glass-strong p-5 text-center"
    >
      <div className="font-display text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-300 to-teal-300">{big}</div>
      <div className="mt-1 text-xs text-white/55">{label}</div>
    </motion.div>
  );
}

export function ShowcaseConsole({ initial }: { initial: Data }) {
  const [data, setData] = useState<Data>(initial);
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [live, setLive] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => { timers.current.forEach(clearTimeout); timers.current = []; };
  useEffect(() => () => clearTimers(), []);

  const run = useCallback(async () => {
    clearTimers();
    setPhase("running");
    setNote(null);
    setShowDiff(false);
    try {
      const res = await fetch("/api/showcase", { cache: "no-store" });
      const body = await res.json();
      if (res.ok && body.data) {
        setData(body.data as Data);
        setLive(true);
      } else {
        setLive(false);
        setNote(body.error || "Showing the last generated result.");
      }
    } catch {
      setLive(false);
      setNote("Showing the last generated result.");
    }
    // Staged reveal so judges see the remediation "land".
    timers.current.push(setTimeout(() => setPhase("done"), 1100));
  }, []);

  const d = data.deltas;
  const done = phase === "done";
  const scoreGain = useCountUp(d.score_gain, done);

  return (
    <div className="container-x pb-28">
      {/* Control bar */}
      <div className="mb-10 flex flex-col items-start gap-4 rounded-2xl glass-strong p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-white">
            Demo subject: <span className="text-neon-cyan">{data.demo_agent}</span>
          </div>
          <div className="mt-0.5 text-xs text-white/45">
            One agent, hardened. Same engine, same evidence rules — the improvement is measured, not asserted.
            {live && <span className="ml-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] text-emerald-300">live engine</span>}
          </div>
        </div>
        <button
          onClick={run}
          disabled={phase === "running"}
          className="inline-flex shrink-0 items-center gap-2 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] px-6 py-3 text-sm font-semibold text-white shadow-glow transition-transform active:scale-[0.98] disabled:opacity-50"
        >
          <Icon name={phase === "running" ? "Loader2" : done ? "RotateCcw" : "ShieldCheck"} className={cn("h-4 w-4", phase === "running" && "animate-spin")} />
          {phase === "running" ? "Remediating…" : done ? "Replay remediation" : "Run remediation"}
        </button>
      </div>

      {note && (
        <div className="mb-6 rounded-lg border border-amber-400/25 bg-amber-400/5 px-4 py-2 text-xs text-amber-200/80">
          {note}
        </div>
      )}

      {/* Delta tiles */}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <DeltaTile big={`+${done ? Math.round(scoreGain) : 0}`} label="assurance score gained" active={done} />
        <DeltaTile big={`−${d.findings_removed}`} label="findings resolved" active={done} />
        <DeltaTile big={`−${d.asr_relative_reduction_pct}%`} label="attack success rate" active={done} />
        <DeltaTile big={`+${d.injection_resistance_gain_pct}%`} label="injection resistance" active={done} />
      </div>

      {/* Before / after */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SideCard side={data.before} label="Before — as authored" />
        <AnimatePresence mode="wait">
          {done ? (
            <motion.div
              key="after"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            >
              <SideCard side={data.after} label="After — remediated" />
            </motion.div>
          ) : (
            <motion.div
              key="pending"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex min-h-[420px] items-center justify-center rounded-2xl border border-dashed border-white/12 text-center text-sm text-white/40"
            >
              {phase === "running"
                ? "Applying AgentShield remediation…"
                : "Run the remediation to reveal the hardened agent."}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Auto-remediation evidence */}
      {done && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="mt-8 rounded-2xl glass p-6"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Icon name="Wrench" className="h-4 w-4 text-neon-cyan" />
              AgentShield generated the fix — {data.auto_remediation.diff_lines} diff lines
            </div>
            <button
              onClick={() => setShowDiff((s) => !s)}
              className="rounded-full border border-white/12 px-3 py-1 text-xs text-white/60 transition-colors hover:text-white"
            >
              {showDiff ? "Hide diff" : "Show diff"}
            </button>
          </div>
          <ul className="mt-3 space-y-1.5">
            {data.auto_remediation.applied.map((a) => (
              <li key={a} className="flex items-start gap-2 text-sm text-white/75">
                <Icon name="Check" className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                {a}
              </li>
            ))}
          </ul>
          <AnimatePresence>
            {showDiff && (
              <motion.pre
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 overflow-auto rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-[11px] leading-relaxed"
              >
                {data.auto_remediation.diff.split("\n").map((ln, i) => (
                  <div
                    key={i}
                    className={cn(
                      ln.startsWith("+++") || ln.startsWith("---") || ln.startsWith("@@")
                        ? "text-sky-300"
                        : ln.startsWith("+")
                          ? "text-emerald-300"
                          : ln.startsWith("-")
                            ? "text-rose-300"
                            : "text-white/55",
                    )}
                  >
                    {ln || "\u00a0"}
                  </div>
                ))}
              </motion.pre>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      <p className="mt-8 text-xs leading-relaxed text-white/40">{data.disclaimer}</p>
    </div>
  );
}
