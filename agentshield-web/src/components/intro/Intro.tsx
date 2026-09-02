"use client";

import { useEffect, useState } from "react";
import { LogoIntro } from "@/components/intro/LogoIntro";
import { HudIntro } from "@/components/intro/HudIntro";

// Which pre-hero intro to play. Override live with ?intro=particles or ?intro=hud.
const DEFAULT_VARIANT: "hud" | "particles" = "hud";

export function Intro() {
  const [variant, setVariant] = useState<"hud" | "particles" | null>(null);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("intro");
    setVariant(q === "particles" || q === "hud" ? q : DEFAULT_VARIANT);
  }, []);

  if (variant === null) return null;
  return variant === "particles" ? <LogoIntro /> : <HudIntro />;
}
