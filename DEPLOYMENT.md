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

- **Azure Container Apps (one command)** — from the repo root:

  ```powershell
  ./deploy/azure-containerapp.ps1          # Windows / PowerShell
  ```
  ```bash
  ./deploy/azure-containerapp.sh           # Linux / macOS / Cloud Shell
  ```

  This wraps `az containerapp up`, which **cloud-builds** the `Dockerfile` with
  ACR (no local Docker needed), provisions the resource group + environment, and
  deploys with external ingress on port 3000. Override defaults via parameters
  or env vars, e.g. `./deploy/azure-containerapp.ps1 -ResourceGroup rg-agentshield -Location eastus -AppName agentshield`.
  Re-run the script to redeploy. It prints the public `https://…` URL at the end.

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

## Quick host comparison

| Host | Site renders | Upload feature works | Notes |
|---|---|---|---|
| Docker (Option 1) | ✅ | ✅ | Node + Python in one image |
| VM / bare Node (Option 2) | ✅ | ✅ | install Python 3 yourself |
| Azure Container Apps / App Service (container) | ✅ | ✅ | deploy the image |
