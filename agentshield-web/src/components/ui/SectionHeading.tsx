import { Reveal } from "./Reveal";
import { Pill } from "./Pill";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  align = "center",
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  subtitle?: ReactNode;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-5",
        align === "center" ? "items-center text-center" : "items-start text-left",
        className
      )}
    >
      {eyebrow && (
        <Reveal>
          <Pill>{eyebrow}</Pill>
        </Reveal>
      )}
      <Reveal delay={0.06}>
        <h2 className="max-w-3xl font-display text-4xl font-semibold leading-[1.05] tracking-tight text-white sm:text-5xl">
          {title}
        </h2>
      </Reveal>
      {subtitle && (
        <Reveal delay={0.12}>
          <p
            className={cn(
              "max-w-2xl text-base leading-relaxed text-white/60 sm:text-lg",
              align === "center" ? "mx-auto" : ""
            )}
          >
            {subtitle}
          </p>
        </Reveal>
      )}
    </div>
  );
}
