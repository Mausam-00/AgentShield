import { Reveal } from "@/components/ui/Reveal";
import { Icon } from "@/components/ui/Icon";
import { SectionHeading } from "@/components/ui/SectionHeading";

const advisory = [
  "Extracts facts & describes uncertainty",
  "Predicts operational impact",
  "Recommends constraints & safe plans",
  "Posture: PASS / WARN / BLOCK",
];
const control = [
  "Versioned policy owns every decision",
  "One verdict: allow, transform, approve, escalate, deny",
  "Approval bound to hash, version & expiry",
  "Fails closed on missing evidence",
];

export function AssuranceSplit() {
  return (
    <section className="container-x py-24 sm:py-32">
      <SectionHeading
        eyebrow="Separation of powers"
        title={
          <>
            Judgement is advisory.{" "}
            <span className="text-gradient-neon">Authority is deterministic.</span>
          </>
        }
        subtitle="An assurance PASS is never a certification, and a model never grants access. This separation is the core of the platform."
      />

      <div className="trust-lanes relative mt-16 grid gap-8 lg:grid-cols-2">
        <Reveal>
          <div className="trust-lane trust-advisory h-full rounded-2xl p-8">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-neon-blue/15 text-neon-blue">
                <Icon name="Sparkles" className="h-5 w-5" />
              </span>
              <h3 className="font-display text-xl font-semibold text-white">
                AI analysis — advisory
              </h3>
            </div>
            <ul className="mt-6 space-y-4">
              {advisory.map((c) => (
                <li key={c} className="flex items-start gap-3 text-white/70">
                  <Icon name="Check" className="mt-0.5 h-5 w-5 shrink-0 text-neon-blue" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="trust-lane trust-authority h-full rounded-2xl p-8">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-neon-teal/15 text-neon-teal">
                <Icon name="Lock" className="h-5 w-5" />
              </span>
              <h3 className="font-display text-xl font-semibold text-white">
                Deterministic control — authority
              </h3>
            </div>
            <ul className="mt-6 space-y-4">
              {control.map((c) => (
                <li key={c} className="flex items-start gap-3 text-white/70">
                  <Icon name="Check" className="mt-0.5 h-5 w-5 shrink-0 text-neon-teal" />
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
