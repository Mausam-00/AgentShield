<#
.SYNOPSIS
    One-command deploy of AgentShield AI (Next.js site + Python engine) to
    Azure Container Apps. Cloud-builds the root Dockerfile with ACR — no local
    Docker required.

.DESCRIPTION
    Wraps `az containerapp up`, which provisions the resource group, Container
    Apps environment, and registry, builds the image from ./Dockerfile, and
    deploys it with external ingress on port 3000. Re-running redeploys the app.

.EXAMPLE
    ./deploy/azure-containerapp.ps1
    ./deploy/azure-containerapp.ps1 -ResourceGroup rg-agentshield -Location eastus -AppName agentshield
#>
[CmdletBinding()]
param(
    [string]$ResourceGroup = "rg-agentshield",
    [string]$Location      = "eastus",
    [string]$AppName       = "agentshield",
    [string]$Environment   = "agentshield-env"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) not found. Install it: https://aka.ms/InstallAzureCLI"
}

Write-Host "==> Checking Azure sign-in..." -ForegroundColor Cyan
if (-not (az account show 2>$null)) {
    Write-Host "    Not signed in — launching 'az login'..." -ForegroundColor Yellow
    az login | Out-Null
}
$sub = az account show --query "{name:name, id:id}" -o tsv
Write-Host "    Using subscription: $sub"

Write-Host "==> Ensuring the containerapp CLI extension..." -ForegroundColor Cyan
az extension add --name containerapp --upgrade --only-show-errors 2>$null | Out-Null

Write-Host "==> Deploying '$AppName' to Container Apps (cloud build from Dockerfile)..." -ForegroundColor Cyan
Write-Host "    Resource group : $ResourceGroup"
Write-Host "    Location       : $Location"
Write-Host "    Environment    : $Environment"
Write-Host "    Source         : $RepoRoot"

az containerapp up `
    --name $AppName `
    --resource-group $ResourceGroup `
    --location $Location `
    --environment $Environment `
    --source "$RepoRoot" `
    --ingress external `
    --target-port 3000 `
    --env-vars "AGENTSHIELD_PYTHON=python3" "NODE_ENV=production"

if ($LASTEXITCODE -ne 0) { throw "az containerapp up failed with exit code $LASTEXITCODE." }

$fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host ""
Write-Host "==> Deployed." -ForegroundColor Green
Write-Host "    URL: https://$fqdn"
Write-Host "    Open the site and use the 'Assess your agent' section to upload an .md and download a report."
