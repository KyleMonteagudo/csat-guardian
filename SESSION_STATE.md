# CSAT Guardian - Session State

> **Last Updated**: January 24, 2026
> **Status**: ✅ Deployed to Commercial Azure (Central US)

---

## Quick Context for AI Assistant

```
Read the SESSION_STATE.md file in the csat-guardian project to understand the current state.
```

---

## Current State

### ✅ Completed

1. **FastAPI Backend** - Production-ready REST API
   - File: `src/api.py`
   - All endpoints working with Azure SQL and Azure AI Services
   - Swagger docs at `/docs`

2. **Azure SQL Integration**
   - `src/db_sync.py` - Synchronous SQL client
   - `src/clients/azure_sql_adapter.py` - Async wrapper
   - Database seeded with test cases

3. **Azure AI Services Sentiment Analysis**
   - AI Foundry (AI Hub + AI Services) with GPT-4o deployment
   - `src/services/sentiment_service.py`

4. **Infrastructure as Code**
   - `infrastructure/bicep/main-commercial.bicep` - Complete template
   - Deploys: VNet, Bastion, Dev-box VM, SQL, AI Hub, AI Services, Key Vault, App Service
   - All backend services use Private Endpoints (no public access)

5. **Deployed to Azure**
   - App Service deployed via `az webapp up`
   - Database seeded via Cloud Shell sqlcmd
   - Key Vault secrets configured

6. **Documentation** - Updated for Commercial Azure (Central US)

### ⏳ Next Steps (Development Backlog)

1. **VNet Integration** - Enable App Service VNet integration to reach private endpoints
2. **Real AI Integration** - Test sentiment analysis with AI Services endpoint
3. **DfM Integration** - Build real Dynamics Field Management client
4. **Teams Notifications** - Webhook setup for alert delivery
5. **Dashboard UI** - Streamlit or React frontend
6. **Authentication** - Azure AD integration

---

## Deployment Info

**Target Environment:**
- Cloud: Commercial Azure (Central US)
- Subscription: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `CSAT_Guardian_Dev`

**Key Resources:**
| Resource | Name |
|----------|------|
| App Service | `app-csatguardian-dev.azurewebsites.net` |
| App Service Plan | `asp-csatguardian-dev` |
| SQL Server | `sql-csatguardian-dev.database.windows.net` |
| SQL Database | `sqldb-csatguardian-dev` |
| AI Services | `ais-csatguardian-dev` |
| AI Hub | `aihub-csatguardian-dev` |
| Key Vault | `kv-csatguard-dev` (note: shorter name due to soft-delete conflict) |
| Bastion | `bas-csatguardian-dev` |
| Dev-box VM | `vm-devbox-csatguardian` (testadmin/Password1!) |
| VNet | `vnet-csatguardian-dev` |

**Key Vault Secrets:**
| Secret | Description |
|--------|-------------|
| `SqlServer--ConnectionString` | Azure SQL connection string |
| `AzureOpenAI--ApiKey` | AI Services API key |
| `AzureOpenAI--Endpoint` | AI Services endpoint URL |

**Network:**
- VNet: 10.100.0.0/16 (Central US)
- All backend services: Private Endpoints
- Access via Bastion → Dev-box VM

---

## Development Workflow

**Local Development:**
```powershell
cd src
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Deploy to Azure (via Cloud Shell):**
```bash
cd ~/csat-guardian
git pull
cd src
az webapp up --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --runtime "PYTHON:3.11"
```

---

## File Structure

```
csat-guardian/
├── src/                    # Python source code
│   ├── api.py              # FastAPI backend
│   ├── config.py           # Configuration
│   ├── db_sync.py          # Azure SQL client
│   └── services/           # Business logic
├── infrastructure/
│   ├── bicep/              # IaC templates
│   ├── deploy-all.ps1      # Deployment script
│   ├── seed-database.sql   # SQL for database seeding
│   └── DEPLOYMENT_GUIDE.md # Step-by-step guide
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md               # Project overview
```
