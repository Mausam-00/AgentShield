"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { gates } from "@/lib/site";
import { cn } from "@/lib/utils";

export function GatesShowcase() {
  const [active, setActive] = useState(4); // G4 highlighted by default
  const gate = gates[active];

  return (
    <section className="container-x py-24 sm:py-32">
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

      <div className="mt-16 grid gap-8 lg:grid-cols-[1.1fr_1fr]">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {gates.map((g, i) => {
            const isG4 = g.id === "G4";
            const selected = i === active;
            return (
              <button
                key={g.id}
                onMouseEnter={() => setActive(i)}
                onClick={() => setActive(i)}
                className={cn(
                  "group relative overflow-hidden rounded-xl border p-4 text-left transition-all duration-300",
                  selected
                    ? "border-transparent"
                    : "border-white/10 bg-white/[0.03] hover:border-white/20"
                )}
              >
                {selected && (
                  <motion.span
                    layoutId="gate-active"
                    className="absolute inset-0 bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 ring-1 ring-white/15"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <span className="relative z-10">
                  <span
                    className={cn(
                      "font-display text-lg font-semibold",
                      isG4 ? "text-neon-cyan" : "text-white"
                    )}
                  >
                    {g.id}
                  </span>
                  <span className="mt-1 block text-xs leading-tight text-white/60">
                    {g.name}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        <div className="relative overflow-hidden rounded-2xl glass p-8">
          <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-neon-violet/20 blur-3xl" />
          <AnimatePresence mode="wait">
            <motion.div
              key={gate.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
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
