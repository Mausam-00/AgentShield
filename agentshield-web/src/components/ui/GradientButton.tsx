"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Icon } from "./Icon";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  href?: string;
  variant?: "primary" | "ghost";
  className?: string;
  icon?: boolean;
  onClick?: () => void;
  target?: string;
  rel?: string;
};

export function GradientButton({
  children,
  href,
  variant = "primary",
  className,
  icon = true,
  onClick,
  target,
  rel,
}: Props) {
  const base =
    "group relative inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-semibold tracking-tight transition-all duration-300";

  const styles =
    variant === "primary"
      ? "text-white shadow-glow hover:shadow-glow-violet"
      : "text-white/85 border border-white/15 bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/25";

  const inner = (
    <motion.span
      whileTap={{ scale: 0.97 }}
      className={cn(base, styles, className)}
    >
      {variant === "primary" && (
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-[linear-gradient(110deg,#4f7cff,#a855f7_55%,#38e1ff)] opacity-100"
        />
      )}
      {variant === "primary" && (
        <span
          aria-hidden
          className="absolute inset-0 overflow-hidden rounded-full"
        >
          <span className="btn-shimmer absolute inset-0 -translate-x-full animate-shimmer" />
        </span>
      )}
      <span className="relative z-10 flex items-center gap-2">
        {children}
        {icon && (
          <Icon
            name="ArrowRight"
            className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1"
          />
        )}
      </span>
    </motion.span>
  );

  if (href) {
    return (
      <Link href={href} onClick={onClick} target={target} rel={rel} className="inline-flex">
        {inner}
      </Link>
    );
  }
  return (
    <button onClick={onClick} className="inline-flex">
      {inner}
    </button>
  );
}
