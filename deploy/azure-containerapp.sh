#!/usr/bin/env bash
# One-command deploy of AgentShield AI (Next.js site + Python engine) to Azure
# Container Apps. Cloud-builds the root Dockerfile with ACR — no local Docker.
#
# Usage:
#   ./deploy/azure-containerapp.sh
#   RESOURCE_GROUP=rg-agentshield LOCATION=eastus APP_NAME=agentshield ./deploy/azure-containerapp.sh
#
# Wraps `az containerapp up`, which provisions the resource group, Container Apps
# environment, and registry, builds ./Dockerfile, and deploys with external
# ingress on port 3000. Re-running redeploys the app.
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-agentshield}"
LOCATION="${LOCATION:-eastus}"
APP_NAME="${APP_NAME:-agentshield}"
ENVIRONMENT="${ENVIRONMENT:-agentshield-env}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

command -v az >/dev/null 2>&1 || {
  echo "Azure CLI (az) not found. Install it: https://aka.ms/InstallAzureCLI" >&2
  exit 1
}

echo "==> Checking Azure sign-in..."
az account show >/dev/null 2>&1 || { echo "    Not signed in — launching 'az login'..."; az login >/dev/null; }
echo "    Using subscription: $(az account show --query name -o tsv)"

echo "==> Ensuring the containerapp CLI extension..."
az extension add --name containerapp --upgrade --only-show-errors >/dev/null 2>&1 || true

echo "==> Deploying '${APP_NAME}' to Container Apps (cloud build from Dockerfile)..."
echo "    Resource group : ${RESOURCE_GROUP}"
echo "    Location       : ${LOCATION}"
echo "    Environment    : ${ENVIRONMENT}"
echo "    Source         : ${REPO_ROOT}"

az containerapp up \
  --name "${APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --environment "${ENVIRONMENT}" \
  --source "${REPO_ROOT}" \
  --ingress external \
  --target-port 3000 \
  --env-vars "AGENTSHIELD_PYTHON=python3" "NODE_ENV=production"

FQDN="$(az containerapp show --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" \
  --query "properties.configuration.ingress.fqdn" -o tsv)"

echo ""
echo "==> Deployed."
echo "    URL: https://${FQDN}"
echo "    Open the site and use the 'Assess your agent' section to upload an .md and download a report."
