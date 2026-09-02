import Link from "next/link";
import { nav, site } from "@/lib/site";
import { Icon } from "@/components/ui/Icon";
import { ShieldMark } from "@/components/brand/ShieldMark";

export function Footer() {
  return (
    <footer className="relative mt-32 overflow-hidden border-t border-white/10">
      <div className="pointer-events-none absolute -top-40 left-1/2 h-80 w-[60rem] -translate-x-1/2 rounded-full bg-neon-blue/10 blur-[120px]" />
      <div className="container-x relative py-16">
        <div className="grid gap-12 lg:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5">
              <span className="h-10 w-10">
                <ShieldMark />
              </span>
              <span className="font-display text-lg font-semibold text-white">
                AgentShield <span className="text-gradient-neon">AI</span>
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/55">
              {site.tagline}. Predict, govern, approve, execute safely, and audit
              every autonomous action.
            </p>
            <div className="mt-6 flex gap-3">
              {["in", "X", "GH"].map((s) => (
                <span
                  key={s}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-xs font-semibold text-white/60 transition-colors hover:border-white/25 hover:text-white"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-white/40">
              Explore
            </h4>
            <ul className="mt-4 space-y-3">
              {nav
                .filter((n) => n.href !== "/")
                .map((n) => (
                  <li key={n.href}>
                    <Link
                      href={n.href}
                      className="text-sm text-white/65 transition-colors hover:text-white"
                    >
                      {n.label}
                    </Link>
                  </li>
                ))}
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-white/40">
              On this page
            </h4>
            <ul className="mt-4 space-y-3">
              {[
                { label: "Why AgentShield", href: "/#usp" },
                { label: "Efficiency dashboard", href: "/#dashboard" },
                { label: "Business value", href: "/#value" },
                { label: "Run the Engine", href: "/#demo" },
              ].map((c) => (
                <li key={c.href}>
                  <Link
                    href={c.href}
                    className="text-sm text-white/65 transition-colors hover:text-white"
                  >
                    {c.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-white/40">
              Principles
            </h4>
            <ul className="mt-4 space-y-3 text-sm text-white/65">
              <li>Fail closed by default</li>
              <li>Evidence over claims</li>
              <li>Judgement ≠ authority</li>
              <li>Humans accountable</li>
            </ul>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-start justify-between gap-4 border-t border-white/10 pt-8 text-sm text-white/45 sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} {site.name}. All rights reserved.</p>
          <p className="flex items-center gap-2">
            <Icon name="Lock" className="h-3.5 w-3.5" />
            Assurance & governance support — not certification or a guarantee of safety.
          </p>
        </div>
      </div>
    </footer>
  );
}
