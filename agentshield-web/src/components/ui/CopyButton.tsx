"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Icon } from "./Icon";
import { cn } from "@/lib/utils";

/**
 * Copy-to-clipboard control with a check-mark morph. Renders the text as a
 * monospace chip with a trailing copy/confirm icon.
 */
export function CopyButton({
  value,
  label,
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable — no-op */
    }
  }

  return (
    <button
      onClick={copy}
      aria-label={`Copy ${label ?? value}`}
      className={cn(
        "group inline-flex items-center gap-3 rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 font-mono text-sm text-white/75 transition-colors hover:border-white/25 hover:bg-white/[0.06]",
        className
      )}
    >
      <span className="text-white/45 select-none">$</span>
      <span className="truncate">{label ?? value}</span>
      <span className="relative ml-1 grid h-4 w-4 place-items-center">
        <AnimatePresence mode="wait" initial={false}>
          {copied ? (
            <motion.span
              key="check"
              initial={{ scale: 0.4, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.4, opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="absolute text-neon-cyan"
            >
              <Icon name="Check" className="h-4 w-4" />
            </motion.span>
          ) : (
            <motion.span
              key="copy"
              initial={{ scale: 0.4, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.4, opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="absolute text-white/50 group-hover:text-white/80"
            >
              <Icon name="Copy" className="h-4 w-4" />
            </motion.span>
          )}
        </AnimatePresence>
      </span>
    </button>
  );
}
