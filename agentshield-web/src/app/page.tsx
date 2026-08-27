import { Hero } from "@/components/sections/Hero";
import { USPSection } from "@/components/sections/USPSection";
import { GatesShowcase } from "@/components/sections/GatesShowcase";
import { Dashboard } from "@/components/sections/Dashboard";
import { BusinessValue } from "@/components/sections/BusinessValue";
import { AssessConsole } from "@/components/sections/AssessConsole";
import { AssuranceSplit } from "@/components/sections/AssuranceSplit";
import { StatsBand } from "@/components/sections/StatsBand";
import { CTASection } from "@/components/sections/CTASection";

export default function HomePage() {
  return (
    <>
      <Hero />
      <USPSection />
      <GatesShowcase />
      <Dashboard />
      <BusinessValue />
      <AssessConsole />
      <AssuranceSplit />
      <StatsBand />
      <CTASection />
    </>
  );
}
