import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { GatesShowcase } from "@/components/sections/GatesShowcase";
import { CTASection } from "@/components/sections/CTASection";
import { ExpandableCard } from "@/components/ui/ExpandableCard";
import { Icon } from "@/components/ui/Icon";
import { RevealGroup, RevealItem } from "@/components/ui/Reveal";
import { products } from "@/lib/site";

export const metadata: Metadata = {
  title: "Products",
  description:
    "The AgentShield control plane, red-team engine, Responsible AI module and evidence vault — the seven-gate architecture in product form.",
};

const accentRing: Record<string, string> = {
  blue: "from-neon-blue/25 to-neon-cyan/25 text-neon-cyan",
  magenta: "from-neon-magenta/25 to-neon-violet/25 text-neon-magenta",
  violet: "from-neon-violet/25 to-neon-blue/25 text-neon-violet",
  teal: "from-neon-teal/25 to-neon-cyan/25 text-neon-teal",
};

export default function ProductsPage() {
  return (
    <>
      <PageHero
        eyebrow="Products"
        title={
          <>
            The{" "}
            <span className="text-gradient-neon">seven-gate</span> control plane,
            modular
          </>
        }
        subtitle="Adopt the full runtime or start with a single module. Every product shares one principle — judgement is advisory, authority is deterministic. Click any card for more."
      />

      <section className="container-x py-20">
        <RevealGroup className="grid gap-5 md:grid-cols-2">
          {products.map((p) => (
            <RevealItem key={p.name}>
              <ExpandableCard more={p.more}>
                <div className="flex items-center justify-between">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ring-1 ring-white/10 ${accentRing[p.accent]}`}
                  >
                    <Icon name="ShieldCheck" className="h-5 w-5" />
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-wider text-white/55">
                    {p.tier}
                  </span>
                </div>
                <h3 className="mt-5 font-display text-2xl font-semibold text-white">
                  {p.name}
                </h3>
                <p className="mt-2.5 text-sm leading-relaxed text-white/60">
                  {p.body}
                </p>
                <div className="mt-5 flex flex-wrap gap-2 border-t border-white/10 pt-5">
                  {p.features.map((f) => (
                    <span
                      key={f}
                      className="rounded-full bg-white/[0.06] px-3 py-1 text-xs text-white/70"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </ExpandableCard>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      <GatesShowcase />

      <CTASection />
    </>
  );
}
