import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { StatsBand } from "@/components/sections/StatsBand";
import { CTASection } from "@/components/sections/CTASection";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ExpandableCard } from "@/components/ui/ExpandableCard";
import { RevealGroup, RevealItem, Reveal } from "@/components/ui/Reveal";
import { values } from "@/lib/site";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "AgentShield AI exists to keep autonomous agents inside a demonstrable safety envelope — separating judgement from authority.",
};

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About Us"
        title={
          <>
            We govern the{" "}
            <span className="text-gradient-neon">agentic era</span>
          </>
        }
        subtitle="AgentShield AI was founded on one conviction: an AI recommendation must never be authorization. We build the deterministic control plane that keeps autonomous agents safe, accountable and auditable."
      />

      <section className="container-x py-20">
        <div className="grid gap-12 lg:grid-cols-2">
          <Reveal>
            <div>
              <h2 className="font-display text-3xl font-semibold text-white">
                Our mission
              </h2>
              <p className="mt-5 text-lg leading-relaxed text-white/65">
                Autonomous agents now act faster than governance can react. They
                call real tools, they can be hijacked, and too often a model&apos;s
                suggestion is treated as permission. We close that gap.
              </p>
              <p className="mt-4 text-lg leading-relaxed text-white/65">
                AgentShield intercepts every action before it executes, predicts
                its impact, and lets only deterministic, versioned policy decide —
                preserving evidence for every outcome, including denials.
              </p>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="relative overflow-hidden rounded-2xl glass p-8">
              <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-neon-blue/20 blur-3xl" />
              <blockquote className="relative font-display text-2xl font-medium leading-snug text-white">
                &ldquo;Judgement is advisory. Authority is deterministic. Humans
                stay accountable.&rdquo;
              </blockquote>
              <p className="relative mt-5 text-sm text-white/55">
                The principle behind every gate, control and report we ship.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <StatsBand />

      <section className="container-x py-20">
        <SectionHeading
          eyebrow="Principles"
          title="What we refuse to compromise on"
          subtitle="Four non-negotiables that shape every gate, control and report. Click any card for more."
        />
        <RevealGroup className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {values.map((v) => (
            <RevealItem key={v.title}>
              <ExpandableCard more={v.more}>
                <h3 className="font-display text-lg font-semibold text-white">
                  {v.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-white/60">
                  {v.body}
                </p>
              </ExpandableCard>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      <CTASection />
    </>
  );
}
