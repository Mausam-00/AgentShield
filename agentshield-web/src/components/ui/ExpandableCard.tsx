"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

/**
 * Glass card with a "click for more info" reveal — the shared interaction
 * used across the home and inner pages. Always-visible content is passed as
 * children; `more` is revealed on toggle.
 */
export function ExpandableCard({
  children,
  more,
  className,
  glowClass = "bg-neon-violet/15",
}: {
  children: ReactNode;
  more: ReactNode;
  className?: string;
  glowClass?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      aria-expanded={open}
      className={cn(
        "group relative flex h-full w-full flex-col overflow-hidden rounded-2xl glass p-6 text-left shadow-card transition-all duration-300",
        open ? "ring-1 ring-neon-blue/40" : "hover:-translate-y-1.5",
        className
      )}
    >
      <div
        className={cn(
          "pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full blur-3xl transition-opacity duration-300 group-hover:opacity-100",
          glowClass
        )}
      />
      <div className="relative flex flex-1 flex-col">{children}</div>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="relative overflow-hidden"
          >
            <p className="mt-4 border-t border-white/10 pt-4 text-sm leading-relaxed text-white/75">
              {more}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      <span className="relative mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-neon-cyan/80">
        <Icon
          name={open ? "Minus" : "Plus"}
          className="h-3.5 w-3.5"
        />
        {open ? "Show less" : "Click for more info"}
      </span>
    </button>
  );
}
