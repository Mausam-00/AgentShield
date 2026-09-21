"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Icon } from "@/components/ui/Icon";
import { RevealGroup, RevealItem } from "@/components/ui/Reveal";
import { usps } from "@/lib/site";
import { cn } from "@/lib/utils";

export function USPSection() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="usp" className="container-x py-24 sm:py-32">
      <SectionHeading
        eyebrow="Why AgentShield"
        title={
          <>
            What makes it{" "}
            <span className="text-gradient-neon">fundamentally different</span>
          </>
        }
        subtitle="Six differentiators that separate a demonstrable safety envelope from a best-effort guardrail. Click any card for more."
      />

      <RevealGroup className="usp-grid mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {usps.map((u, i) => {
          const isOpen = open === i;
          return (
            <RevealItem key={u.title} className={i === 0 || i === 5 ? "lg:col-span-2" : ""}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
                className={cn(
                  "feature-panel group relative flex h-full w-full flex-col overflow-hidden rounded-2xl p-7 text-left transition-all duration-300",
                  isOpen ? "ring-1 ring-neon-blue/40" : "hover:-translate-y-1.5"
                )}
              >
                <div aria-hidden className="feature-circuit" />
                <div className="relative flex items-start justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan ring-1 ring-white/10">
                    <Icon name={u.icon} className="h-5 w-5" />
                  </span>
                  <span
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full border border-white/12 text-white/60 transition-colors",
                      isOpen ? "bg-neon-blue/20 text-white" : "group-hover:text-white"
                    )}
                  >
                    <Icon name={isOpen ? "Minus" : "Plus"} className="h-4 w-4" />
                  </span>
                </div>

                <h3 className="relative mt-5 font-display text-lg font-semibold text-white">
                  {u.title}
                </h3>
                <p className="relative mt-2 text-sm leading-relaxed text-white/60">
                  {u.summary}
                </p>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                      className="relative overflow-hidden"
                    >
                      <p className="mt-4 border-t border-white/10 pt-4 text-sm leading-relaxed text-white/75">
                        {u.detail}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <span className="relative mt-4 inline-flex items-center gap-1 text-xs font-medium text-neon-cyan/80">
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
