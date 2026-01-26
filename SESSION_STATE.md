# CSAT Guardian - Session State

> **Last Updated**: January 26, 2026 (10:30 PM)
> **Status**: ✅ MSI Auth Migration Complete - Deployed & Verified Working

---

## Quick Context for AI Assistant

```
Read the SESSION_STATE.md file in the csat-guardian project to understand the current state.
```

---

## 🎉 MILESTONE: MSI Authentication Working (January 26, 2026)

**All services are now authenticating via Managed Identity:**

| Service | Status | Auth Method |
|---------|--------|-------------|
| Azure SQL | ✅ Working | MSI token via `DefaultAzureCredential` |
| Azure OpenAI | ✅ Working | MSI token via `get_bearer_token_provider` |
| Key Vault | ✅ Working | `@Microsoft.KeyVault` references with MSI |
| API Health | ✅ Working | All services reporting "healthy" |

### Key Finding: Directory Readers Workaround

**Root Cause**: Azure SQL Server MSI (`04199892-389c-4531-97a7-42eda6734c28`) does not have Directory Readers role in Azure AD, which is required to validate incoming AAD tokens from non-admin users.

**Current Workaround**: Made App Service MSI (`7b0f0d42-0f23-48cd-b982-41abad5f1927`) a SQL Server admin. This bypasses the Directory Readers requirement.

**Production Fix**: Request AAD admin to grant Directory Readers role to SQL Server MSI, then demote App Service to database user with least privilege.

---

## Security Configuration Summary

### Security Hardening Applied (January 25, 2026)

| # | Resource | Change | Status |
|---|----------|--------|--------|
| 1 | **Key Vault** | Disabled public network access | ✅ Working via PE |
| 2 | **Bastion + Public IP** | Deleted | N/A - use VM run-command |
| 3 | **AI Services** | Disabled local auth | ✅ MSI working |
| 4 | **Azure SQL** | AD-only auth enabled | ✅ MSI working |
| 5 | **Storage Account** | Disabled shared key access | N/A |

### MSI Authentication Implementation

| File | Changes |
|------|---------|
| `src/config.py` | Added `use_managed_identity` flag to `AzureOpenAIConfig`, `use_sql_managed_identity` to `FeatureFlags` |
| `src/db_sync.py` | Added `_get_msi_access_token()` using `DefaultAzureCredential` with struct-packed token |
| `src/services/sentiment_service.py` | Uses `get_bearer_token_provider()` for Azure OpenAI |
| `src/agent/guardian_agent.py` | Uses `ad_token_provider` for Semantic Kernel |
| `requirements.txt` | Added `pyodbc>=5.0.0` |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_OPENAI_MANAGED_IDENTITY` | `true` | MSI for Azure OpenAI |
| `USE_SQL_MANAGED_IDENTITY` | `true` | MSI for Azure SQL |

### Azure RBAC Configuration

| Resource | Principal | Role/Permission | Status |
|----------|-----------|-----------------|--------|
| SQL Server | App Service MSI | **SQL Admin** (workaround) | ✅ Configured |
| AI Services | App Service MSI | `Cognitive Services User` | ✅ Configured |
| Key Vault | App Service MSI | `Key Vault Secrets User` | ✅ Configured |

---

## Current State

### ✅ Completed Features

1. **FastAPI Backend** - Production-ready REST API (`src/api.py`)
2. **Azure SQL Integration** - Thread-safe per-query connections with MSI auth
3. **AI-Powered Analysis** - GPT-4o sentiment, timeline analysis, coaching
4. **Semantic Kernel Agent** - Function-calling conversational agent
5. **MSI Authentication** - No API keys or passwords in code/config
6. **Private Networking** - All services via Private Endpoints

### ✅ Recent Changes (January 26, 2026)

| Change | Details |
|--------|---------|
| MSI auth for Azure SQL | Token-based auth via `DefaultAzureCredential` |
| MSI auth for Azure OpenAI | `get_bearer_token_provider()` and `ad_token_provider` |
| SQL Admin workaround | App Service MSI set as SQL admin (Directory Readers unavailable) |
| Debug endpoints | Added `/api/debug/msi-token` and `/api/debug/sql-users` for troubleshooting |
| Health endpoint fix | Restored missing return statement |

### ⏳ Next Steps (Priority Order)

1. **Production Fix: Directory Readers**
   - Request AAD admin to grant Directory Readers to SQL Server MSI
   - Demote App Service from SQL admin to db_datareader/db_datawriter
   
2. **Clean Up Debug Endpoints**
   - Remove `/api/debug/msi-token` and `/api/debug/sql-users` before production

3. **DfM Integration**
   - Replace seed data with real Dynamics for Microsoft case sync
   
4. **Teams Notifications**
   - Webhook alerts for managers on CSAT risks

5. **CI/CD Pipeline**
   - GitHub Actions for automated deployment

6. **User Authentication**
   - Azure AD integration for API access

---

## Deployment Info

**Target Environment:**
- Cloud: Commercial Azure (Central US)
- Subscription: `a20d761d-cb36-4f83-b827-58ccdb166f39`
- Resource Group: `CSAT_Guardian_Dev`

**Key Resources:**

| Resource | Name | Notes |
|----------|------|-------|
| App Service | `app-csatguardian-dev` | MSI: `7b0f0d42-0f23-48cd-b982-41abad5f1927` |
| SQL Server | `sql-csatguardian-dev` | MSI: `04199892-389c-4531-97a7-42eda6734c28`, AD Admin: App Service |
| SQL Database | `sqldb-csatguardian-dev` | Contains external user `app-csatguardian-dev` |
| AI Services | `ais-csatguardian-dev` | GPT-4o deployment |
| Key Vault | `kv-csatguard-dev` | Private endpoint only |
| VNet | `vnet-csatguardian-dev` | 10.100.0.0/16 |
| Dev VM | `vm-devbox-csatguardian` | MSI: `2941775d-fe8f-4ebd-88ef-6852df0eb43b` (former SQL admin) |

**Testing Access:**
- No Bastion (deleted for security)
- Use `az vm run-command invoke` to test via VM
- Or access via Cloud Shell → Kudu console

---

## Development Workflow

**Local Development (API Keys):**
```powershell
$env:USE_SQL_MANAGED_IDENTITY = "false"
$env:USE_OPENAI_MANAGED_IDENTITY = "false"
cd src
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Deploy to Azure (Kudu Method):**
```bash
# Cloud Shell
cd ~/csat-guardian && git pull origin develop
rm -f deploy.zip && zip -r deploy.zip src requirements.txt
# Upload via https://app-csatguardian-dev.scm.azurewebsites.net/ZipDeployUI
az webapp restart --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev
```

**Test via VM:**
```bash
az vm run-command invoke \
    --resource-group CSAT_Guardian_Dev \
    --name vm-devbox-csatguardian \
    --command-id RunPowerShellScript \
    --scripts "Invoke-WebRequest -Uri 'https://app-csatguardian-dev.azurewebsites.net/api/health' -UseBasicParsing | Select-Object -ExpandProperty Content"
```

4. **Infrastructure as Code**
   - `infrastructure/bicep/main-commercial.bicep` - Complete template
   - ⚠️ **Note**: Bicep template does NOT reflect current security state - manual changes were made
   - Deploys: VNet, ~~Bastion~~, ~~Dev-box VM~~, SQL, AI Hub, AI Services, Key Vault, App Service
   - All backend services use Private Endpoints (no public access)

5. **Deployed to Azure**
   - App Service running with VNet integration
   - Database accessible via private endpoint
   - Key Vault secrets auto-resolved via managed identity
   - **Deployment method**: Kudu drag-and-drop (standard az commands have MSI scope issues)

6. **Documentation** - Comprehensive guides for deployment, architecture, and troubleshooting

### ✅ Recent Fixes (January 2026)

| Date | Fix | Details |
|------|-----|---------|
| Jan 26 | **MSI Auth Migration** | Updated code to use `DefaultAzureCredential` for Azure OpenAI and SQL |
| Jan 25 | Security hardening | Disabled local auth on AI Services, SQL, Storage |
| Jan 25 | Database concurrency | Changed to per-query connections to fix "Connection is busy" errors |
| Jan 25 | Agent analysis | Full sentiment, timeline, and coaching now working in production |
| Jan 24 | Deployment method | Documented Kudu drag-drop as working approach |

### ⏳ Next Steps

1. **✅ DONE: MSI Auth Migration** - Code updated to use `DefaultAzureCredential`
2. **🔴 BLOCKING: Grant MSI Permissions** - RBAC roles for AI Services, SQL user creation
3. **🔴 BLOCKING: Deploy & Test** - Redeploy to App Service and verify MSI auth works
4. **DfM Integration** - Replace seed data with real Dynamics case sync
5. **Teams Notifications** - Webhook alerts for managers on CSAT risks
6. **CI/CD Pipeline** - GitHub Actions for automated Kudu deployment
7. **User Authentication** - Azure AD integration for API access

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
| Dev-box VM | `vm-devbox-csatguardian` |
| VNet | `vnet-csatguardian-dev` |

**Key Vault Secrets:**
| Secret | Description |
|--------|-------------|
| `azure-openai-key` | AI Services API key |
| `sql-admin-password` | Azure SQL admin password |
| `devbox-password` | Dev-box VM password |

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

**Deploy to Azure (Kudu Method - Working):**
```bash
# Cloud Shell
cd ~/csat-guardian && git pull origin develop
rm -f deploy.zip && zip -r deploy.zip src requirements.txt
download deploy.zip

# Then in browser:
# 1. Go to https://app-csatguardian-dev.scm.azurewebsites.net/DebugConsole
# 2. Drag-drop deploy.zip to /home
# 3. In SSH: cd /home/site/wwwroot && rm -rf src requirements.txt && mv /home/src . && mv /home/requirements.txt .
# 4. Restart App Service
```

---

## File Structure

```
csat-guardian/
├── src/                    # Python source code
│   ├── api.py              # FastAPI backend
│   ├── config.py           # Configuration
│   ├── db_sync.py          # Azure SQL client (per-query connections)
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
