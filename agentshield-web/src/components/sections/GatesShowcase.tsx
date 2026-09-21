"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Icon } from "@/components/ui/Icon";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { gates } from "@/lib/site";
import { cn } from "@/lib/utils";

export function GatesShowcase() {
  const [active, setActive] = useState(4); // G4 highlighted by default
  const reduce = useReducedMotion();
  const gate = gates[active];

  return (
    <section className="container-x section-chapter py-24 sm:py-32">
      <SectionHeading
        eyebrow="How it works"
        title={
          <>
            The <span className="text-gradient-neon">seven-gate</span> governance
            workflow
          </>
        }
        subtitle="Every action flows through the gates in order. Only gate four — deterministic policy — can authorize."
      />

      <div className="gate-workspace mt-14 rounded-2xl p-5 sm:p-8">
        <ol className="gate-pathway">
          {gates.map((g, i) => {
            const isG4 = g.id === "G4";
            const selected = i === active;
            return (
              <li key={g.id} className="gate-step" data-selected={selected} data-policy={isG4}>
                <button
                  id={`gate-${g.id}`}
                  aria-pressed={selected}
                  aria-controls="gate-detail"
                  onFocus={() => setActive(i)}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => setActive(i)}
                  className="gate-button group relative w-full rounded-xl text-left"
                >
                  <span className="gate-node relative z-10 font-mono">
                    {isG4 ? <Icon name="Lock" className="h-4 w-4" /> : <span className="gate-node-dot" />}
                  </span>
                  <span className="relative z-10 block">
                    <span
                      className={cn(
                        "font-display text-lg font-semibold",
                        isG4 ? "text-neon-cyan" : "text-white"
                      )}
                    >
                      {g.id}
                    </span>
                    <span className="mt-1 block text-xs leading-relaxed text-white/65">
                      {g.name}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ol>

        <div id="gate-detail" role="region" aria-labelledby={`gate-${gate.id}`} className="gate-detail relative mt-8 min-h-[240px] overflow-hidden rounded-xl p-6 sm:p-8">
          <div aria-hidden className="circuit-grid pointer-events-none absolute inset-0 opacity-40" />
          <span aria-hidden className="pointer-events-none absolute -bottom-8 right-4 font-mono text-[180px] font-semibold leading-none text-white/[0.025]">{gate.id}</span>
          <AnimatePresence mode="wait">
            <motion.div
              key={gate.id}
              initial={{ opacity: 0, y: reduce ? 0 : 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reduce ? 0 : 0.2 }}
              className="relative max-w-3xl"
            >
              <div className="flex items-baseline gap-3">
                <span className="font-display text-5xl font-semibold text-gradient-neon">
                  {gate.id}
                </span>
                <span className="text-xl font-semibold text-white">
                  {gate.name}
                </span>
              </div>
              <p className="mt-4 text-base leading-relaxed text-white/65">
                {gate.body}
              </p>
              {gate.id === "G4" && (
                <p className="mt-4 inline-flex rounded-full border border-neon-cyan/30 bg-neon-cyan/10 px-3 py-1 text-xs font-medium text-neon-cyan">
                  The only gate that authorizes — fails closed
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
