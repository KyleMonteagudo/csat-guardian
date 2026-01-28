# CSAT Guardian - Deployment Guide

## Overview

This guide explains how to deploy CSAT Guardian to **Commercial Azure**. Due to enterprise security constraints and Cloud Shell limitations, deployment uses the **Kudu file upload method**.

**Current Deployed Environment:**
- Subscription ID: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `CSAT_Guardian_Dev`
- Region: Central US

---

## Prerequisites

1. Access to **Azure Portal** with Cloud Shell
2. Access to **GitHub repository**: `https://github.com/kmonteagudo_microsoft/csat-guardian.git`
3. **SCM Basic Auth enabled** on App Service (required for Kudu access)

---

## ⚠️ Important: Why Standard Deployment Methods Don't Work

| Method | Issue |
|--------|-------|
| `az webapp up` | Cloud Shell MSI token scope doesn't support appservice.azure.com |
| `az webapp deployment source sync` | Caches old builds, often doesn't pick up new code |
| `az webapp deploy --type zip` | Same MSI token scope issue |

**Solution**: Use the **Kudu file upload method** described below.

---

## Complete Deployment Process

### Step 1: Clone Repository (Cloud Shell - First Time Only)

```bash
cd ~
git clone https://github.com/kmonteagudo_microsoft/csat-guardian.git
cd csat-guardian
```

### Step 2: Create Deployment Package (Cloud Shell)

```bash
cd ~/csat-guardian
git pull origin develop

# Remove any old package
rm -f deploy.zip

# Create deployment ZIP with src folder only (requirements.txt is inside src/)
zip -r deploy.zip src

# Deploy directly using az webapp deploy
az webapp deploy --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --src-path deploy.zip --type zip --clean
```

### Step 3: Verify Deployment

Test the health endpoint:
```bash
az vm run-command invoke \
  --resource-group CSAT_Guardian_Dev \
  --name vm-devbox-csatguardian \
  --command-id RunPowerShellScript \
  --scripts "Invoke-RestMethod -Uri 'https://app-csatguardian-dev.azurewebsites.net/api/health'"
```

---

## Startup Command

The App Service startup command is configured as:

```
cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Note**: `requirements.txt` lives inside `src/`, not at the root level.

---

## Restart App Service

If needed, restart via Cloud Shell:
```bash
az webapp restart --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev
```

---

## Required App Settings

| Setting | Value |
|---------|-------|
| `AZURE_OPENAI_ENDPOINT` | `https://ais-csatguardian-dev.cognitiveservices.azure.com/` |
| `AZURE_OPENAI_API_KEY` | `@Microsoft.KeyVault(VaultName=kv-csatguard-dev;SecretName=azure-openai-key)` |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` |
| `DATABASE_CONNECTION_STRING` | `Server=tcp:sql-csatguardian-dev.database.windows.net,1433;Initial Catalog=sqldb-csatguardian-dev;User ID=sqladmin;Password=XXXX;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;` |
| `WEBSITE_VNET_ROUTE_ALL` | `1` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `WEBSITES_PORT` | `8000` |

⚠️ **Note**: Use `AZURE_OPENAI_DEPLOYMENT`, NOT `AZURE_OPENAI_DEPLOYMENT_NAME`

---

## Database Deployment

### Deploy Schema (Cloud Shell)

```bash
# Get SQL password from Key Vault first
sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev \
  -U sqladmin -P '<password-from-keyvault>' \
  -i infrastructure/sql/001-schema-complete.sql
```

### Deploy Seed Data (Cloud Shell)

```bash
sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev \
  -U sqladmin -P '<password-from-keyvault>' \
  -i infrastructure/sql/002-seed-data.sql
```

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

### Option 1: From Devbox VM (via Bastion)

1. **Azure Portal** → **Virtual machines** → `vm-devbox-csatguardian`
2. Click **Connect** → **Bastion**
3. Credentials: `testadmin` / (password from Key Vault)
4. Open PowerShell and test:

```powershell
# Health check
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"

# List cases
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/cases"

# Chat with agent
$body = @{ message = "Check case-001"; engineer_id = "eng-001" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/chat" -Method POST -ContentType "application/json" -Body $body
```

### Option 2: Via Browser

1. Navigate to: `https://app-csatguardian-dev.azurewebsites.net/docs`
2. Test endpoints via Swagger UI

---

## Troubleshooting

### "No module named uvicorn" / "No module named fastapi"

The startup command must include pip install:
```
cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### App returns 500 errors

Check logs:
- **Portal**: App Service → Log stream
- **Kudu**: `https://app-csatguardian-dev.scm.azurewebsites.net/api/logstream`

### SQL connection fails

1. Verify `WEBSITE_VNET_ROUTE_ALL=1` in App Settings
2. Verify Private DNS zone is linked to VNet
3. Restart App Service after changing settings

### Chat endpoint returns error

1. Verify `AZURE_OPENAI_DEPLOYMENT` (not DEPLOYMENT_NAME) is set
2. Check Key Vault access for managed identity
3. Verify AZURE_OPENAI_ENDPOINT ends with `/`

### Kudu upload fails

1. Ensure **SCM Basic Auth** is enabled:
   - Portal → App Service → Configuration → General settings → SCM Basic Auth → **On**
2. Try refreshing the Kudu page

### Old code still running after deployment

1. Remove all files from wwwroot before deploying
2. Restart App Service (not just refresh)
3. Clear browser cache

---

## Clean Up (Delete Everything)

```bash
az group delete --name CSAT_Guardian_Dev --yes --no-wait
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
