# CSAT Guardian - Deployment Guide

## Overview

This guide explains how to deploy CSAT Guardian to **Commercial Azure** using Cloud Shell.

**Current Deployed Environment:**
- Subscription ID: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `CSAT_Guardian_Dev`
- Region: Central US

---

## Prerequisites

- Access to Azure Portal with Cloud Shell
- Git repository access: `https://github.com/kmonteagudo_microsoft/csat-guardian.git`

---

## Deployment Workflow

### Initial Setup (One-time in Cloud Shell)

```bash
# Clone the repo
git clone https://github.com/kmonteagudo_microsoft/csat-guardian.git
cd csat-guardian
```

### Deploy/Update Application

```bash
cd ~/csat-guardian
git pull
cd src
az webapp up --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --runtime "PYTHON:3.11"
```

This takes 3-5 minutes to build and deploy.

---

## Current Resource Names

| Resource | Name |
|----------|------|
| Resource Group | `CSAT_Guardian_Dev` |
| App Service | `app-csatguardian-dev` |
| App Service Plan | `asp-csatguardian-dev` |
| SQL Server | `sql-csatguardian-dev` |
| SQL Database | `sqldb-csatguardian-dev` |
| AI Services | `ais-csatguardian-dev` |
| Key Vault | `kv-csatguard-dev` |
| Bastion | `bas-csatguardian-dev` |
| Dev-box VM | `vm-devbox-csatguardian` |

---

## Verify Deployment

Connect to the dev-box VM via Bastion to test:

1. Go to **Azure Portal** → **Virtual machines** → `vm-devbox-csatguardian`
2. Click **Connect** → **Bastion**
3. Enter credentials:
   - Username: `testadmin`
   - Password: `Password1!`
4. Open browser in VM and go to:
   - https://app-csatguardian-dev.azurewebsites.net/docs

---

## What Gets Deployed

| Resource | Name | Purpose |
|----------|------|---------|
| Virtual Network | vnet-csatguardian-dev | Private networking (10.100.0.0/16) |
| Azure Bastion | bas-csatguardian-dev | Secure VM access |
| Dev-box VM | vm-devbox-csatguardian | Testing private endpoints |
| SQL Server | sql-csatguardian-dev | Database server |
| SQL Database | sqldb-csatguardian-dev | Application data |
| Azure OpenAI | oai-csatguardian-dev | Sentiment analysis (GPT-4o) |
| Key Vault | kv-csatguardian-dev | Secrets storage |
| App Service Plan | asp-csatguardian-dev | Hosting plan (Linux B1) |
| App Service | app-csatguardian-dev | Web application |
| Application Insights | appi-csatguardian-dev | Monitoring |
| Private Endpoints | pe-* | Private connectivity |
| Private DNS Zones | privatelink.* | DNS resolution |

---

## Redeploying Code Changes

After making code changes, redeploy just the app:

```powershell
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipInfrastructure -SkipDatabase
```

Or manually:

```powershell
# Create zip of src folder
Compress-Archive -Path "..\src\*" -DestinationPath "app.zip" -Force

# Copy requirements.txt into the zip
Compress-Archive -Path "..\requirements.txt" -DestinationPath "app.zip" -Update

# Deploy
az webapp deploy --resource-group KMonteagudo_CSAT_Guardian --name app-csatguardian-dev --src-path app.zip --type zip
```

---

## Troubleshooting

### "az: command not found"
Azure CLI is not installed. Download from https://aka.ms/installazurecliwindows

### "Login failed"
Run `az login` again. Make sure you're using an account with access to the subscription.

### "Resource group does not exist"
```powershell
az group create --name KMonteagudo_CSAT_Guardian --location eastus
```

### Bastion connection fails
Wait 5-10 minutes after deployment for Bastion to fully provision.

### App returns 500 errors
Check logs from dev-box VM:
```powershell
az webapp log tail --resource-group KMonteagudo_CSAT_Guardian --name app-csatguardian-dev
```

### Query editor won't connect
Make sure you're using the correct SQL admin password from deployment.

---

## Clean Up (Delete Everything)

```powershell
az group delete --name KMonteagudo_CSAT_Guardian --yes --no-wait
```

**Warning:** This deletes ALL resources including data!

---

## Architecture Summary

```
Internet
    │
    └──▶ Azure Bastion ──▶ Dev-box VM (private)
                              │
                              ├──▶ App Service (VNet integrated)
                              │        │
                              │        ├──▶ SQL (Private Endpoint)
                              │        ├──▶ Key Vault (Private Endpoint)
                              │        └──▶ OpenAI (Private Endpoint)
                              │
                              └──▶ Direct test of private endpoints
```

All backend services (SQL, Key Vault, OpenAI) have **public access disabled** and are only accessible via Private Endpoints within the VNet.
