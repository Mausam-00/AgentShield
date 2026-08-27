"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { nav } from "@/lib/site";
import { cn } from "@/lib/utils";
import { GradientButton } from "@/components/ui/GradientButton";
import { Icon } from "@/components/ui/Icon";
import { MobileMenu } from "./MobileMenu";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setMobileOpen(false), [pathname]);

  return (
    <>
      <header
        className={cn(
          "fixed inset-x-0 top-0 z-50 transition-all duration-500",
          scrolled ? "py-2" : "py-4"
        )}
      >
        <div className="container-x">
          <div
            className={cn(
              "flex items-center justify-between rounded-2xl px-4 py-2.5 transition-all duration-500",
              scrolled ? "glass-strong shadow-card" : "bg-transparent"
            )}
            onMouseLeave={() => setActive(null)}
          >
            <Link href="/" className="flex items-center gap-2.5">
              <Image
                src="/logo.png"
                alt="AgentShield AI"
                width={44}
                height={44}
                className="h-10 w-10 object-contain"
                priority
              />
              <span className="hidden font-display text-lg font-semibold tracking-tight text-white sm:block">
                AgentShield <span className="text-gradient-neon">AI</span>
              </span>
            </Link>

            <nav className="hidden items-center gap-1 lg:flex">
              {nav.map((item) => (
                <div
                  key={item.label}
                  className="relative"
                  onMouseEnter={() => setActive(item.children ? item.label : null)}
                >
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1 rounded-full px-4 py-2 text-sm font-medium transition-colors",
                      pathname === item.href
                        ? "text-white"
                        : "text-white/65 hover:text-white"
                    )}
                  >
                    {item.label}
                    {item.children && (
                      <svg
                        className={cn(
                          "h-3.5 w-3.5 transition-transform",
                          active === item.label ? "rotate-180" : ""
                        )}
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="m6 9 6 6 6-6" />
                      </svg>
                    )}
                  </Link>

                  <AnimatePresence>
                    {item.children && active === item.label && (
                      <motion.div
                        initial={{ opacity: 0, y: 12, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.98 }}
                        transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                        className="absolute left-1/2 top-full w-[520px] -translate-x-1/2 pt-4"
                      >
                        <div className="glass-strong grid grid-cols-1 gap-1 rounded-2xl p-3 shadow-card">
                          {item.children.map((child) => (
                            <Link
                              key={child.href}
                              href={child.href}
                              className="group flex items-start gap-3 rounded-xl p-3 transition-colors hover:bg-white/5"
                            >
                              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-neon-blue/25 to-neon-violet/25 text-neon-cyan">
                                <Icon name="ShieldCheck" className="h-4 w-4" />
                              </span>
                              <span>
                                <span className="flex items-center gap-1 text-sm font-semibold text-white">
                                  {child.label}
                                  <Icon
                                    name="ArrowUpRight"
                                    className="h-3.5 w-3.5 -translate-x-1 opacity-0 transition-all group-hover:translate-x-0 group-hover:opacity-100"
                                  />
                                </span>
                                <span className="mt-0.5 block text-xs leading-relaxed text-white/55">
                                  {child.desc}
                                </span>
                              </span>
                            </Link>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </nav>

            <div className="flex items-center gap-3">
              <div className="hidden lg:block">
                <GradientButton href="/contact">Book a demo</GradientButton>
              </div>
              <button
                aria-label="Open menu"
                onClick={() => setMobileOpen(true)}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white lg:hidden"
              >
                <Icon name="Menu" className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <MobileMenu open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </>
  );
}
