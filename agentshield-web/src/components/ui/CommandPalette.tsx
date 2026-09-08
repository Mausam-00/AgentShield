"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { nav, site } from "@/lib/site";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

type Command = {
  id: string;
  label: string;
  hint?: string;
  icon: string;
  run: () => void;
};

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = useMemo<Command[]>(() => {
    const go = (href: string, external?: boolean) => () => {
      setOpen(false);
      if (external) window.open(href, "_blank", "noopener,noreferrer");
      else router.push(href);
    };
    const navCmds: Command[] = nav.map((n) => ({
      id: `nav-${n.label}`,
      label: n.label,
      hint: n.external ? "External" : "Navigate",
      icon: n.external ? "ArrowUpRight" : "ArrowRight",
      run: go(n.href, n.external),
    }));
    return [
      ...navCmds,
      {
        id: "about",
        label: "About AgentShield AI",
        hint: "What it is, features & how it differs",
        icon: "Sparkles",
        run: () => {
          setOpen(false);
          window.dispatchEvent(new Event("open-about"));
        },
      },
      {
        id: "run-engine",
        label: "Run the Engine",
        hint: "Assessment console",
        icon: "Play",
        run: go("/#demo"),
      },
      {
        id: "github",
        label: "Open GitHub repository",
        hint: "github.com",
        icon: "GitBranch",
        run: go(site.repo, true),
      },
      {
        id: "copy-clone",
        label: "Copy git clone command",
        hint: "Clipboard",
        icon: "Copy",
        run: () => {
          navigator.clipboard?.writeText(`git clone ${site.repo}.git`);
          setOpen(false);
        },
      },
    ];
  }, [router]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => c.label.toLowerCase().includes(q));
  }, [commands, query]);

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setCursor(0);
  }, []);

  // Global open/close hotkeys and a custom event (for a navbar trigger).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape") {
        close();
      }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener("open-cmdk", onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("open-cmdk", onOpen);
    };
  }, [close]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 20);
  }, [open]);

  useEffect(() => setCursor(0), [query]);

  function onListKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      filtered[cursor]?.run();
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[90] flex items-start justify-center px-4 pt-[14vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          <div
            className="absolute inset-0 bg-ink-950/70 backdrop-blur-sm"
            onClick={close}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            onKeyDown={onListKey}
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="glass-strong relative z-10 w-full max-w-xl overflow-hidden rounded-2xl shadow-card"
          >
            <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
              <Icon name="Search" className="h-4 w-4 text-white/45" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search actions, pages…"
                className="w-full bg-transparent text-sm text-white placeholder:text-white/35 focus:outline-none"
              />
              <kbd className="rounded border border-white/15 px-1.5 py-0.5 text-[10px] text-white/40">
                ESC
              </kbd>
            </div>

            <div className="max-h-80 overflow-y-auto p-2">
              {filtered.length === 0 && (
                <div className="px-3 py-8 text-center text-sm text-white/40">
                  No matching actions
                </div>
              )}
              {filtered.map((c, i) => (
                <button
                  key={c.id}
                  onMouseEnter={() => setCursor(i)}
                  onClick={c.run}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                    i === cursor ? "bg-white/[0.08]" : "hover:bg-white/[0.04]"
                  )}
                >
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-neon-blue/20 to-neon-violet/20 text-neon-cyan">
                    <Icon name={c.icon} className="h-4 w-4" />
                  </span>
                  <span className="flex-1">
                    <span className="block text-sm font-medium text-white">
                      {c.label}
                    </span>
                    {c.hint && (
                      <span className="block text-xs text-white/45">{c.hint}</span>
                    )}
                  </span>
                  {i === cursor && (
                    <Icon name="CornerDownLeft" className="h-3.5 w-3.5 text-white/35" />
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
