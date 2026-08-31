"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { nav, site } from "@/lib/site";
import { Icon } from "@/components/ui/Icon";
import { GradientButton } from "@/components/ui/GradientButton";

export function MobileMenu({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[80] lg:hidden"
        >
          <div
            className="absolute inset-0 bg-ink-950/80 backdrop-blur-xl"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}
            className="absolute right-0 top-0 flex h-full w-[86%] max-w-sm flex-col glass-strong p-6"
          >
            <div className="flex items-center justify-between">
              <span className="font-display text-lg font-semibold text-white">
                Menu
              </span>
              <button
                aria-label="Close menu"
                onClick={onClose}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white"
              >
                <Icon name="X" className="h-5 w-5" />
              </button>
            </div>

            <nav className="mt-8 flex flex-col gap-1 overflow-y-auto">
              {nav.map((item, i) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.06 }}
                >
                  <Link
                    href={item.href}
                    target={item.external ? "_blank" : undefined}
                    rel={item.external ? "noopener noreferrer" : undefined}
                    onClick={onClose}
                    className="block rounded-xl px-4 py-3 text-lg font-semibold text-white/85 transition-colors hover:bg-white/5"
                  >
                    {item.label}
                  </Link>
                  {item.children && (
                    <div className="ml-3 border-l border-white/10 pl-3">
                      {item.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          onClick={onClose}
                          className="block rounded-lg px-3 py-2 text-sm text-white/55 transition-colors hover:text-white"
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </nav>

            <div className="mt-auto pt-6">
              <GradientButton href={site.repo} target="_blank" rel="noopener noreferrer" className="w-full">
                GitHub
              </GradientButton>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
