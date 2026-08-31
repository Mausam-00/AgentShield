"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

// The seven-gate pipeline, narrated as it "runs". These are cosmetic stage
// labels cycled while the real engine works server-side (a single request with
// no progress stream), so the window feels alive instead of showing a spinner.
const STAGES = [
  "Intercepting the proposed action",
  "Auditing assurance controls",
  "Resolving identity & trust context",
  "Mapping BlastRadius — capability & impact",
  "Applying ChangeShield — deterministic policy",
  "Running Gate R red-team probes",
  "Reading Responsible AI posture",
  "Constraining the safe plan",
  "Validating outcome & sealing evidence",
];

export function AssessProcessing() {
  const [i, setI] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % STAGES.length), 900);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex h-[300px] flex-col items-center justify-center gap-6 overflow-hidden rounded-xl border border-white/10 bg-white/[0.015] px-6">
      {/* Radar / shield core */}
      <div className="relative grid h-28 w-28 place-items-center">
        {/* Rotating conic "radar" sweep, masked into a thin ring. */}
        <motion.span
          aria-hidden
          className="absolute inset-0 rounded-full"
          style={{
            background:
              "conic-gradient(from 0deg, rgba(56,225,255,0) 210deg, rgba(56,225,255,0.55) 320deg, rgba(168,85,247,0.85) 360deg)",
            WebkitMask:
              "radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 3px))",
            mask: "radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 3px))",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1.6, ease: "linear", repeat: Infinity }}
        />

        {/* Expanding pulse rings. */}
        {[0, 1].map((r) => (
          <motion.span
            key={r}
            aria-hidden
            className="absolute inset-0 rounded-full border border-neon-cyan/30"
            initial={{ scale: 0.65, opacity: 0.5 }}
            animate={{ scale: 1.3, opacity: 0 }}
            transition={{ duration: 1.8, repeat: Infinity, delay: r * 0.9, ease: "easeOut" }}
          />
        ))}

        {/* Static inner guide ring. */}
        <span className="absolute inset-3 rounded-full border border-white/10" />

        {/* Breathing shield. */}
        <motion.span
          className="relative grid h-12 w-12 place-items-center rounded-full bg-[linear-gradient(135deg,#4f7cff,#a855f7)] shadow-glow"
          animate={{ scale: [1, 1.09, 1] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        >
          <Icon name="ShieldCheck" className="h-6 w-6 text-white" />
        </motion.span>
      </div>

      {/* Cycling stage label. */}
      <div className="flex h-5 items-center overflow-hidden text-center">
        <motion.span
          key={i}
          initial={{ y: 14, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="text-sm font-medium text-white/85"
        >
          {STAGES[i]}
        </motion.span>
      </div>

      {/* Stepper dots — the active stage stretches, passed stages stay lit. */}
      <div className="flex items-center gap-1.5">
        {STAGES.map((_, idx) => (
          <span
            key={idx}
            className={cn(
              "h-1.5 rounded-full transition-all duration-300",
              idx === i ? "w-5 bg-neon-cyan" : idx < i ? "w-1.5 bg-neon-cyan/50" : "w-1.5 bg-white/15"
            )}
          />
        ))}
      </div>

      {/* Indeterminate shimmer bar. */}
      <div className="relative h-1 w-48 overflow-hidden rounded-full bg-white/[0.08]">
        <motion.span
          aria-hidden
          className="absolute inset-y-0 w-1/3 rounded-full bg-[linear-gradient(90deg,transparent,#38e1ff,#a855f7,transparent)]"
          animate={{ x: ["-70%", "230%"] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    </div>
  );
}
