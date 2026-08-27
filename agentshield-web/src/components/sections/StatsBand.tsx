import { StatCounter } from "@/components/ui/StatCounter";
import { Reveal } from "@/components/ui/Reveal";
import { bandStats } from "@/lib/site";

export function StatsBand() {
  return (
    <section className="container-x py-12">
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl glass-strong p-10 sm:p-14">
          <div className="pointer-events-none absolute inset-0 bg-radial-hero opacity-70" />
          <div className="relative grid grid-cols-2 gap-8 lg:grid-cols-4">
            {bandStats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="font-display text-4xl font-semibold text-white sm:text-5xl">
                  <StatCounter value={s.value} suffix={s.suffix} />
                </div>
                <div className="mt-2 text-xs uppercase tracking-[0.16em] text-white/50">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
