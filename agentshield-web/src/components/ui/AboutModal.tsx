"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { site } from "@/lib/site";
import { Icon } from "@/components/ui/Icon";
import { ShieldMark } from "@/components/brand/ShieldMark";
import { cn } from "@/lib/utils";

/* Everything a first-time visitor needs to understand AgentShield AI, opened
   from the navbar "About" button (event: "open-about"). Content is honest and
   project-true: deterministic authorization, assurance kept separate from
   authorization, fail-closed, never certification. */

const KEY_FEATURES = [
  {
    icon: "Target",
    title: "BlastRadius — capability & impact mapping",
    body: "Maps exactly what an agent can do — tools, permissions, trust boundaries — and predicts how far any action reaches before it runs.",
  },
  {
    icon: "ShieldCheck",
    title: "Deterministic policy engine",
    body: "Versioned controls return exactly one verdict with reason codes. No model can weaken a hard control or grant access.",
  },
  {
    icon: "GitBranch",
    title: "Semantic safety invariants",
    body: "add_disk never becomes remove_disk. Meaning is preserved and plans stay reversible before anything touches a target.",
  },
  {
    icon: "Radar",
    title: "Adversarial red-team",
    body: "Static, simulation-only probing across nine attack families, surfaced as a defense-coverage heatmap — not a live attack.",
  },
];

const STANDOUT = [
  {
    icon: "ScrollText",
    title: "Evidence provenance & confidence weighting",
    body: "Every finding is traced to where its evidence lives. Illustrative snippets in fenced examples are transparently down-weighted — never hidden, never inflated.",
  },
  {
    icon: "Scale",
    title: "Compliance framework mapping",
    body: "Advisory, versioned mapping to OWASP Top 10 for LLMs, NIST AI RMF and the EU AI Act — with honest coverage statuses. Support for compliance, never a certification claim.",
  },
  {
    icon: "Layers",
    title: "Fix These First — prioritized remediation",
    body: "Findings ranked by effective severity × evidence confidence, so the report is actionable, not just diagnostic.",
  },
  {
    icon: "Lock",
    title: "Self-contained, audit-ready reports",
    body: "One HTML file: no scripts, no external calls, credential-like fields redacted, URLs defanged. Every outcome — including denials — is recorded.",
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
    label: "Evidence handling",
    us: "Provenance-weighted; never fabricated",
    them: "Flat findings; example noise drives posture",
  },
  {
    label: "Runtime posture",
    us: "Approve / Transform / Deny gate with kill switch",
    them: "Scan-only, no runtime control plane",
  },
  {
    label: "Reports & data",
    us: "Portable, redacted, tamper-evident record",
    them: "Locked in a SaaS dashboard",
  },
];

const PRINCIPLES = [
  "Deterministic controls own authorization",
  "Assurance is kept separate from authorization",
  "Fail closed on anything unknown or high-risk",
  "Never fabricate evidence, connectors or results",
];

export function AboutModal() {
  const [open, setOpen] = useState(false);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("open-about", onOpen);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("open-about", onOpen);
      window.removeEventListener("keydown", onKey);
    };
  }, [close]);

  // Lock body scroll while the modal is open.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[95] flex items-start justify-center px-4 py-[6vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div
            className="absolute inset-0 bg-ink-950/75 backdrop-blur-md"
            onClick={close}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="About AgentShield AI"
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="glass-strong relative z-10 flex max-h-[88vh] w-full max-w-4xl flex-col overflow-hidden rounded-3xl shadow-card"
          >
            {/* Header */}
            <div className="relative flex items-center gap-4 border-b border-white/10 px-6 py-5 sm:px-8">
              <span className="h-11 w-11 shrink-0">
                <ShieldMark />
              </span>
              <div className="min-w-0">
                <h2 className="font-display text-xl font-semibold tracking-tight text-white sm:text-2xl">
                  AgentShield <span className="text-gradient-neon">AI</span>
                </h2>
                <p className="truncate text-sm text-white/55">{site.tagline}</p>
              </div>
              <button
                onClick={close}
                aria-label="Close"
                className="ml-auto grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-white/12 bg-white/[0.03] text-white/60 transition-colors hover:border-white/25 hover:text-white"
              >
                <Icon name="X" className="h-4 w-4" />
              </button>
            </div>

            {/* Scrollable body */}
            <div className="overflow-y-auto px-6 py-6 sm:px-8">
              {/* What it is */}
              <section>
                <span className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.03] px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-neon-cyan">
                  <Icon name="Sparkles" className="h-3 w-3" /> What it is
                </span>
                <p className="mt-3 text-[15px] leading-relaxed text-white/75">
                  AgentShield AI is a{" "}
                  <span className="text-white">
                    deterministic security control plane for AI agents
                  </span>
                  . It predicts what an agent can do, governs the changes it may
                  make, and decides — with versioned, auditable policy — whether an
                  action is allowed, transformed, escalated or denied. It produces
                  evidence-based assurance reports while keeping{" "}
                  <span className="text-white">
                    assurance strictly separate from runtime authorization
                  </span>
                  . It fails closed, never fabricates evidence, and never claims
                  certification.
                </p>
              </section>

              {/* Key features */}
              <SectionTitle icon="ShieldCheck" text="Key features" />
              <div className="grid gap-3 sm:grid-cols-2">
                {KEY_FEATURES.map((f) => (
                  <Card key={f.title} {...f} />
                ))}
              </div>

              {/* Standout capabilities */}
              <SectionTitle icon="Zap" text="Standout capabilities" />
              <div className="grid gap-3 sm:grid-cols-2">
                {STANDOUT.map((f) => (
                  <Card key={f.title} {...f} accent />
                ))}
              </div>

              {/* How it's different */}
              <SectionTitle icon="Scale" text="How it's different" />
              <div className="overflow-hidden rounded-2xl border border-white/10">
                <div className="grid grid-cols-[1.1fr_1.4fr_1.4fr] bg-white/[0.04] text-[11px] font-semibold uppercase tracking-wider text-white/45">
                  <span className="px-4 py-2.5">Dimension</span>
                  <span className="px-4 py-2.5 text-neon-cyan">AgentShield AI</span>
                  <span className="px-4 py-2.5">Typical agent scanners</span>
                </div>
                {DIFFERENTIATORS.map((row, i) => (
                  <div
                    key={row.label}
                    className={cn(
                      "grid grid-cols-[1.1fr_1.4fr_1.4fr] text-sm",
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

              {/* Principles */}
              <SectionTitle icon="Lock" text="Non-negotiable principles" />
              <div className="grid gap-2 sm:grid-cols-2">
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
                PASS is not certification. WARN is not authorization. AgentShield
                AI provides assurance and governance support only — the named
                owner and approver remain accountable for every action.
              </p>
            </div>

            {/* Footer actions */}
            <div className="flex flex-col gap-3 border-t border-white/10 px-6 py-4 sm:flex-row sm:items-center sm:px-8">
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
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function SectionTitle({ icon, text }: { icon: string; text: string }) {
  return (
    <h3 className="mb-3 mt-7 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-white/50">
      <Icon name={icon} className="h-4 w-4 text-neon-cyan" />
      {text}
    </h3>
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
        "rounded-2xl border p-4 transition-colors",
        accent
          ? "border-neon-violet/20 bg-gradient-to-br from-neon-blue/[0.06] to-neon-violet/[0.06] hover:border-neon-violet/40"
          : "border-white/10 bg-white/[0.02] hover:border-white/20"
      )}
    >
      <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan">
        <Icon name={icon} className="h-4 w-4" />
      </span>
      <h4 className="text-sm font-semibold text-white">{title}</h4>
      <p className="mt-1 text-[13px] leading-relaxed text-white/60">{body}</p>
    </div>
  );
}
