import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { ShowcaseConsole, type Data } from "@/components/sections/ShowcaseConsole";
import { CTASection } from "@/components/sections/CTASection";
import showcaseData from "@/lib/showcase-data.json";

export const metadata: Metadata = {
  title: "Before / After Remediation",
  description:
    "Watch AgentShield harden a deliberately-weak AI agent live: assurance score, findings, red-team attack-success-rate, injection resistance and the runtime decision — measured before and after remediation.",
};

export default function ShowcasePage() {
  return (
    <>
      <PageHero
        eyebrow="Live demo · before → after"
        title={
          <>
            One weak agent,{" "}
            <span className="text-gradient-neon">provably hardened</span>
          </>
        }
        subtitle="A deliberately-insecure infrastructure agent runs through AgentShield, gets remediated, and is re-measured on the same evidence. Findings fall, attack-success-rate collapses, and its destructive action stops being allowed — replay it as many times as you like."
      />
      <ShowcaseConsole initial={showcaseData as unknown as Data} />
      <CTASection />
    </>
  );
}
