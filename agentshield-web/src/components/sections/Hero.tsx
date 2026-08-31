"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { Hero3D } from "@/components/three/Hero3D";
import { AuroraBackground } from "@/components/background/AuroraBackground";
import { ParticleField } from "@/components/background/ParticleField";
import { GradientButton } from "@/components/ui/GradientButton";
import { Pill } from "@/components/ui/Pill";
import { StatCounter } from "@/components/ui/StatCounter";
import { heroStats, site } from "@/lib/site";

const line1 = ["Govern", "every"];
const line2 = ["autonomous", "action."];

export function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const yText = useTransform(scrollYProgress, [0, 1], [0, 140]);
  const yScene = useTransform(scrollYProgress, [0, 1], [0, 220]);
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <section
      ref={ref}
      className="relative flex min-h-[100svh] items-center overflow-hidden pt-28"
    >
      <AuroraBackground />
      <motion.div style={{ y: yScene }} className="absolute inset-0">
        <Hero3D />
      </motion.div>
      <ParticleField className="opacity-70" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-ink-950 to-transparent" />

      <motion.div
        style={{ y: yText, opacity }}
        className="container-x relative z-10"
      >
        <div className="max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <Pill>The Security Control Plane for the Agentic Enterprise</Pill>
          </motion.div>

          <h1 className="mt-7 font-display text-5xl font-semibold leading-[0.98] tracking-tight text-white sm:text-7xl lg:text-8xl">
            <span className="block overflow-hidden">
              {line1.map((w, i) => (
                <motion.span
                  key={w}
                  className="mr-4 inline-block"
                  initial={{ y: "110%" }}
                  animate={{ y: 0 }}
                  transition={{
                    duration: 0.9,
                    delay: 0.15 + i * 0.08,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                >
                  {w}
                </motion.span>
              ))}
            </span>
            <span className="block overflow-hidden">
              {line2.map((w, i) => (
                <motion.span
                  key={w}
                  className="mr-4 inline-block text-gradient-neon"
                  initial={{ y: "110%" }}
                  animate={{ y: 0 }}
                  transition={{
                    duration: 0.9,
                    delay: 0.32 + i * 0.08,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                >
                  {w}
                </motion.span>
              ))}
            </span>
          </h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.55 }}
            className="mt-7 max-w-xl text-lg leading-relaxed text-white/65"
          >
            AgentShield AI intercepts every agent action before it executes,
            predicts its impact, and lets only deterministic, versioned policy
            decide. AI advises — never authorizes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.68 }}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <GradientButton href={site.repo} target="_blank" rel="noopener noreferrer">
              Get it on GitHub
            </GradientButton>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.85 }}
            className="mt-14 grid max-w-2xl grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-4"
          >
            {heroStats.map((s) => (
              <div key={s.label}>
                <div className="font-display text-3xl font-semibold text-white sm:text-4xl">
                  <StatCounter
                    value={s.value}
                    suffix={s.suffix}
                    decimals={(s as { decimals?: number }).decimals ?? 0}
                  />
                </div>
                <div className="mt-1 text-xs uppercase tracking-[0.14em] text-white/45">
                  {s.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 z-10 hidden -translate-x-1/2 sm:block"
      >
        <div className="flex h-10 w-6 items-start justify-center rounded-full border border-white/20 p-1.5">
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 1.6, repeat: Infinity }}
            className="h-2 w-1 rounded-full bg-neon-cyan"
          />
        </div>
      </motion.div>
    </section>
  );
}
