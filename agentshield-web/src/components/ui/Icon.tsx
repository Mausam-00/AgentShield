"use client";

import {
  Activity,
  Cpu,
  GitBranch,
  Lock,
  Radar,
  Scale,
  ScrollText,
  ShieldCheck,
  Workflow,
  ArrowRight,
  ArrowUpRight,
  Check,
  Menu,
  X,
  Sparkles,
  Gauge,
  Coins,
  TrendingDown,
  Plus,
  Minus,
  Zap,
  Database,
  Layers,
  Play,
  Upload,
  FileText,
  Download,
  Loader2,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";

const map: Record<string, LucideIcon> = {
  Activity,
  Cpu,
  GitBranch,
  Lock,
  Radar,
  Scale,
  ScrollText,
  ShieldCheck,
  Workflow,
  ArrowRight,
  ArrowUpRight,
  Check,
  Menu,
  X,
  Sparkles,
  Gauge,
  Coins,
  TrendingDown,
  Plus,
  Minus,
  Zap,
  Database,
  Layers,
  Play,
  Upload,
  FileText,
  Download,
  Loader2,
  AlertTriangle,
};

export function Icon({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const Cmp = map[name] ?? Sparkles;
  return <Cmp className={className} strokeWidth={1.6} />;
}
