# Deploy AgentShield to Azure — Browser Only (no Azure CLI)

This guide deploys the whole app (Next.js site **+** Python engine, so the
**Assess-your-agent upload feature works**) to **Azure Container Apps** using
only your browser. Azure builds the repo-root `Dockerfile` in the cloud via
Azure Container Registry — you need **no local Docker and no `az` CLI login**.

> **Account note:** Your `@microsoft.com` corporate account is blocked by
> Conditional Access for this. Sign in to the Azure Portal with a **personal
> Azure account that has an active subscription** (create a free one at
> <https://azure.microsoft.com/free> if needed). Use a private/incognito browser
> window so corporate SSO doesn't auto-select the wrong account.

---

## Path A — Portal wizard sets up GitHub deploy (recommended, fully automatic)

The Portal creates the GitHub Actions workflow **and** the credentials for you.

1. Go to <https://portal.azure.com> → search **Container Apps** → **Create**.
2. **Basics** tab:
   - **Subscription / Resource group:** create `rg-agentshield`.
   - **Container app name:** `agentshield`.
   - **Region:** `East US` (or nearest, e.g. `Central India`).
   - **Container Apps environment:** create `agentshield-env`.
3. **Deployment source** → choose **Continuous deployment (GitHub)**.
   - Authorize GitHub, then pick:
     - **Organization:** `Mausam-00`
     - **Repository:** `AgentShield`
     - **Branch:** `main`
   - **Dockerfile:** select `Dockerfile` (in the repo root).
   - **Build context / path:** `/` (repository root — important, the Dockerfile
     copies `agentshield/`, `scripts/`, and `agentshield-web/`).
4. **Ingress** tab:
   - **Ingress:** Enabled, **Accepting traffic from anywhere** (external).
   - **Target port:** `3000`.
5. **Container** tab → **Environment variables**, add:
   - `AGENTSHIELD_PYTHON` = `python3`
   - `NODE_ENV` = `production`
6. **Review + create** → **Create**.

Azure commits a workflow to your repo (`.github/workflows/`) and adds the needed
secrets automatically. The first build runs on GitHub Actions; when it finishes,
the Container App page shows the **Application URL**.

7. Open the URL → go to the **Assess** section → upload an agent `.md` → confirm
   you get a verdict and a downloadable report. Done. ✅

---

## Path B — Use the committed workflow (`azure-container-apps.yml`)

Use this if you prefer the curated workflow already in
`.github/workflows/azure-container-apps.yml`. It needs three secrets that use
OIDC (no stored password).

### 1. Create an app registration (browser)

1. Portal → **Microsoft Entra ID** → **App registrations** → **New
   registration** → name `agentshield-deployer` → **Register**.
2. Copy the **Application (client) ID** and **Directory (tenant) ID**.
3. **Certificates & secrets** → **Federated credentials** → **Add credential** →
   scenario **GitHub Actions deploying Azure resources**:
   - Organization: `Mausam-00`, Repository: `AgentShield`
   - Entity: **Branch**, Branch: `main`
   - (Add a second credential with Entity **Environment** or **Pull request** if
     you later trigger from those.)

### 2. Give it permission on the subscription

Portal → **Subscriptions** → your subscription → **Access control (IAM)** →
**Add role assignment** → role **Contributor** → assign to the
`agentshield-deployer` app. (Copy the **Subscription ID** from the subscription
overview.)

### 3. Add the GitHub secrets

GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New
repository secret**, add:

| Secret name             | Value                          |
| ----------------------- | ------------------------------ |
| `AZURE_CLIENT_ID`       | Application (client) ID        |
| `AZURE_TENANT_ID`       | Directory (tenant) ID          |
| `AZURE_SUBSCRIPTION_ID` | Subscription ID                |

### 4. Run it

GitHub repo → **Actions** → **Deploy to Azure Container Apps** → **Run
workflow** (defaults: `rg-agentshield`, `eastus`, `agentshield`,
`agentshield-env`). The final step prints the live `https://…` URL.

To deploy automatically on every push to `main`, uncomment the `push:` trigger
at the top of the workflow.

---

## What you get / cost

- A public HTTPS URL serving the site with a **working upload→report** feature.
- Container Apps scales to zero when idle, so cost is low; a small always-warm
  setup is a few USD/month. Delete `rg-agentshield` to stop all charges.

## Troubleshooting

- **Upload returns "Python engine not found":** the container is missing Python
  or the repo files. Ensure the build used the **repo-root Dockerfile** with
  build context `/`, and that `AGENTSHIELD_PYTHON=python3` is set.
- **Build fails on GitHub:** open the Actions run logs. Most failures are a wrong
  Dockerfile path or build context — both must point at the repository root.
- **Wrong account / access blocked:** you signed in with the corporate account.
  Use a private window and a personal subscription.
