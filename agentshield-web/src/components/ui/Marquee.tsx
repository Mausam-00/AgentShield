"use client";

import { motion } from "framer-motion";

export function Marquee({ items }: { items: string[] }) {
  const row = [...items, ...items];
  return (
    <div className="relative overflow-hidden py-2 [mask-image:linear-gradient(90deg,transparent,black_12%,black_88%,transparent)]">
      <motion.div
        className="flex w-max gap-16 pr-16"
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration: 26, ease: "linear", repeat: Infinity }}
      >
        {row.map((item, i) => (
          <span
            key={i}
            className="whitespace-nowrap font-display text-lg font-semibold tracking-[0.2em] text-white/35"
          >
            {item}
          </span>
        ))}
      </motion.div>
    </div>
  );
}
