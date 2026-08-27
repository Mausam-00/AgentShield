import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { CTASection } from "@/components/sections/CTASection";
import { ExpandableCard } from "@/components/ui/ExpandableCard";
import { RevealGroup, RevealItem } from "@/components/ui/Reveal";
import { solutions } from "@/lib/site";

export const metadata: Metadata = {
  title: "Solutions",
  description:
    "AgentShield solutions for financial services, healthcare, critical infrastructure and technology — measurable outcomes by industry.",
};

export default function SolutionsPage() {
  return (
    <>
      <PageHero
        eyebrow="Solutions"
        title={
          <>
            Outcomes for{" "}
            <span className="text-gradient-neon">regulated, high-stakes</span>{" "}
            industries
          </>
        }
        subtitle="Wherever an agent can take a costly, irreversible action, AgentShield turns risk into a measurable, auditable control. Click any card for more."
      />

      <section className="container-x py-20">
        <RevealGroup className="grid gap-5 md:grid-cols-2">
          {solutions.map((s) => (
            <RevealItem key={s.title}>
              <ExpandableCard more={s.more} glowClass="bg-neon-teal/15">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="text-xs font-medium uppercase tracking-[0.18em] text-neon-cyan">
                      {s.sector}
                    </span>
                    <h3 className="mt-3 font-display text-2xl font-semibold text-white">
                      {s.title}
                    </h3>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="font-display text-4xl font-semibold text-gradient-neon">
                      {s.metric}
                    </div>
                    <div className="mt-1 text-[11px] uppercase tracking-wider text-white/45">
                      {s.metricLabel}
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-relaxed text-white/60">
                  {s.body}
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
