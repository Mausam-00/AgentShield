# AgentShield AI — Website

A premium, enterprise-grade marketing site for **AgentShield AI**, the security
control plane for the agentic enterprise. Dark luxury theme, glassmorphism,
cinematic Framer Motion animations, a React Three Fiber 3D hero, animated
particle/aurora backgrounds and 11 fully separate pages.

> **Status:** Hand-authored, production-shaped codebase. It has **not** been
> compiled in this environment because Node.js is not installed here. Follow the
> steps below to install dependencies, run and verify.

---

## Tech stack

| Layer      | Choice                                              |
| ---------- | --------------------------------------------------- |
| Framework  | Next.js 14 (App Router) + React 18                  |
| Styling    | Tailwind CSS 3.4 + custom design tokens             |
| Animation  | Framer Motion 11                                    |
| 3D         | Three.js + @react-three/fiber + @react-three/drei   |
| Icons      | lucide-react                                        |
| Language   | TypeScript 5.6                                       |

---

## Getting started

```bash
# 1. Install Node.js 18.18+ or 20+  (from the official nodejs.org site)
#    Windows (winget):  winget install OpenJS.NodeJS.LTS

# 2. From this folder, install dependencies
npm install

# 3. Run the dev server
npm run dev
# open the app at localhost port 3000

# 4. Production build + start
npm run build
npm run start

# 5. Lint
npm run lint
```

---

## Project structure

```
agentshield-web/
├─ public/
│  └─ logo.png                 # brand logo (from Designer.png)
├─ src/
│  ├─ app/                     # App Router routes (one folder per page)
│  │  ├─ layout.tsx            # fonts, SEO metadata, chrome (Navbar/Footer)
│  │  ├─ template.tsx          # per-route enter transition
│  │  ├─ globals.css           # design tokens + glass/gradient utilities
│  │  ├─ page.tsx              # Home
│  │  ├─ about/ services/ solutions/ products/
│  │  ├─ portfolio/ team/ testimonials/ blog/
│  │  └─ careers/ contact/
│  ├─ components/
│  │  ├─ layout/               # Navbar (mega-menu), MobileMenu, Footer
│  │  ├─ sections/             # Hero, FeatureGrid, GatesShowcase, CTASection…
│  │  ├─ background/           # ParticleField, AuroraBackground, CursorGlow…
│  │  ├─ three/                # HeroScene (R3F) + Hero3D (ssr:false loader)
│  │  └─ ui/                   # GlassCard, GradientButton, Reveal, Icon…
│  └─ lib/
│     ├─ site.ts               # ALL content + nav config (single source)
│     ├─ motion.ts             # shared Framer Motion variants
│     └─ utils.ts              # cn() class helper
└─ tailwind.config.ts          # colors, animations, shadows
```

All page copy, navigation, stats, services, case studies, team, testimonials,
posts and jobs live in **`src/lib/site.ts`** — edit there to update the site.

---

## Design system

- **Palette** — near-black `ink` scale (`#05070d → #1a2338`) with neon accents:
  cyan `#38e1ff`, blue `#4f7cff`, violet `#a855f7`, teal `#5eead4`,
  magenta `#f65fd0`. One dominant dark tone, neon used sparingly for emphasis.
- **Typography** — Space Grotesk (display), Inter (body), JetBrains Mono
  (labels/mono), all via `next/font/google`.
- **Materials** — glassmorphism (`.glass`), radial mouse-glow cards, aurora +
  particle fields, subtle grid fade and noise overlay.
- **Motion** — scroll-reveal (`Reveal`/`RevealGroup`), staggered grids, page
  templates, animated stat counters, marquee, shimmer buttons, 3D float. All
  respect `prefers-reduced-motion`.
- **Responsive** — mobile-first; sticky navbar collapses to an animated
  hamburger + full-screen mobile menu; grids reflow 1→2→3 columns.

---

## Pages

Home · About Us · Services · Solutions · Products · Case Studies (Portfolio) ·
Team · Testimonials · Insights (Blog) · Careers · Contact Us.

Each inner page opens with a shared `PageHero`, composes tailored sections from
`components/sections`, and (except Contact) closes with a `CTASection`.

---

## Notes

- The **Assess console** (home `#demo` section) is a *real* feature, not a
  mock. It uploads an agent `.md` to the `POST /api/assess` route handler, which
  runs the Python AgentShield engine (`scripts/agentshield_report.py` in the
  repo root) and returns a downloadable, self-contained HTML report plus an
  on-page verdict (runtime decision, assurance / red-team / Responsible AI
  posture, defense coverage, residual exposure). Nothing is executed against a
  target; the uploaded file is processed transiently and not retained.
  - **Runtime requirement:** the server needs **Python 3** on `PATH` with the
    `agentshield` package importable (it lives one level up, in the repo root).
    Override the interpreter with the `AGENTSHIELD_PYTHON` env var if needed.
  - Because it shells out to Python, this route needs the **Node runtime**
    (`next start` on a VM/container/Azure App Service) — it will not run on a
    static export or a pure-edge host. The rest of the site is fully static and
    the CLI/engine remain independently usable without the website.
- The contact form is a client-side demo (no backend); wire it to your API/email
  provider in `components/sections/ContactForm.tsx`.
- The 3D hero lazy-loads and is disabled during SSR for performance; it degrades
  gracefully behind the particle/aurora backdrop.
- Replace `public/logo.png` and the content in `src/lib/site.ts` to rebrand.
