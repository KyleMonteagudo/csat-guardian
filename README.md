# CSAT Guardian

> **Customer Satisfaction Guardian** - Proactive CSAT Risk Detection and Intervention

---

## 🚀 Quick Deployment (Secure Environment)

**Prerequisites on your machine:**
- Azure CLI installed
- Git installed
- PowerShell

### Step 1: Clone the Repository

```powershell
git clone https://github.com/kmonteagudo_microsoft/csat-guardian.git
cd csat-guardian
git checkout develop
```

### Step 2: Login to Azure

```powershell
az login
az account set --subscription "a20d761d-cb36-4f83-b827-58ccdb166f39"
az account show  # Verify: should show KMonteagudo subscription
```

### Step 3: Deploy Infrastructure + Application

```powershell
cd infrastructure
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipDatabase
```

**What this deploys:**
- Virtual Network with private subnets
- Azure Bastion for secure VM access
- Dev-box VM (Windows 11, no public IP)
- Azure SQL Database (private endpoint only)
- Azure OpenAI with gpt-4o model
- Key Vault for secrets
- App Service with VNet integration

**Expected time:** 15-20 minutes

### Step 4: Seed the Database (via Azure Portal)

Since ODBC drivers can't be installed on locked-down laptops, seed the database through the Azure Portal:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: `Resource Groups` → `KMonteagudo_CSAT_Guardian` → `sqldb-csatguardian-dev`
3. Click **Query editor (preview)** in the left menu
4. Login with:
   - **Username:** `sqladmin`
   - **Password:** (the SqlPassword you used in Step 3)
5. Open the file `infrastructure/seed-database.sql` from your local clone
6. Copy the entire contents and paste into the query editor
7. Click **Run**

### Step 5: Verify Deployment

**Option A: Via Bastion (from the dev-box VM)**

1. Azure Portal → `vm-devbox-csatguardian` → **Connect** → **Bastion**
2. Login: `testadmin` / `Password1!`
3. Open Edge browser on the VM and go to:
   ```
   https://app-csatguardian-dev.azurewebsites.net/docs
   ```

**Option B: Quick health check (if App Service has public endpoint)**

```powershell
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"
```

---

## 📋 Troubleshooting

### "Resource group not found"

```powershell
az group create --name KMonteagudo_CSAT_Guardian --location eastus
```

### "Deployment failed - name already exists"

Resources may already exist from a previous deployment. Check the Portal and delete conflicting resources, or run:

```powershell
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipDatabase
```

### "SQL connection failed"

The SQL server only accepts connections from within the VNet. You must:
1. Use the dev-box VM (via Bastion) to connect, OR
2. Use Azure Portal Query Editor (which bypasses the firewall)

### "App Service returns 500 error"

Check the logs:
1. Azure Portal → `app-csatguardian-dev` → **Log stream**
2. Or via CLI:
   ```powershell
   az webapp log tail --name app-csatguardian-dev --resource-group KMonteagudo_CSAT_Guardian
   ```

### Need to redeploy just the app code

```powershell
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipInfrastructure -SkipDatabase
```

---

## 🔐 Credentials Reference

| Resource | Username | Password |
|----------|----------|----------|
| SQL Admin | `sqladmin` | Your `-SqlPassword` value |
| Dev-box VM | `testadmin` | `Password1!` |

---

## 🏗️ Architecture

### Infrastructure Overview

```
Azure Commercial (East US)
└── KMonteagudo_CSAT_Guardian
    ├── VNet: 10.100.0.0/16
    │   ├── snet-app (10.100.1.0/24) - App Service
    │   ├── snet-private (10.100.2.0/24) - Private Endpoints
    │   ├── snet-devbox (10.100.3.0/24) - Dev VM
    │   └── AzureBastionSubnet (10.100.4.0/26) - Bastion
    │
    ├── Azure Bastion - Secure RDP access (no public IPs)
    ├── Dev-box VM - Windows 11 for testing
    │
    ├── App Service - FastAPI backend
    │   └── VNet integrated (outbound via VNet)
    │
    ├── Azure SQL - Private endpoint only
    ├── Azure OpenAI - gpt-4o model, private endpoint
    └── Key Vault - Stores all secrets
```

### Data Flow

```
Case Data (SQL) → Monitor Service → Sentiment Analysis (OpenAI) → Alerts → Dashboard
```

---

## 🔗 Deployed Resources

| Resource | Name | Access |
|----------|------|--------|
| **App Service** | `app-csatguardian-dev` | `https://app-csatguardian-dev.azurewebsites.net` |
| **SQL Server** | `sql-csatguardian-dev` | Private endpoint only |
| **Azure OpenAI** | `oai-csatguardian-dev` | Private endpoint only |
| **Key Vault** | `kv-csatguardian-dev` | Private endpoint only |
| **Bastion** | `bas-csatguardian-dev` | Portal → VM → Connect → Bastion |
| **Dev-box VM** | `vm-devbox-csatguardian` | Access via Bastion |

---

## 📡 API Endpoints

Once deployed, access Swagger docs at: `https://app-csatguardian-dev.azurewebsites.net/docs`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with service status |
| `/api/engineers` | GET | List all engineers |
| `/api/cases` | GET | List cases (with optional filters) |
| `/api/cases/{id}` | GET | Get case details with timeline |
| `/api/analyze/{id}` | POST | Run sentiment analysis on a case |
| `/api/chat` | POST | Chat with the Guardian agent |
| `/api/alerts` | GET | List active alerts |

---

## 🧪 Test Cases

The seed data includes 6 test scenarios:

| Case ID | Scenario | Expected Alerts |
|---------|----------|-----------------|
| `case-001` | Happy Customer | None |
| `case-002` | Frustrated Customer | Negative sentiment |
| `case-003` | Neutral Customer | None |
| `case-004` | Declining Sentiment | Trend + 7-day breach |
| `case-005` | 7-Day Warning | Compliance warning |
| `case-006` | 7-Day Breach | Compliance breach |

**Test sentiment analysis:**
```powershell
# From the dev-box VM (via Bastion):
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/analyze/case-002" -Method POST
```

---

## 📁 Project Structure

```
csat-guardian/
├── infrastructure/
│   ├── bicep/
│   │   ├── main-commercial.bicep      # All Azure resources
│   │   └── main-commercial.bicepparam # Parameter values
│   ├── deploy-all.ps1                 # One-click deployment
│   ├── seed-database.sql              # SQL for Portal Query Editor
│   └── DEPLOYMENT_GUIDE.md            # Detailed deployment guide
├── src/
│   ├── api.py              # FastAPI REST backend
│   ├── db_sync.py          # Azure SQL client
│   ├── config.py           # Configuration
│   └── services/           # Business logic
├── docs/                   # Additional documentation
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🆘 Getting Help

If deployment fails:
1. Copy the exact error message
2. Commit any fix to GitHub from your dev machine
3. On the secure laptop: `git pull origin develop` then retry

**GitHub Repo:** https://github.com/kmonteagudo_microsoft/csat-guardian

---

## 📜 License

Internal Microsoft Use Only - CSS Escalations Team POC
