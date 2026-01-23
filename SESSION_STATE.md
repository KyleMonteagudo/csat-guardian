# CSAT Guardian - Session State

> **Last Updated**: January 23, 2026
> **Status**: ✅ Ready for Deployment to Commercial Azure

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
   - All endpoints working with Azure SQL and Azure OpenAI
   - Swagger docs at `/docs`

2. **Azure SQL Integration**
   - `src/db_sync.py` - Synchronous SQL client
   - `src/clients/azure_sql_adapter.py` - Async wrapper

3. **Azure OpenAI Sentiment Analysis**
   - Real GPT-4o integration
   - `src/services/sentiment_service.py`

4. **Infrastructure as Code**
   - `infrastructure/bicep/main-commercial.bicep` - Complete template
   - Deploys: VNet, Bastion, Dev-box VM, SQL, OpenAI, Key Vault, App Service
   - All backend services use Private Endpoints (no public access)

5. **Deployment Script**
   - `infrastructure/deploy-all.ps1` - One-command deployment
   - Handles infra, database seeding, and app deployment

6. **Documentation** - Clean and updated for Commercial Azure

### ⏳ Next Steps

1. **Deploy to Azure** - Run `deploy-all.ps1 -SkipDatabase` from locked-down PC
2. **Seed Database** - Use Azure Portal Query Editor with `seed-database.sql`
3. **Test via Bastion** - Connect to dev-box VM and verify endpoints

---

## Deployment Info

**Target Environment:**
- Cloud: Commercial Azure (East US)
- Subscription: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `KMonteagudo_CSAT_Guardian`

**Key Resources:**
| Resource | Name |
|----------|------|
| App Service | `app-csatguardian-dev.azurewebsites.net` |
| SQL Server | `sql-csatguardian-dev.database.windows.net` |
| Azure OpenAI | `oai-csatguardian-dev.openai.azure.com` |
| Key Vault | `kv-csatguardian-dev.vault.azure.net` |
| Bastion | `bas-csatguardian-dev` |
| Dev-box VM | `vm-devbox-csatguardian` (testadmin/Password1!) |

**Network:**
- VNet: 10.100.0.0/16
- All backend services: Private Endpoints only (no public access)
- Access via Bastion → Dev-box VM

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
│   ├── seed-database.sql   # SQL for Azure Portal
│   └── DEPLOYMENT_GUIDE.md # Step-by-step guide
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md               # Project overview
```

---

## Commands

**Deploy everything:**
```powershell
cd infrastructure
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipDatabase
```

**Redeploy code only:**
```powershell
.\deploy-all.ps1 -SqlPassword "YourSecurePassword123!" -SkipInfrastructure -SkipDatabase
```

**Local development:**
```powershell
cd src
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```
