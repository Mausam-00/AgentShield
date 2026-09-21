# AgentShield AI — Website

A premium, enterprise-grade marketing site for **AgentShield AI**, the security
control plane for the agentic enterprise. A neural-security visual system with
a shield-centred network illustration, connected gate pathway, instrument
panels, and cinematic Framer Motion animations.

---

## Tech stack

| Layer      | Choice                                              |
| ---------- | --------------------------------------------------- |
| Framework  | Next.js 14 (App Router) + React 18                  |
| Styling    | Tailwind CSS 3.4 + custom design tokens             |
| Animation  | Framer Motion 11                                    |
| Graphics   | Three.js / React Three Fiber scenes with SVG fallbacks |
| UI tests   | Playwright, desktop and mobile Chromium            |
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

# 6. Browser regression tests (Node.js 20+; production build required)
npx playwright install chromium
npm run test:ui
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
│  │  ├─ three/                # SecurityVisual loader, WebGL scenes + SVG fallbacks
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
- **Materials** — quiet instrument panels, circuit traces, asymmetric feature
  cards, differentiated advisory/authority lanes, and restrained glass surfaces.
- **Motion** — scroll-reveal (`Reveal`/`RevealGroup`), staggered grids, page
  templates, animated stat counters, marquee, shimmer buttons, and network
  signals. Framer Motion uses the user's reduced-motion preference; the hero,
  zipper and assessment radar also have explicit reduced-motion handling.
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
- Graphics are decorative, not live telemetry. Desktop fine-pointer devices
  progressively load a real WebGL shield, a rotating six-node control network
  beside the differentiators, and a gate corridor beside the workflow. The
  latter two reflect card/gate selection without affecting engine decisions.
  Mobile, reduced-motion, unsupported WebGL, and context-loss cases use SVG
  fallbacks. WebGL loops pause offscreen and in hidden tabs; pixel ratio is
  capped at 1.5. A single bounded, 30fps canvas network sits behind all pages,
  pauses in hidden tabs, and becomes static for reduced-motion users.
- The efficiency dashboard replays the existing recorded benchmark in three
  illustrative stages, with interpolated counters and bars. This is explicitly
  not a live engine run: there are no API calls, new measurements, or fabricated
  results. It runs once on entry, offers pause/resume/replay, pauses offscreen
  and in hidden tabs, and displays the final values immediately for reduced
  motion. The existing benchmark values, caveats, and expandable details remain.
- The closing call to action has a lightweight SVG security perimeter with
  agent chips, a locked shield, and an audit-record motif. Decorative signal
  paths pause offscreen/in hidden tabs and stop for reduced-motion users. This
  does not create a connector or represent a running agent workflow.
- Three signature sequences are preserved: the once-per-session HUD boot,
  the About Us zipper (including its reverse close), and the assessment radar
  while awaiting an API response. Loader stages are illustrative, not server
  progress. Reduced-motion users get quieter versions, not missing functionality.
- Browser tests cover those sequences, rendering modes, animation lifecycle,
  benchmark replay, gate selection, layout overflow,
  and assessment success/failure using explicitly synthetic API fixtures. Tests
  do not call the Python engine or cloud providers. The runner owns a temporary
  local production server on port 3210 and stops it on completion.
- Replace `public/logo.png` and the content in `src/lib/site.ts` to rebrand.
