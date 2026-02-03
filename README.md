# CSAT Guardian

> **Customer Satisfaction Guardian** - AI-Powered CSAT Risk Detection and Proactive Coaching for GSX (Government Support Engineers)

---

## � Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| [**Getting Started**](docs/GETTING_STARTED.md) | **Everyone** | Start here! Overview and quick start guide |
| [File Reference](docs/FILE_REFERENCE.md) | Everyone | Complete file-by-file explanation |
| [Code Guide for Non-Developers](docs/CODE_GUIDE_FOR_NON_DEVELOPERS.md) | Non-programmers | How to read Python code |
| [Architecture](docs/ARCHITECTURE.md) | Developers | Technical deep-dive |
| [Quick Reference](docs/QUICK_REFERENCE.md) | Developers | API cheat sheet |
| [Deployment Guide](infrastructure/DEPLOYMENT_GUIDE.md) | DevOps | How to deploy |
| [Security Review](docs/APPLICATION_SECURITY_REVIEW.md) | Security | Security controls |

---

## �📋 Project Status

### ✅ Completed (Dev Environment)

| Component | Status | Details |
|-----------|--------|---------|
| **Frontend UI** | ✅ Running | **Microsoft Learn-style HTML/CSS/JS at `/ui`** |
| Azure SQL Database | ✅ Deployed | 12 tables, 8 test cases with timelines |
| App Service | ✅ Running | Python 3.11, VNet integrated, private endpoints |
| Azure OpenAI | ✅ Connected | GPT-4o via MSI authentication |
| Semantic Kernel Agent | ✅ Working | Function calling with CSAT rules plugin |
| MSI Authentication | ✅ Working | No API keys - SQL and OpenAI both use managed identity |
| `/ui` | ✅ Working | **Static frontend served by FastAPI** |
| `/api/health` | ✅ Working | Health check endpoint |
| `/api/cases` | ✅ Working | Lists cases from Azure SQL |
| `/api/analyze/{id}` | ✅ Working | Sentiment analysis (AI-powered) |
| `/api/chat` | ✅ Working | Conversational CSAT coaching |

### 🔄 Pending (For Production)

| Item | Priority | Status | Notes |
|------|----------|--------|-------|
| DfM/Kusto Integration | High | ⏳ Awaiting access | Data is in Azure Data Explorer (Kusto), not D365 OData |
| Teams Bot Integration | High | ⏳ Awaiting security approval | Need approval for Azure Function gateway |
| Directory Readers Role | Medium | ⏳ Awaiting Entra admin | SQL Server MSI needs this for least-privilege |
| CI/CD Pipeline | Low | Blocked | Network restrictions prevent GitHub Actions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Azure Commercial (Central US)                         │
│                        Subscription: a20d761d-cb36-4f83-b827-58ccdb166f39   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              VNet: vnet-csatguardian-dev (10.100.0.0/16)            │   │
│  │                                                                      │   │
│  │   ┌──────────────────┐    ┌──────────────────┐                      │   │
│  │   │ AzureBastionSubnet│    │  snet-devbox     │                      │   │
│  │   │  10.100.4.0/26   │───▶│  10.100.3.0/24   │                      │   │
│  │   │                  │    │                  │                      │   │
│  │   │  Azure Bastion   │    │  vm-devbox       │                      │   │
│  │   └──────────────────┘    │  (Windows 11)    │                      │   │
│  │                           └────────┬─────────┘                      │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │           snet-appservice (10.100.1.0/24)                    │  │   │
│  │   │                                                               │  │   │
│  │   │   ┌─────────────────────────────────────────────────────┐    │  │   │
│  │   │   │         App Service: app-csatguardian-dev           │    │  │   │
│  │   │   │         ─────────────────────────────────           │    │  │   │
│  │   │   │    FastAPI + Uvicorn (Python 3.11)                  │    │  │   │
│  │   │   │    Semantic Kernel Agent with CSAT Rules Plugin     │    │  │   │
│  │   │   │    VNet Integration Enabled                         │    │  │   │
│  │   │   └─────────────────────────────────────────────────────┘    │  │   │
│  │   └───────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │          snet-private-endpoints (10.100.2.0/24)              │  │   │
│  │   │                                                               │  │   │
│  │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │   │
│  │   │   │ Azure SQL   │  │ Key Vault   │  │ Azure OpenAI        │  │  │   │
│  │   │   │ (Private EP)│  │ (Private EP)│  │ (AI Services)       │  │  │   │
│  │   │   │             │  │             │  │                     │  │  │   │
│  │   │   │ sql-csat... │  │ kv-csatguard│  │ ais-csatguardian-dev│  │  │   │
│  │   │   └─────────────┘  └─────────────┘  └─────────────────────┘  │  │   │
│  │   └───────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │   Private DNS Zones:                                                 │   │
│  │   • privatelink.database.windows.net                                 │   │
│  │   • privatelink.vaultcore.azure.net                                  │   │
│  │   • privatelink.cognitiveservices.azure.com                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Development Environment Setup

### Understanding the Three-Machine Architecture

Due to enterprise security constraints, development spans three machines:

| Machine | Purpose | Has Access To |
|---------|---------|---------------|
| **Local Machine** | VS Code + GitHub Copilot, code editing | GitHub repo (read/write) |
| **SAW** | Azure Portal, Cloud Shell | Azure resources, GitHub repo (via Cloud Shell) |
| **Devbox VM** | Testing private endpoints | App Service, Azure SQL (via VNet) |

### Key Limitations

- **Local Machine**: No Azure CLI, no direct Azure access
- **SAW**: Azure access but no direct VNet connectivity
- **Devbox VM**: VNet access but no code editing tools
- **Cloud Shell**: Can run az commands but has MSI token scope limitations for some operations

---

## 🚀 Complete Deployment Guide

### Prerequisites

1. **Azure Subscription** with permissions to create:
   - Resource Groups, Virtual Networks, Azure SQL
   - Azure OpenAI (AI Services), Key Vault, App Service

2. **GitHub Repository** with code pushed

3. **Access to Cloud Shell** in Azure Portal

### Phase 1: Infrastructure (Already Done for Dev)

The following resources exist in `CSAT_Guardian_Dev`:

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `CSAT_Guardian_Dev` | Container for all resources |
| Virtual Network | `vnet-csatguardian-dev` | Private networking |
| App Service Plan | `asp-csatguardian-dev` | Linux P1v3 hosting |
| App Service | `app-csatguardian-dev` | Python 3.11 web app |
| SQL Server | `sql-csatguardian-dev` | Database server |
| SQL Database | `sqldb-csatguardian-dev` | Application data |
| AI Services | `ais-csatguardian-dev` | GPT-4o model |
| Key Vault | `kv-csatguard-dev` | Secrets storage |
| Bastion | `bas-csatguardian-dev` | Secure VM access |
| Dev VM | `vm-devbox-csatguardian` | Testing from VNet |

### Phase 2: Database Schema Deployment

**From Cloud Shell:**

```bash
# Set subscription
az account set --subscription a20d761d-cb36-4f83-b827-58ccdb166f39

# Navigate to repo (clone first if needed)
cd ~/csat-guardian
git pull origin develop

# Deploy schema (get password from Key Vault)
sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev \
  -U sqladmin -P '<password-from-keyvault>' \
  -i infrastructure/sql/001-schema-complete.sql

# Deploy seed data
sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev \
  -U sqladmin -P '<password-from-keyvault>' \
  -i infrastructure/sql/002-seed-data.sql
```

### Phase 3: App Service Configuration

**Required App Settings** (set in Portal → App Service → Configuration):

| Setting | Value |
|---------|-------|
| `AZURE_OPENAI_ENDPOINT` | `https://ais-csatguardian-dev.cognitiveservices.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` |
| `DATABASE_CONNECTION_STRING` | `Server=tcp:sql-csatguardian-dev.database.windows.net,1433;...` |
| `USE_SQL_MANAGED_IDENTITY` | `true` |
| `USE_OPENAI_MANAGED_IDENTITY` | `true` |
| `WEBSITE_VNET_ROUTE_ALL` | `1` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `WEBSITES_PORT` | `8000` |

**Enable SCM Basic Auth** (required for deployments):
- Portal → App Service → Configuration → General settings → SCM Basic Auth → **On**

### Phase 4: Code Deployment (The Working Method)

⚠️ **Important**: Standard `az webapp up` and `az webapp deployment source sync` do NOT work reliably. Use the Kudu file upload method:

**Step 1: Create deployment ZIP (Cloud Shell)**
```bash
cd ~/csat-guardian
git pull origin develop
rm -f deploy.zip
zip -r deploy.zip src requirements.txt
download deploy.zip
```

**Step 2: Upload via Kudu (SAW Browser)**
1. Go to: `https://app-csatguardian-dev.scm.azurewebsites.net/DebugConsole`
2. Navigate to `/home`
3. Drag and drop `deploy.zip` into the file area

**Step 3: Move files to wwwroot (Kudu SSH)**
```bash
cd /home/site/wwwroot
rm -rf src requirements.txt
mv /home/src .
mv /home/requirements.txt .
```

**Step 4: Set startup command (Portal)**
```
cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Step 5: Restart App Service**

### Phase 5: Verification (From Devbox VM)

Connect via Bastion, then test:
```powershell
# Health check
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"

# List cases
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/cases"

# Chat with agent
$body = @{ message = "Check CSAT rules for case-001"; engineer_id = "eng-001" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/chat" -Method POST -ContentType "application/json" -Body $body
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health status |
| `/api/cases` | GET | List cases (with filters) |
| `/api/cases/{id}` | GET | Get case with timeline |
| `/api/analyze/{id}` | POST | AI sentiment analysis |
| `/api/chat` | POST | Chat with CSAT Guardian agent |

---

## 📁 Project Structure

```
csat-guardian/
├── src/
│   ├── api.py                    # FastAPI REST endpoints + static serving
│   ├── config.py                 # Configuration management
│   ├── db_sync.py                # Azure SQL sync client
│   ├── models.py                 # Pydantic data models
│   ├── static/                   # ** FRONTEND UI **
│   │   ├── index.html            # Microsoft Learn-style HTML
│   │   ├── css/styles.css        # Fluent Design CSS
│   │   └── js/app.js             # Frontend JavaScript
│   ├── agent/
│   │   ├── guardian_agent.py     # Semantic Kernel agent
│   │   └── csat_rules_plugin.py  # CSAT rules function plugin
│   ├── services/
│   │   ├── sentiment_service.py  # Azure OpenAI sentiment analysis
│   │   └── alert_service.py      # Alert generation
│   └── clients/
│       └── dfm_client.py         # DfM API client (async)
├── infrastructure/
│   ├── bicep/                    # Azure IaC templates
│   ├── sql/
│   │   ├── 001-schema-complete.sql  # Database schema
│   │   └── 002-seed-data.sql        # Test data (8 cases)
│   └── DEPLOYMENT_GUIDE.md
├── docs/
│   └── ARCHITECTURE.md
└── README.md
```

---

## 🧪 Test Cases

| Case ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| `case-001` | Happy customer | Good communication, no violations |
| `case-002` | Frustrated customer | Negative sentiment detected |
| `case-003` | Neutral progress | Steady engagement |
| `case-004` | Declining sentiment | Trend analysis alerts |
| `case-005` | 7-day warning | Approaching compliance breach |
| `case-006` | 7-day breach | Compliance violation |
| `case-007` | Technical complexity | Complex troubleshooting |
| `case-008` | Escalation scenario | Multi-team involvement |

---

## 🔐 Credentials

| Resource | Username | Notes |
|----------|----------|-------|
| SQL Admin | `sqladmin` | Password stored in Key Vault |
| Devbox VM | `testadmin` | Password stored in Key Vault |
| Azure OpenAI Key | - | Key Vault secret: `azure-openai-key` |

---

## 🔧 Troubleshooting

### App returns 500 errors
- Check Portal → App Service → Log stream
- Or Kudu: `https://app-csatguardian-dev.scm.azurewebsites.net/api/logstream`

### "No module named uvicorn"
Ensure startup command includes `pip install -r requirements.txt`

### SQL connection fails
- Verify `WEBSITE_VNET_ROUTE_ALL=1`
- Check Private DNS zone linked to VNet
- Restart App Service

### Chat endpoint returns error
- Check `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` settings
- Verify Key Vault access for managed identity

---

## 📈 Known Deployment Issues & Workarounds

| Issue | Workaround |
|-------|------------|
| `az webapp up` fails | Use Kudu file upload method |
| `az webapp deployment source sync` caches old code | Use Kudu file upload method |
| Cloud Shell MSI token scope errors | Upload files via Kudu manually |

---

## 🔮 Future Enhancements

1. **DfM Integration**: Replace seed data with real case sync
2. **Teams Notifications**: Alert managers on CSAT risks
3. **CI/CD Pipeline**: GitHub Actions for automated deployment
4. **Real-time Updates**: WebSocket for live dashboard refresh

---

## 📜 License

Internal Microsoft Use Only
