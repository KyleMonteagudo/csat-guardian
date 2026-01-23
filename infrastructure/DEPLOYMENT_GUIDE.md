# CSAT Guardian - Deployment Guide

## Overview

This guide explains how to deploy CSAT Guardian to **Commercial Azure** from a locked-down PC.

**Target Environment:**
- Subscription ID: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `KMonteagudo_CSAT_Guardian`
- Region: East US

---

## Prerequisites

Before starting, ensure the locked-down PC has:

1. **Azure CLI** installed
   - Download: https://aka.ms/installazurecliwindows
   - Verify: `az --version`

2. **PowerShell 5.1+** (pre-installed on Windows)
   - Verify: `$PSVersionTable.PSVersion`

3. **Git** installed
   - Download: https://git-scm.com/download/win
   - Verify: `git --version`

**Note:** ODBC Driver is NOT required on the deployment machine. Database seeding is done via Azure Portal.

---

## Step-by-Step Deployment

### Step 1: Clone the Repository

```powershell
cd C:\Projects  # or wherever you want
git clone https://github.com/kmonteagudo_microsoft/csat-guardian.git
cd csat-guardian
git checkout develop
```

### Step 2: Login to Azure

```powershell
az login
az account set --subscription "a20d761d-cb36-4f83-b827-58ccdb166f39"

# Verify
az account show --query "{Name:name, SubscriptionId:id}" -o table
```

### Step 3: Create Resource Group (if needed)

```powershell
az group create --name KMonteagudo_CSAT_Guardian --location eastus
```

### Step 4: Run the Deployment Script

```powershell
cd infrastructure

# Deploy infrastructure and app (skip database seeding)
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipDatabase
```

**This takes approximately 15-20 minutes** (Bastion alone takes ~10 min).

The script deploys:
- Virtual Network with private subnets
- Azure Bastion (for secure VM access)
- Dev-box VM (Windows 11, no public IP)
- Azure SQL Server + Database
- Azure OpenAI with GPT-4o
- Azure Key Vault
- App Service with VNet integration
- Private Endpoints for all backend services
- Private DNS Zones

### Step 5: Seed the Database (via Azure Portal)

Since we can't install ODBC on the locked-down PC, seed the database using Azure Portal:

1. Go to **Azure Portal** → **SQL databases** → `sqldb-csatguardian-dev`
2. Click **Query editor (preview)** in the left menu
3. Login with:
   - Username: `sqladmin`
   - Password: (the password you used in Step 4)
4. Copy the contents of `infrastructure/seed-database.sql`
5. Paste into Query editor and click **Run**

### Step 6: Verify Deployment

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
