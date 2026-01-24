# CSAT Guardian

> **Customer Satisfaction Guardian** - Proactive CSAT Risk Detection and Intervention

---

## 🚀 Current Deployment Status

✅ **Deployed to Commercial Azure (Central US)**

| Resource | Name | Status |
|----------|------|--------|
| Resource Group | `CSAT_Guardian_Dev` | ✅ Active |
| App Service | `app-csatguardian-dev` | ✅ Running |
| SQL Database | `sqldb-csatguardian-dev` | ✅ Seeded |
| AI Services | `ais-csatguardian-dev` | ✅ Deployed |
| Key Vault | `kv-csatguard-dev` | ✅ Configured |
| Bastion | `bas-csatguardian-dev` | ✅ Ready |

---

## 🛠️ Development Workflow

### Local Development

```powershell
cd csat-guardian\src
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Then open: http://localhost:8000/docs

### Deploy to Azure

1. **Push changes to GitHub:**
   ```powershell
   git add -A
   git commit -m "Your change description"
   git push origin develop
   ```

2. **In Azure Cloud Shell:**
   ```bash
   cd ~/csat-guardian
   git pull
   cd src
   az webapp up --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --runtime "PYTHON:3.11"
   ```

---

## 🏗️ Architecture

```
Azure Commercial (Central US)
└── CSAT_Guardian_Dev
    ├── VNet: vnet-csatguardian-dev (10.100.0.0/16)
    │   ├── snet-app (10.100.1.0/24) - App Service
    │   ├── snet-private (10.100.2.0/24) - Private Endpoints
    │   ├── snet-devbox (10.100.3.0/24) - Dev VM
    │   └── AzureBastionSubnet (10.100.4.0/26) - Bastion
    │
    ├── Azure Bastion - Secure RDP access (no public IPs)
    ├── Dev-box VM - Windows 11 for testing
    │
    ├── App Service - FastAPI backend (Python 3.11)
    │
    ├── Azure SQL - Private endpoint only
    ├── Azure AI Services - gpt-4o model, private endpoint
    └── Key Vault - Stores all secrets
```

---

## 📡 API Endpoints

Access Swagger docs at: `https://app-csatguardian-dev.azurewebsites.net/docs`

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

---

## 🔐 Credentials Reference

| Resource | Username | Password |
|----------|----------|----------|
| SQL Admin | `sqladmin` | (stored in Key Vault) |
| Dev-box VM | `testadmin` | `Password1!` |

---

## 📁 Project Structure

```
csat-guardian/
├── src/
│   ├── api.py              # FastAPI REST backend
│   ├── db_sync.py          # Azure SQL client
│   ├── config.py           # Configuration
│   ├── services/           # Business logic
│   ├── clients/            # External service clients
│   └── agent/              # AI Agent
├── infrastructure/
│   ├── bicep/              # IaC templates
│   ├── deploy-all.ps1      # Deployment script
│   └── seed-database.sql   # Database seed data
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔗 Key Resources

| Resource | Name | Access |
|----------|------|--------|
| **App Service** | `app-csatguardian-dev` | `https://app-csatguardian-dev.azurewebsites.net` |
| **SQL Server** | `sql-csatguardian-dev` | Private endpoint only |
| **AI Services** | `ais-csatguardian-dev` | Private endpoint only |
| **Key Vault** | `kv-csatguard-dev` | Private endpoint only |
| **Bastion** | `bas-csatguardian-dev` | Portal → VM → Connect → Bastion |
| **Dev-box VM** | `vm-devbox-csatguardian` | Access via Bastion |

---

## 📋 Troubleshooting

### "App Service returns 500 error"

Check logs in Kudu:
1. Azure Portal → `app-csatguardian-dev` → **Advanced Tools** → **Go**
2. Click **Debug console** → **CMD**
3. Navigate to `LogFiles` and check `docker/*.log`

### Need to redeploy the app

In Cloud Shell:
```bash
cd ~/csat-guardian
git pull
cd src
az webapp up --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --runtime "PYTHON:3.11"
```

### SQL connection issues

SQL Server only accepts connections from within the VNet. Use:
- Dev-box VM (via Bastion), OR
- Cloud Shell with `sqlcmd`

---

## 📜 License

Internal Microsoft Use Only - CSS Escalations Team POC
