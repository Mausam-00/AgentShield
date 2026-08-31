import { Reveal } from "@/components/ui/Reveal";
import { GradientButton } from "@/components/ui/GradientButton";
import { site } from "@/lib/site";

export function CTASection() {
  return (
    <section className="container-x py-24">
      <Reveal>
        <div className="relative overflow-hidden rounded-[2rem] border border-white/10 p-10 text-center sm:p-16">
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(79,124,255,0.22),rgba(168,85,247,0.22))]" />
          <div className="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-neon-blue/30 blur-[110px]" />
          <div className="pointer-events-none absolute -right-24 bottom-0 h-72 w-72 rounded-full bg-neon-violet/30 blur-[110px]" />
          <div className="relative">
            <h2 className="mx-auto max-w-3xl font-display text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">
              Put a control plane in front of every agent.
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-lg text-white/70">
              See AgentShield intercept, govern and audit a live agent workflow in
              a 30-minute technical walkthrough.
            </p>
            <div className="mt-9 flex flex-wrap justify-center gap-4">
              <GradientButton href="/contact">Book a demo</GradientButton>
              <GradientButton href={site.repo} target="_blank" rel="noopener noreferrer" variant="ghost" icon={false}>
                Get it on GitHub
              </GradientButton>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
