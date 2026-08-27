import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Pill({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-white/70",
        className
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan shadow-[0_0_10px_2px_rgba(56,225,255,0.8)]" />
      {children}
    </span>
  );
}
