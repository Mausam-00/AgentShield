"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GradientButton } from "@/components/ui/GradientButton";

const fields = [
  { name: "name", label: "Full name", type: "text", placeholder: "Ada Lovelace" },
  { name: "email", label: "Work email", type: "email", placeholder: "ada@company.com" },
  { name: "company", label: "Company", type: "text", placeholder: "Acme Corp" },
];

export function ContactForm() {
  const [sent, setSent] = useState(false);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setSent(true);
      }}
      className="relative overflow-hidden rounded-2xl glass p-7 sm:p-9"
    >
      <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-neon-violet/15 blur-3xl" />
      <div className="relative space-y-5">
        <div className="grid gap-5 sm:grid-cols-2">
          {fields.map((f) => (
            <div
              key={f.name}
              className={f.name === "company" ? "sm:col-span-2" : ""}
            >
              <label
                htmlFor={f.name}
                className="mb-2 block text-xs font-medium uppercase tracking-wider text-white/55"
              >
                {f.label}
              </label>
              <input
                id={f.name}
                name={f.name}
                type={f.type}
                required
                placeholder={f.placeholder}
                className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-neon-blue/50 focus:bg-white/[0.06] focus:ring-2 focus:ring-neon-blue/20"
              />
            </div>
          ))}
          <div className="sm:col-span-2">
            <label
              htmlFor="message"
              className="mb-2 block text-xs font-medium uppercase tracking-wider text-white/55"
            >
              How can we help?
            </label>
            <textarea
              id="message"
              name="message"
              rows={4}
              required
              placeholder="Tell us about the agents you need to govern…"
              className="w-full resize-none rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-neon-blue/50 focus:bg-white/[0.06] focus:ring-2 focus:ring-neon-blue/20"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <GradientButton>Request a briefing</GradientButton>
          <AnimatePresence>
            {sent && (
              <motion.p
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-sm text-neon-teal"
              >
                Thanks — this is a demo form. We&apos;ll be in touch.
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>
    </form>
  );
}
