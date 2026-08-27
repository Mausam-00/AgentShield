import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { CTASection } from "@/components/sections/CTASection";
import { ExpandableCard } from "@/components/ui/ExpandableCard";
import { Icon } from "@/components/ui/Icon";
import { RevealGroup, RevealItem } from "@/components/ui/Reveal";
import { services } from "@/lib/site";

export const metadata: Metadata = {
  title: "Services",
  description:
    "Governance, adversarial assurance, Responsible AI, safe-plan engineering, monitoring and integration services for agentic systems.",
};

export default function ServicesPage() {
  return (
    <>
      <PageHero
        eyebrow="Services"
        title={
          <>
            Everything you need to{" "}
            <span className="text-gradient-neon">govern agents</span>
          </>
        }
        subtitle="From pre-execution interception to exportable evidence, our services wrap the entire lifecycle of an autonomous action. Click any card for more."
      />

      <section className="container-x py-20">
        <RevealGroup className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {services.map((s) => (
            <RevealItem key={s.title}>
              <ExpandableCard more={s.more}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan ring-1 ring-white/10">
                  <Icon name={s.icon} className="h-5 w-5" />
                </div>
                <h3 className="mt-5 font-display text-xl font-semibold text-white">
                  {s.title}
                </h3>
                <p className="mt-2.5 text-sm leading-relaxed text-white/60">
                  {s.body}
                </p>
                <ul className="mt-5 space-y-2.5 border-t border-white/10 pt-5">
                  {s.points.map((p) => (
                    <li
                      key={p}
                      className="flex items-center gap-2.5 text-sm text-white/70"
                    >
                      <Icon name="Check" className="h-4 w-4 shrink-0 text-neon-teal" />
                      {p}
                    </li>
                  ))}
                </ul>
              </ExpandableCard>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      <CTASection />
    </>
  );
}
