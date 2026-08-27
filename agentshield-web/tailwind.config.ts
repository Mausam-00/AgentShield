import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#04060d",
          900: "#070b16",
          850: "#0a1020",
          800: "#0d1426",
          700: "#131c33",
          600: "#1b2742",
        },
        graphite: {
          500: "#2a3552",
          400: "#3b4a6b",
        },
        neon: {
          cyan: "#38e1ff",
          blue: "#4f7cff",
          violet: "#a855f7",
          teal: "#5eead4",
          magenta: "#e94bd0",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      maxWidth: {
        container: "1240px",
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(79,124,255,0.55)",
        "glow-violet": "0 0 46px -10px rgba(168,85,247,0.6)",
        card: "0 24px 70px -30px rgba(0,0,0,0.85)",
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to bottom, transparent, #04060d 78%), repeating-linear-gradient(90deg, rgba(79,124,255,0.06) 0 1px, transparent 1px 64px), repeating-linear-gradient(0deg, rgba(79,124,255,0.06) 0 1px, transparent 1px 64px)",
        "radial-hero":
          "radial-gradient(60% 60% at 20% 10%, rgba(79,124,255,0.22), transparent 60%), radial-gradient(50% 60% at 85% 20%, rgba(168,85,247,0.2), transparent 60%)",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-14px)" },
        },
        "float-slow": {
          "0%,100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(-24px) rotate(6deg)" },
        },
        aurora: {
          "0%,100%": { transform: "translate3d(0,0,0) scale(1)", opacity: "0.55" },
          "50%": { transform: "translate3d(4%, -4%,0) scale(1.15)", opacity: "0.8" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "spin-slow": {
          to: { transform: "rotate(360deg)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "float-slow": "float-slow 11s ease-in-out infinite",
        aurora: "aurora 16s ease-in-out infinite",
        shimmer: "shimmer 3.5s linear infinite",
        "spin-slow": "spin-slow 26s linear infinite",
        "pulse-ring": "pulse-ring 3s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
