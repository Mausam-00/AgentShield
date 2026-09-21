"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { Reveal } from "@/components/ui/Reveal";
import { viewportOnce } from "@/lib/motion";
import { dashboard } from "@/lib/site";
import { cn } from "@/lib/utils";

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

function MetricBar({
  label,
  before,
  after,
  unit,
  change,
  detail,
}: {
  label: string;
  before: number;
  after: number;
  unit: string;
  change: string;
  detail: string;
}) {
  const [open, setOpen] = useState(false);
  const afterPct = Math.max(6, Math.round((after / before) * 100));

  return (
    <div className="instrument-panel rounded-2xl p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-medium text-white/70">{label}</div>
          <div className="mt-1 font-display text-2xl font-semibold text-white">
            {fmt(after)}
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
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-rose-500 to-orange-400"
              initial={{ width: "8%" }}
              whileInView={{ width: "100%" }}
              viewport={viewportOnce}
              transition={{ duration: 1.3, ease: [0.16, 1, 0.3, 1] }}
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
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-neon-teal to-neon-cyan"
              initial={{ width: "8%" }}
              whileInView={{ width: `${afterPct}%` }}
              viewport={viewportOnce}
              transition={{ duration: 1.3, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
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

      <div className="mt-16 grid gap-5 lg:grid-cols-[1.15fr_1fr]">
        {/* Left: metric bars + preserved */}
        <div className="grid gap-5">
          <div className="grid gap-5 sm:grid-cols-2">
            {dashboard.metrics.map((m) => (
              <MetricBar key={m.label} {...m} />
            ))}
          </div>

          <Reveal>
            <div className="rounded-2xl glass-strong p-6">
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
