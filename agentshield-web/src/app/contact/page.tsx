import type { Metadata } from "next";
import { PageHero } from "@/components/sections/PageHero";
import { ContactForm } from "@/components/sections/ContactForm";
import { Reveal } from "@/components/ui/Reveal";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact Us",
  description:
    "Talk to the AgentShield AI team about governing your autonomous agents. Request a briefing or a technical deep-dive.",
};

const details = [
  { label: "Email", value: site.email, href: `mailto:${site.email}` },
  { label: "Location", value: site.location },
];

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Contact Us"
        title={
          <>
            Let&apos;s make your agents{" "}
            <span className="text-gradient-neon">provably safe</span>
          </>
        }
        subtitle="Tell us about the autonomous actions you need to govern. We&apos;ll show you the seven gates in action on your own use case."
      />

      <section className="container-x pb-24">
        <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr]">
          <Reveal>
            <div className="space-y-8">
              <div>
                <h2 className="font-display text-2xl font-semibold text-white">
                  Start a conversation
                </h2>
                <p className="mt-3 max-w-md text-sm leading-relaxed text-white/60">
                  Whether you are piloting your first agent or governing a fleet,
                  we&apos;ll tailor a briefing to your risk profile and stack.
                </p>
              </div>

              <div className="space-y-4">
                {details.map((d) => (
                  <div
                    key={d.label}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
                  >
                    <div className="text-[11px] uppercase tracking-wider text-white/45">
                      {d.label}
                    </div>
                    {d.href ? (
                      <a
                        href={d.href}
                        className="mt-1 block text-lg font-medium text-white transition-colors hover:text-neon-cyan"
                      >
                        {d.value}
                      </a>
                    ) : (
                      <div className="mt-1 text-lg font-medium text-white">
                        {d.value}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <ContactForm />
          </Reveal>
        </div>
      </section>
    </>
  );
}
