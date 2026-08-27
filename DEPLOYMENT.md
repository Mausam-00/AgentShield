# Deploying AgentShield AI

The website's **Assess your agent** feature (`POST /api/assess`) shells out to the
Python AgentShield engine. So the host has **two runtime requirements**:

1. A **real Node server** (`next start`) — not a serverless/edge-only host.
2. **Python 3** on `PATH`, with the repo's `agentshield/` + `scripts/` present.

The engine is **pure Python standard library** — no `pip install` needed.

If either requirement is missing, the upload feature **degrades gracefully**:
the API returns `"Python engine not found on the server…"` and the rest of the
site keeps working. Override the interpreter with the `AGENTSHIELD_PYTHON`
environment variable (e.g. `python`, `python3`, or an absolute path).

---

## Option 1 — Docker (recommended, works fully)

A root [`Dockerfile`](./Dockerfile) bundles Node + Python 3 + the whole repo and
runs `next start`. Build **from the repository root**:

```bash
docker build -t agentshield .
docker run -p 3000:3000 agentshield
# open http://localhost:3000  →  "Assess your agent"
```

Deploy that image to any container host:

- **Azure Container Apps** — `az containerapp up --source . --ingress external --target-port 3000`
- **Azure App Service (Linux container)**, **Render**, **Railway**, **Fly.io** — point them at this repo/Dockerfile; expose port `3000`.

No extra env vars are required (the image sets `AGENTSHIELD_PYTHON=python3`).

---

## Option 2 — A VM / bare Node host

On any VM (Azure VM, EC2, etc.) with Node 18+ and Python 3:

```bash
git clone https://github.com/Mausam-00/agentshield-web.git app && cd app
cd agentshield-web
npm ci
npm run build
npm run start            # serves on :3000; engine resolved at ../scripts/
```

Keep it alive with `pm2`, a `systemd` unit, or the container above.

---

## Option 3 — Vercel / static & serverless hosts (site only)

Vercel deploys and runs the marketing site, **but not** the Python upload
feature (serverless Node can't spawn Python, and files outside the Root
Directory aren't deployed). The upload section returns the graceful
"engine not found" message; everything else works.

To deploy the **site** on Vercel from this monorepo:

1. Import the repo in Vercel.
2. **Project → Settings → General → Root Directory → `agentshield-web`** (click
   *Edit*, type the folder, save). This tells Vercel the Next.js app lives in
   that subfolder.
3. Framework Preset: **Next.js** (auto-detected). Build/Output can stay default.
4. Deploy.

For a Vercel deployment that also runs the assessment, you would need to move the
engine call to a **Vercel Python Serverless Function** (`api/*.py`) and include
the `agentshield/` package inside the Root Directory — a larger change. For now,
use Option 1 or 2 when you need the live upload feature.

---

## Quick host comparison

| Host | Site renders | Upload feature works | Notes |
|---|---|---|---|
| Docker (Option 1) | ✅ | ✅ | Node + Python in one image |
| VM / bare Node (Option 2) | ✅ | ✅ | install Python 3 yourself |
| Azure Container Apps / App Service (container) | ✅ | ✅ | deploy the image |
| Vercel / Netlify (serverless) | ✅ | ❌ (graceful message) | set Root Directory = `agentshield-web` |
