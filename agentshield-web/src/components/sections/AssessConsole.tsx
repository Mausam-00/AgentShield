"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { AssessProcessing } from "@/components/ui/AssessProcessing";
import { cn } from "@/lib/utils";

type Summary = {
  subject: string;
  assurance_posture: string;
  assurance_score: number;
  findings_count: number;
  runtime_decision: string;
  redteam_posture: string;
  defense_coverage: number | null;
  residual_exposure: number | null;
  rai_posture: string;
};

const decisionStyle: Record<string, { text: string; ring: string; bg: string; dot: string }> = {
  ALLOW: { text: "text-emerald-300", ring: "ring-emerald-400/40", bg: "bg-emerald-400/10", dot: "bg-emerald-400" },
  TRANSFORM: { text: "text-sky-300", ring: "ring-sky-400/40", bg: "bg-sky-400/10", dot: "bg-sky-400" },
  APPROVE: { text: "text-cyan-300", ring: "ring-cyan-400/40", bg: "bg-cyan-400/10", dot: "bg-cyan-400" },
  ESCALATE: { text: "text-amber-300", ring: "ring-amber-400/40", bg: "bg-amber-400/10", dot: "bg-amber-400" },
  DENY: { text: "text-rose-300", ring: "ring-rose-400/40", bg: "bg-rose-400/10", dot: "bg-rose-400" },
};

const postureStyle: Record<string, string> = {
  PASS: "text-emerald-300 border-emerald-400/30 bg-emerald-400/10",
  "RAI-PASS": "text-emerald-300 border-emerald-400/30 bg-emerald-400/10",
  WARN: "text-amber-300 border-amber-400/30 bg-amber-400/10",
  "RAI-WARN": "text-amber-300 border-amber-400/30 bg-amber-400/10",
  BLOCK: "text-rose-300 border-rose-400/30 bg-rose-400/10",
  "RAI-BLOCK": "text-rose-300 border-rose-400/30 bg-rose-400/10",
};

const postureHex: Record<string, string> = {
  PASS: "#34d399",
  WARN: "#fbbf24",
  BLOCK: "#fb7185",
};

function pct(v: number | null): string {
  return v == null ? "—" : `${Math.round(v * 100)}%`;
}

function ScoreRing({ score, posture }: { score: number; posture: string }) {
  const radius = 40;
  const circ = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const dash = (clamped / 100) * circ;
  const color = postureHex[posture] ?? "#38e1ff";
  return (
    <div className="relative grid h-[104px] w-[104px] shrink-0 place-items-center">
      <svg width="104" height="104" viewBox="0 0 104 104" className="-rotate-90">
        <circle cx="52" cy="52" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="9" />
        <circle
          cx="52"
          cy="52"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
        />
      </svg>
      <div className="absolute text-center leading-none">
        <div className="font-display text-2xl font-bold text-white">{score}</div>
        <div className="mt-0.5 text-[9px] uppercase tracking-[0.14em] text-white/45">/ 100</div>
      </div>
    </div>
  );
}

function safeName(subject: string): string {
  const cleaned = subject.replace(/\s+/g, "_").replace(/[^A-Za-z0-9._-]/g, "");
  return `AgentShield_AI_Report_${cleaned || "Agent"}.html`;
}

function PosturePill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
      <span className="text-[11px] uppercase tracking-wider text-white/45">{label}</span>
      <span className={cn("rounded-full border px-2.5 py-0.5 text-xs font-semibold", postureStyle[value] ?? "text-white/70 border-white/15")}>
        {value}
      </span>
    </div>
  );
}

export function AssessConsole() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const htmlRef = useRef<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const accept = useCallback((f: File | null) => {
    setError(null);
    setSummary(null);
    htmlRef.current = null;
    if (f && !/\.(md|markdown|txt)$/i.test(f.name)) {
      setError("Please upload a Markdown (.md) agent definition.");
      setFile(null);
      return;
    }
    setFile(f);
  }, []);

  async function run() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setSummary(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/assess", { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Assessment failed.");
      htmlRef.current = data.html as string;
      setSummary(data.summary as Summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assessment failed.");
    } finally {
      setLoading(false);
    }
  }

  function download() {
    if (!htmlRef.current || !summary) return;
    const blob = new Blob([htmlRef.current], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = safeName(summary.subject);
    a.click();
    URL.revokeObjectURL(url);
  }

  function preview() {
    if (!htmlRef.current) return;
    const blob = new Blob([htmlRef.current], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  const d = summary ? decisionStyle[summary.runtime_decision] ?? decisionStyle.DENY : decisionStyle.ALLOW;

  return (
    <section id="demo" className="container-x scroll-mt-28 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Assess your agent · simulation"
        title={
          <>
            Upload an agent definition and{" "}
            <span className="text-gradient-neon">get a governed report</span>
          </>
        }
        subtitle="Drop a custom-agent .md file. AgentShield runs the real engine — static assessment, OBSERVE, Gate R red-team, and a Responsible AI read — and hands back a downloadable, self-contained HTML report. Nothing is executed against a target."
      />

      <div className="mt-16 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        {/* Upload panel */}
        <div className="rounded-2xl glass p-6">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
            <Icon name="Upload" className="h-4 w-4 text-neon-cyan" />
            Upload an agent .md
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              accept(e.dataTransfer.files?.[0] ?? null);
            }}
            onClick={() => inputRef.current?.click()}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 text-center transition-colors",
              dragging ? "border-neon-blue/60 bg-white/[0.05]" : "border-white/12 bg-white/[0.02] hover:border-white/25"
            )}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".md,.markdown,.txt"
              className="hidden"
              onChange={(e) => accept(e.target.files?.[0] ?? null)}
            />
            <div className="grid h-11 w-11 place-items-center rounded-full bg-white/[0.06]">
              <Icon name={file ? "FileText" : "Upload"} className="h-5 w-5 text-white/70" />
            </div>
            {file ? (
              <div>
                <div className="text-sm font-medium text-white">{file.name}</div>
                <div className="mt-0.5 text-xs text-white/45">{(file.size / 1024).toFixed(1)} KB · click to replace</div>
              </div>
            ) : (
              <div>
                <div className="text-sm font-medium text-white">Drag & drop, or click to browse</div>
                <div className="mt-0.5 text-xs text-white/45">.md agent definition · max 512 KB</div>
              </div>
            )}
          </div>

          <button
            onClick={run}
            disabled={!file || loading}
            className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition-transform active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Icon name={loading ? "Loader2" : "ShieldCheck"} className={cn("h-4 w-4", loading && "animate-spin")} />
            {loading ? "Assessing…" : "Run assessment"}
          </button>

          <p className="mt-3 text-[11px] leading-relaxed text-white/40">
            Static, simulation-only. Your file is processed transiently to render the report and is not retained.
          </p>
        </div>

        {/* Result panel */}
        <div className="relative flex flex-col overflow-hidden rounded-2xl glass-strong p-6">
          <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-neon-violet/15 blur-3xl" />

          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-white/45">
              <span className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
              </span>
              control-plane · report
            </div>
            <span className="rounded-full border border-white/10 px-2.5 py-0.5 text-[10px] font-medium text-white/45">
              simulation only
            </span>
          </div>

          <div className="relative mt-5 min-h-[300px]">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <AssessProcessing />
                </motion.div>
              ) : error ? (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex h-[300px] flex-col items-center justify-center gap-3 rounded-xl border border-rose-400/25 bg-rose-400/5 px-6 text-center text-sm text-rose-200/90"
                >
                  <Icon name="AlertTriangle" className="h-6 w-6 text-rose-300" />
                  {error}
                </motion.div>
              ) : summary ? (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                  className="space-y-4"
                >
                  {/* Report header */}
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-white/40">
                        Assessment report
                      </div>
                      <div className="mt-0.5 font-display text-lg font-semibold text-white">
                        {summary.subject}
                      </div>
                    </div>
                    <span
                      className={cn(
                        "rounded-full border px-3 py-1 text-xs font-semibold",
                        postureStyle[summary.assurance_posture] ?? "text-white/70 border-white/15"
                      )}
                    >
                      {summary.assurance_posture}
                    </span>
                  </div>

                  {/* Hero: assurance score + runtime decision */}
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="flex items-center gap-4 rounded-xl border border-white/8 bg-white/[0.02] p-4">
                      <ScoreRing score={summary.assurance_score} posture={summary.assurance_posture} />
                      <div className="min-w-0">
                        <div className="text-[11px] uppercase tracking-wider text-white/45">
                          Assurance score
                        </div>
                        <div className="mt-1 font-display text-3xl font-semibold text-white">
                          {summary.assurance_score}
                          <span className="text-base font-normal text-white/40">/100</span>
                        </div>
                        <div className="mt-1.5">
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
                              summary.findings_count === 0
                                ? "text-emerald-300 border-emerald-400/30 bg-emerald-400/10"
                                : "text-amber-300 border-amber-400/30 bg-amber-400/10"
                            )}
                          >
                            <Icon
                              name={summary.findings_count === 0 ? "ShieldCheck" : "AlertTriangle"}
                              className="h-3.5 w-3.5"
                            />
                            {summary.findings_count === 0
                              ? "No open findings"
                              : `${summary.findings_count} open finding${summary.findings_count === 1 ? "" : "s"}`}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className={cn("flex flex-col justify-center rounded-xl p-4 ring-1", d.bg, d.ring)}>
                      <div className="text-[11px] uppercase tracking-wider text-white/45">
                        Runtime decision
                      </div>
                      <div className="mt-1.5 flex items-center gap-2.5">
                        <span className={cn("h-3 w-3 rounded-full", d.dot)} />
                        <span className={cn("font-display text-3xl font-semibold", d.text)}>
                          {summary.runtime_decision}
                        </span>
                      </div>
                      <p className="mt-2 text-[11px] leading-relaxed text-white/45">
                        Deterministic runtime verdict — the assurance posture is advisory, not authorization.
                      </p>
                    </div>
                  </div>

                  {/* Secondary signals */}
                  <div className="grid grid-cols-2 gap-2.5">
                    <PosturePill label="Red-team" value={summary.redteam_posture} />
                    <PosturePill label="Responsible AI" value={summary.rai_posture} />
                    <div className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
                      <span className="text-[11px] uppercase tracking-wider text-white/45">Defense coverage</span>
                      <span className="font-mono text-sm text-white/85">{pct(summary.defense_coverage)}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
                      <span className="text-[11px] uppercase tracking-wider text-white/45">Residual exposure</span>
                      <span className="font-mono text-sm text-amber-200/90">{pct(summary.residual_exposure)}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2.5 border-t border-white/10 pt-4">
                    <button
                      onClick={download}
                      className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/15 transition-colors hover:bg-white/[0.1]"
                    >
                      <Icon name="Download" className="h-4 w-4 text-neon-cyan" />
                      Download report
                    </button>
                    <button
                      onClick={preview}
                      className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-white/70 ring-1 ring-white/10 transition-colors hover:text-white"
                    >
                      <Icon name="ArrowUpRight" className="h-4 w-4" />
                      Preview in new tab
                    </button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex h-[300px] items-center justify-center rounded-xl border border-dashed border-white/10 px-6 text-center text-sm text-white/40"
                >
                  Upload an agent definition and run the assessment to see the governed verdict and download the report.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
