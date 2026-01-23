# CSAT Guardian - Deployment Guide (Commercial Azure)

## Overview

This guide explains how to deploy CSAT Guardian to **Commercial Azure** from a locked-down PC that doesn't have VS Code or AI tools.

**Target Environment:**
- Subscription ID: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `KMonteagudo_CSAT_Guardian`
- Region: East US
- Cloud: Commercial Azure (not Government)

---

## Prerequisites

Before starting, ensure the locked-down PC has:

1. **Azure CLI** installed
   - Download: https://aka.ms/installazurecliwindows
   - Verify: `az --version`

2. **PowerShell 5.1+** (usually pre-installed on Windows)
   - Verify: `$PSVersionTable.PSVersion`

3. **ODBC Driver 18 for SQL Server** (for database seeding)
   - Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

4. **sqlcmd utility** (for database seeding)
   - Usually installed with ODBC Driver, or download SQL Server tools

---

## Deployment Steps

### Step 1: Transfer Files

Copy the `csat-guardian-deployment.zip` file to the locked-down PC.

Unzip to a location like `C:\Deploy\csat-guardian`

### Step 2: Open PowerShell as Administrator

Press `Win + X` → Select "Windows PowerShell (Admin)"

### Step 3: Navigate to Deployment Folder

```powershell
cd C:\Deploy\csat-guardian\infrastructure
```

### Step 4: Login to Azure

```powershell
# Login to Azure (this will open a browser for authentication)
az login

# Set the subscription
az account set --subscription "a20d761d-cb36-4f83-b827-58ccdb166f39"

# Verify you're in the right subscription
az account show --query "{Name:name, SubscriptionId:id}" -o table
```

### Step 5: Run the Deployment Script

```powershell
# Run the all-in-one deployment script
# Replace 'YourSecurePassword123!' with a strong password (min 8 chars, must include uppercase, lowercase, number)

.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!"
```

**The script will:**
1. Deploy all Azure infrastructure (VNet, SQL, OpenAI, Key Vault, App Service)
2. Create database tables and insert sample data
3. Deploy the application code to App Service

**This takes approximately 10-15 minutes.**

### Step 6: Verify Deployment

After the script completes, test the application:

```powershell
# Test health endpoint
$response = Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"
$response | ConvertTo-Json

# Test engineers endpoint
$response = Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/engineers"
$response | ConvertTo-Json

# Test cases endpoint
$response = Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/cases"
$response | ConvertTo-Json
```

### Step 7: Open the Application

Open a browser and navigate to:
- **Application:** https://app-csatguardian-dev.azurewebsites.net
- **API Docs:** https://app-csatguardian-dev.azurewebsites.net/docs

---

## Troubleshooting

### "az: command not found"
Azure CLI is not installed. Download from https://aka.ms/installazurecliwindows

### "Login failed"
Run `az login` again. Make sure you're using an account with access to the subscription.

### "Resource group does not exist"
The resource group `KMonteagudo_CSAT_Guardian` must exist before deployment:
```powershell
az group create --name KMonteagudo_CSAT_Guardian --location eastus
```

### "SQL firewall rule failed"
Manually add your IP in Azure Portal:
1. Go to SQL Server `sql-csatguardian-dev`
2. Networking → Firewall rules
3. Add your client IP

### "Database seeding failed"
If sqlcmd isn't working, you can seed the database manually:
1. Go to Azure Portal → SQL Database → Query editor
2. Copy the SQL from `infrastructure/deploy-all.ps1` (the `$sqlScript` section)
3. Paste and run in Query editor

### "App Service deployment failed"
Try manual ZIP deployment:
```powershell
# Create the zip manually
Compress-Archive -Path "C:\Deploy\csat-guardian\src\*" -DestinationPath "app.zip"

# Deploy
az webapp deploy --resource-group KMonteagudo_CSAT_Guardian --name app-csatguardian-dev --src-path app.zip --type zip
```

### App returns 500 errors
Check application logs:
```powershell
az webapp log tail --resource-group KMonteagudo_CSAT_Guardian --name app-csatguardian-dev
```

---

## What Gets Deployed

| Resource | Name | Purpose |
|----------|------|---------|
| Virtual Network | vnet-csatguardian-dev | Private networking |
| SQL Server | sql-csatguardian-dev | Database server |
| SQL Database | sqldb-csatguardian-dev | Application data |
| Azure OpenAI | oai-csatguardian-dev | Sentiment analysis (GPT-4o) |
| Key Vault | kv-csatguardian-dev | Secrets storage |
| App Service Plan | asp-csatguardian-dev | Hosting plan |
| App Service | app-csatguardian-dev | Web application |
| Application Insights | appi-csatguardian-dev | Monitoring |
| Private Endpoints | pe-* | Private connectivity |
| Private DNS Zones | privatelink.* | DNS resolution |

---

## Post-Deployment (Optional)

### Disable Public Access

After verifying everything works, disable public access for security:

```powershell
# Disable public access on SQL Server
az sql server update --resource-group KMonteagudo_CSAT_Guardian --name sql-csatguardian-dev --enable-public-network false

# Disable public access on Key Vault
az keyvault update --resource-group KMonteagudo_CSAT_Guardian --name kv-csatguardian-dev --public-network-access Disabled

# Disable public access on Azure OpenAI
az cognitiveservices account update --resource-group KMonteagudo_CSAT_Guardian --name oai-csatguardian-dev --public-network-access Disabled
```

**Note:** After disabling public access, resources are only accessible through the VNet/Private Endpoints.

---

## Clean Up (If Needed)

To delete all resources:

```powershell
az group delete --name KMonteagudo_CSAT_Guardian --yes --no-wait
```

**Warning:** This deletes everything including data!

---

## Support

If deployment fails, save the error output and contact the development team.

Useful diagnostic commands:
```powershell
# Show deployment status
az deployment group list --resource-group KMonteagudo_CSAT_Guardian -o table

# Show deployment errors
az deployment group show --resource-group KMonteagudo_CSAT_Guardian --name <deployment-name> --query properties.error

# List all resources
az resource list --resource-group KMonteagudo_CSAT_Guardian -o table
```
