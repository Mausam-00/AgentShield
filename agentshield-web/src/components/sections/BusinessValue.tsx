"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { RevealGroup, RevealItem } from "@/components/ui/Reveal";
import { StatCounter } from "@/components/ui/StatCounter";
import { businessValue } from "@/lib/site";
import { cn } from "@/lib/utils";

function parseMetric(m: string) {
  const neg = m.trim().startsWith("−") || m.trim().startsWith("-");
  const pct = m.includes("%");
  const num = parseFloat(m.replace(/[^0-9.]/g, "")) || 0;
  const decimals = m.includes(".") ? 1 : 0;
  return { neg, pct, num, decimals };
}

export function BusinessValue() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="value" className="container-x scroll-mt-28 py-24 sm:py-32">
      <SectionHeading
        eyebrow="Business value"
        title={
          <>
            Real outcomes for{" "}
            <span className="text-gradient-neon">security &amp; finance leaders</span>
          </>
        }
        subtitle="Lower cost, provable governance and reduced risk — with no safety trade-off. Click any card for the detail behind the number."
      />

      <RevealGroup className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {businessValue.map((b, i) => {
          const isOpen = open === i;
          const { neg, pct, num, decimals } = parseMetric(b.metric);
          return (
            <RevealItem key={b.title}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
                className={cn(
                  "group flex h-full w-full flex-col rounded-2xl glass p-6 text-left shadow-card transition-all duration-300",
                  isOpen ? "ring-1 ring-neon-blue/40" : "hover:-translate-y-1.5"
                )}
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan ring-1 ring-white/10">
                  <Icon name={b.icon} className="h-5 w-5" />
                </span>

                <div className="mt-5 font-display text-4xl font-semibold text-white">
                  {neg && "−"}
                  <StatCounter value={num} decimals={decimals} suffix={pct ? "%" : ""} />
                </div>
                <h3 className="mt-2 text-sm font-semibold text-white">{b.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-white/55">
                  {b.summary}
                </p>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.32 }}
                      className="overflow-hidden"
                    >
                      <p className="mt-4 border-t border-white/10 pt-3 text-sm leading-relaxed text-white/75">
                        {b.detail}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <span className="mt-auto pt-4 inline-flex items-center gap-1 text-xs font-medium text-neon-cyan/80">
                  <Icon name={isOpen ? "Minus" : "Plus"} className="h-3.5 w-3.5" />
                  {isOpen ? "Show less" : "Click for more info"}
                </span>
              </button>
            </RevealItem>
          );
        })}
      </RevealGroup>
    </section>
  );
}
