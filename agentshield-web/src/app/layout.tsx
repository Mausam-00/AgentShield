import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ScrollProgress } from "@/components/background/ScrollProgress";
import { CursorGlow } from "@/components/background/CursorGlow";
import { Intro } from "@/components/intro/Intro";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { AboutOverlay } from "@/components/ui/AboutOverlay";
import { site } from "@/lib/site";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://agentshield.ai"),
  title: {
    default: `${site.name} — ${site.tagline}`,
    template: `%s · ${site.name}`,
  },
  description:
    "AgentShield AI is the security control plane for the agentic enterprise. Predict, govern, approve, execute safely, and audit every autonomous action.",
  keywords: [
    "AI governance",
    "agent security",
    "AI TRiSM",
    "Responsible AI",
    "AI red-team",
    "agentic AI",
  ],
  openGraph: {
    title: `${site.name} — ${site.tagline}`,
    description:
      "The security control plane for the agentic enterprise. Deterministic policy, adversarial red-team and Responsible AI in one platform.",
    type: "website",
    images: ["/logo.png"],
  },
  icons: { icon: "/logo.png" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body className="noise font-sans antialiased">
        <Intro />
        <CommandPalette />
        <AboutOverlay />
        <ScrollProgress />
        <CursorGlow />
        <Navbar />
        <main className="relative">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
