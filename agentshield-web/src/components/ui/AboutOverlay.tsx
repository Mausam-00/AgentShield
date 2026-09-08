"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  animate,
  motion,
  useMotionTemplate,
  useMotionValue,
  useTransform,
} from "framer-motion";
import { site } from "@/lib/site";
import { Icon } from "@/components/ui/Icon";
import { ShieldMark } from "@/components/brand/ShieldMark";
import { cn } from "@/lib/utils";

/* Full-screen "About Us" experience, opened from the navbar (event:
   "open-about"). It reveals with a zipper unzip: a slider pull travels down a
   toothed seam while two curtains part in a widening wedge, then slide away to
   expose the page. Content is project-true and sourced from the AgentShield
   project report — deterministic authorization, assurance kept separate from
   authorization, fail-closed, never certification. */

// ---------------------------------------------------------------- content ---
const TOPICS = [
  {
    icon: "Sparkles",
    title: "What it is",
    body: "A deterministic security control plane for AI agents. It predicts what an agent can do, governs the changes it may make, and decides — with versioned, auditable policy — whether an action is allowed, transformed, escalated or denied.",
  },
  {
    icon: "Radar",
    title: "Why it's needed now",
    body: "Agents now call tools, touch data and change real systems. A single manipulated or over-privileged action can be irreversible. Scanners and content filters were never built to govern an agent's authority or the blast radius of an action.",
  },
  {
    icon: "Workflow",
    title: "The seven-gate workflow",
    body: "Assurance audit → interception → identity → operational impact → deterministic policy → human approval → constrained safe plan → outcome validation. Every gate is deterministic, versioned and independently tested.",
  },
  {
    icon: "Layers",
    title: "Two lanes, never conflated",
    body: "An offline, network-free core decides authorization, so verdicts are reproducible. An opt-in live lane isolates every real signal — red-team, content-safety, fairness — and never leaks into the core.",
  },
];

const STANDOUT = [
  {
    icon: "Radar",
    title: "Adversarial red-team & ASR",
    body: "Nine attack families scored statically as inert data for defense coverage, residual exposure and Attack Success Rate. Reports lead with coverage; static posture is capped at WARN, never PASS.",
  },
  {
    icon: "Scale",
    title: "Responsible AI posture",
    body: "Six weighted RAI pillars (fairness, reliability, privacy, inclusiveness, transparency, accountability) scored into an advisory RAI-PASS / WARN / BLOCK — kept strictly separate from authorization.",
  },
  {
    icon: "Gauge",
    title: "Token optimization layer",
    body: "A measured efficiency layer cuts context tokens up to ~33% and relative compute cost ~54% — while asserting every decision stays byte-for-byte equal to baseline. It can never alter a policy or authorization.",
  },
  {
    icon: "ScrollText",
    title: "Evidence provenance & confidence",
    body: "Every finding is traced to its source and weighted by confidence. Optional model narrative can explain, but can never silently override, strip or fabricate deterministic evidence.",
  },
  {
    icon: "Lock",
    title: "Compliance framework mapping",
    body: "Advisory, versioned mapping of control families to OWASP LLM Top 10, NIST AI RMF and the EU AI Act. Absent evidence stays 'Unevidenced' — and 'Evidenced' is still never a certification claim.",
  },
  {
    icon: "ShieldCheck",
    title: "Self-contained, audit-ready reports",
    body: "One HTML file: no scripts, no external calls, credential-like fields redacted. Every outcome — including denials and failures — is written to a tamper-evident ledger.",
  },
];

const MARKET = [
  {
    icon: "Workflow",
    stat: "Now",
    label: "Category being created",
    body: "Agent frameworks, MCP tooling and multi-agent orchestration are reaching production ahead of the controls to govern them.",
  },
  {
    icon: "Scale",
    stat: "EU AI Act",
    label: "Regulatory pull",
    body: "Published risk frameworks (OWASP LLM, NIST AI RMF) and regulation now expect demonstrable controls — not claims of safety.",
  },
  {
    icon: "Radar",
    stat: "Gap",
    label: "Unserved need",
    body: "AppSec scanners, content filters and model-evals each cover a slice; none give deterministic, action-level authorization with human-in-the-loop and audit evidence.",
  },
  {
    icon: "Lock",
    stat: "1 action",
    label: "Buyer urgency",
    body: "The cost of a single irreversible agent action — data loss, outage, exfiltration — dwarfs the cost of a governance layer.",
  },
];

const DIFFERENTIATORS: { label: string; us: string; them: string }[] = [
  {
    label: "Authorization decision",
    us: "Deterministic, versioned policy with reason codes",
    them: "LLM judgement or heuristic scoring",
  },
  {
    label: "Assurance vs. authorization",
    us: "Strictly separated — PASS is never authorization",
    them: "Blended into a single score or letter grade",
  },
  {
    label: "Failure mode",
    us: "Fail-closed on unknown identity, invalid approval or missing policy",
    them: "Best-effort — may silently pass",
  },
  {
    label: "Action safety",
    us: "Blast radius + reversibility + constrained safe plan",
    them: "Not modelled",
  },
  {
    label: "Evidence handling",
    us: "Provenance-weighted, tamper-evident, never fabricated",
    them: "Flat findings; example noise drives posture",
  },
  {
    label: "Reports & data",
    us: "Portable, redacted, offline-safe record",
    them: "Locked in a SaaS dashboard",
  },
];

const PRINCIPLES = [
  "Deterministic controls own authorization",
  "Assurance is kept separate from authorization",
  "Fail closed on anything unknown or high-risk",
  "Never fabricate evidence, connectors or results",
];

// ---------------------------------------------------------------- timing ---
const OPEN_MS = 2600;
const CLOSE_MS = 1000;
const TEETH = 26;

export function AboutOverlay() {
  const [mounted, setMounted] = useState(false);
  const [closing, setClosing] = useState(false);
  const progress = useMotionValue(0); // 0 = zipped shut, 1 = fully open

  // Derived motion values driving the zipper.
  const sliderY = useTransform(progress, [0, 0.7, 1], [0, 100, 100]); // %
  const wedge = useTransform(progress, [0, 0.7], [0, 100]); // top recede %
  const leftTopX = useTransform(wedge, (v) => 100 - v); // left curtain inner top
  const rightTopX = wedge; // right curtain inner top
  const leftX = useTransform(progress, [0.7, 1], ["0%", "-112%"]);
  const rightX = useTransform(progress, [0.7, 1], ["0%", "112%"]);
  const sliderOpacity = useTransform(progress, [0, 0.62, 0.72], [1, 1, 0]);
  const contentOpacity = useTransform(progress, [0.28, 0.7], [0, 1]);
  const contentScale = useTransform(progress, [0.28, 1], [0.985, 1]);
  const contentY = useTransform(progress, [0.28, 1], [26, 0]);
  const chromeOpacity = useTransform(progress, [0.55, 0.95], [0, 1]);

  const clipLeft = useMotionTemplate`polygon(0% 0%, ${leftTopX}% 0%, 100% ${sliderY}%, 100% 100%, 0% 100%)`;
  const clipRight = useMotionTemplate`polygon(${rightTopX}% 0%, 100% 0%, 100% 100%, 0% 100%, 0% ${sliderY}%)`;
  const sliderTop = useMotionTemplate`${sliderY}%`;

  const openRef = useRef<ReturnType<typeof animate> | null>(null);

  const close = useCallback(() => {
    if (closing) return;
    setClosing(true);
    openRef.current?.stop();
    const anim = animate(progress, 0, {
      type: "tween",
      duration: CLOSE_MS / 1000,
      ease: [0.7, 0, 0.84, 0],
      onComplete: () => {
        setMounted(false);
        setClosing(false);
      },
    });
    openRef.current = anim;
  }, [closing, progress]);

  // Open on event.
  useEffect(() => {
    const onOpen = () => {
      setClosing(false);
      setMounted(true);
    };
    window.addEventListener("open-about", onOpen);
    return () => window.removeEventListener("open-about", onOpen);
  }, []);

  // Run the unzip once mounted; lock scroll; wire Escape.
  useEffect(() => {
    if (!mounted) return;
    progress.set(0);
    openRef.current = animate(progress, 1, {
      type: "tween",
      duration: OPEN_MS / 1000,
      ease: [0.45, 0.05, 0.55, 0.95],
    });
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
      openRef.current?.stop();
    };
  }, [mounted, progress, close]);

  if (!mounted) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="About AgentShield AI"
      className="fixed inset-0 z-[100] overflow-hidden"
    >
      {/* opaque backdrop so the page behind never shows through the seam */}
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(1200px_600px_at_80%_-10%,rgba(88,101,242,0.16),transparent),radial-gradient(900px_500px_at_-10%_10%,rgba(56,225,255,0.12),transparent)] bg-ink-950"
      />

      {/* ----------------------------------------------------- content page */}
      <motion.div
        style={{ opacity: contentOpacity, scale: contentScale, y: contentY }}
        className="absolute inset-0 overflow-y-auto"
      >
        <div className="mx-auto w-full max-w-6xl px-5 pb-24 pt-[max(4.5rem,7vh)] sm:px-8">
          {/* hero */}
          <div className="flex flex-col items-start gap-5">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.03] px-3 py-1 text-[11px] font-medium uppercase tracking-widest text-neon-cyan">
              <Icon name="Sparkles" className="h-3 w-3" /> About Us
            </span>
            <div className="flex items-center gap-4">
              <span className="h-14 w-14 shrink-0">
                <ShieldMark />
              </span>
              <div>
                <h1 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-5xl">
                  AgentShield <span className="text-gradient-neon">AI</span>
                </h1>
                <p className="mt-1 text-sm text-white/55 sm:text-base">
                  {site.tagline}
                </p>
              </div>
            </div>
            <p className="max-w-3xl text-[15px] leading-relaxed text-white/70 sm:text-lg">
              AgentShield governs the risk of autonomous agents. It audits an
              agent&#39;s design, evaluates a proposed action{" "}
              <span className="text-white">before</span> it reaches a target,
              predicts operational impact, applies deterministic policy, routes
              human approval, produces a constrained safe plan, validates the
              outcome, and preserves tamper-evident evidence — keeping{" "}
              <span className="text-white">
                assurance strictly separate from authorization
              </span>
              , and never letting a model grant permission.
            </p>
            <div className="flex flex-wrap items-center gap-2 text-[13px] text-white/60">
              {["Predict", "Govern", "Approve", "Execute Safely", "Audit"].map(
                (w) => (
                  <span
                    key={w}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1"
                  >
                    {w}
                  </span>
                )
              )}
            </div>
          </div>

          {/* important topics */}
          <SectionTitle icon="Layers" text="The essentials" />
          <div className="grid gap-4 sm:grid-cols-2">
            {TOPICS.map((t) => (
              <Card key={t.title} {...t} />
            ))}
          </div>

          {/* standout capabilities */}
          <SectionTitle icon="Zap" text="Standout capabilities" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {STANDOUT.map((s) => (
              <Card key={s.title} {...s} accent />
            ))}
          </div>

          {/* market opportunity */}
          <SectionTitle icon="Radar" text="Market opportunity" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {MARKET.map((m) => (
              <div
                key={m.label}
                className="rounded-2xl border border-white/10 bg-white/[0.02] p-5"
              >
                <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan">
                  <Icon name={m.icon} className="h-4 w-4" />
                </span>
                <div className="text-2xl font-semibold text-white">
                  {m.stat}
                </div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-neon-cyan">
                  {m.label}
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                  {m.body}
                </p>
              </div>
            ))}
          </div>

          {/* differentiation */}
          <SectionTitle icon="Scale" text="Why we stand out" />
          <div className="overflow-hidden rounded-2xl border border-white/10">
            <div className="grid grid-cols-[1.1fr_1.5fr_1.4fr] bg-white/[0.04] text-[11px] font-semibold uppercase tracking-wider text-white/45">
              <span className="px-4 py-2.5">Dimension</span>
              <span className="px-4 py-2.5 text-neon-cyan">AgentShield AI</span>
              <span className="px-4 py-2.5">Typical agent scanners</span>
            </div>
            {DIFFERENTIATORS.map((row, i) => (
              <div
                key={row.label}
                className={cn(
                  "grid grid-cols-[1.1fr_1.5fr_1.4fr] text-sm",
                  i % 2 ? "bg-white/[0.015]" : "bg-transparent"
                )}
              >
                <span className="px-4 py-3 font-medium text-white/70">
                  {row.label}
                </span>
                <span className="flex items-start gap-2 px-4 py-3 text-white/85">
                  <Icon
                    name="Check"
                    className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400"
                  />
                  {row.us}
                </span>
                <span className="px-4 py-3 text-white/45">{row.them}</span>
              </div>
            ))}
          </div>

          {/* principles */}
          <SectionTitle icon="Lock" text="Non-negotiable principles" />
          <div className="grid gap-3 sm:grid-cols-2">
            {PRINCIPLES.map((p) => (
              <div
                key={p}
                className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3"
              >
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan">
                  <Icon name="Check" className="h-3.5 w-3.5" />
                </span>
                <span className="text-sm text-white/80">{p}</span>
              </div>
            ))}
          </div>

          <p className="mt-6 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-xs leading-relaxed text-white/45">
            PASS is not certification. WARN is not authorization. AgentShield AI
            provides assurance and governance support only — the named owner and
            approver remain accountable for every action.
          </p>

          {/* actions */}
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="/#demo"
              onClick={close}
              className="group inline-flex items-center justify-center gap-2 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition-shadow hover:shadow-glow-violet"
            >
              <Icon name="Play" className="h-4 w-4" />
              Run the Engine
            </Link>
            <Link
              href="/products"
              onClick={close}
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 bg-white/[0.03] px-5 py-2.5 text-sm font-semibold text-white/85 transition-colors hover:border-white/25 hover:bg-white/[0.07]"
            >
              Explore the platform
              <Icon name="ArrowRight" className="h-4 w-4" />
            </Link>
            <a
              href={site.repo}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 bg-white/[0.03] px-5 py-2.5 text-sm font-semibold text-white/85 transition-colors hover:border-white/25 hover:bg-white/[0.07] sm:ml-auto"
            >
              <Icon name="GitBranch" className="h-4 w-4" />
              GitHub
              <Icon name="ArrowUpRight" className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </motion.div>

      {/* --------------------------------------------------- zipper curtains */}
      <motion.div
        aria-hidden
        style={{ clipPath: clipLeft, x: leftX }}
        className="pointer-events-none absolute inset-y-0 left-0 w-1/2 bg-[linear-gradient(90deg,#080d18_0%,#0d1526_82%,#111b30_100%)]"
      >
        <Teeth side="right" />
      </motion.div>
      <motion.div
        aria-hidden
        style={{ clipPath: clipRight, x: rightX }}
        className="pointer-events-none absolute inset-y-0 right-0 w-1/2 bg-[linear-gradient(270deg,#080d18_0%,#0d1526_82%,#111b30_100%)]"
      >
        <Teeth side="left" />
      </motion.div>

      {/* seam glow behind slider (below the pull, still-closed portion) */}
      <motion.div
        aria-hidden
        style={{ opacity: sliderOpacity }}
        className="pointer-events-none absolute inset-y-0 left-1/2 -ml-px w-0.5 bg-gradient-to-b from-transparent via-neon-cyan/40 to-neon-violet/30"
      />

      {/* -------------------------------------------------------- slider pull */}
      <motion.div
        aria-hidden
        style={{ top: sliderTop, opacity: sliderOpacity }}
        className="pointer-events-none absolute left-1/2 z-[30] -translate-x-1/2 -translate-y-1/2"
      >
        <div className="relative flex flex-col items-center">
          <div className="h-8 w-11 rounded-md bg-[linear-gradient(180deg,#e8edf6,#aab6c8_60%,#7c88aa)] shadow-[0_2px_10px_rgba(0,0,0,0.5)] ring-1 ring-white/40" />
          <div className="-mt-1 h-3 w-3 rounded-full bg-[#8b98ad] ring-1 ring-white/30" />
          <div className="mt-0.5 h-6 w-2 rounded-full bg-[linear-gradient(180deg,#cfd7e4,#8a97ab)] shadow-[0_2px_8px_rgba(0,0,0,0.55)]" />
        </div>
      </motion.div>

      {/* ------------------------------------------------------------- chrome */}
      <motion.button
        onClick={close}
        aria-label="Close About"
        style={{ opacity: chromeOpacity }}
        className="fixed right-4 top-4 z-[40] grid h-10 w-10 place-items-center rounded-xl border border-white/15 bg-white/[0.04] text-white/70 backdrop-blur transition-colors hover:border-white/30 hover:text-white sm:right-6 sm:top-6"
      >
        <Icon name="X" className="h-5 w-5" />
      </motion.button>
    </div>
  );
}

// -------------------------------------------------------------------- teeth ---
function Teeth({ side }: { side: "left" | "right" }) {
  return (
    <div
      className={cn(
        "absolute inset-y-0 flex w-4 flex-col justify-between",
        side === "right" ? "right-0" : "left-0"
      )}
      style={{
        background:
          "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(120,140,170,0.18))",
      }}
    >
      {Array.from({ length: TEETH }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "block h-[2.2%] w-3 bg-[linear-gradient(90deg,#9fb0c8,#5c6b82)] shadow-[0_0_2px_rgba(0,0,0,0.5)]",
            side === "right"
              ? "self-start rounded-r-sm"
              : "self-end rounded-l-sm",
            i % 2 === 0 ? "opacity-95" : "opacity-70"
          )}
        />
      ))}
    </div>
  );
}

// -------------------------------------------------------------------- pieces ---
function SectionTitle({ icon, text }: { icon: string; text: string }) {
  return (
    <h2 className="mb-4 mt-12 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-white/50">
      <Icon name={icon} className="h-4 w-4 text-neon-cyan" />
      {text}
    </h2>
  );
}

function Card({
  icon,
  title,
  body,
  accent,
}: {
  icon: string;
  title: string;
  body: string;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border p-5 transition-colors",
        accent
          ? "border-neon-violet/20 bg-gradient-to-br from-neon-blue/[0.06] to-neon-violet/[0.06] hover:border-neon-violet/40"
          : "border-white/10 bg-white/[0.02] hover:border-white/20"
      )}
    >
      <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <h3 className="text-[15px] font-semibold text-white">{title}</h3>
      <p className="mt-1.5 text-[13px] leading-relaxed text-white/60">{body}</p>
    </div>
  );
}
