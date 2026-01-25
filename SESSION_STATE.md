# CSAT Guardian - Session State

> **Last Updated**: January 25, 2026
> **Status**: ⚠️ ON HOLD - Security Remediation Required

---

## Quick Context for AI Assistant

```
Read the SESSION_STATE.md file in the csat-guardian project to understand the current state.
```

---

## 🚨 CRITICAL: Security Breaking Changes (January 25, 2026)

The following security hardening changes have been applied to comply with enterprise guardrails.
**The application is currently non-functional until code changes are made to support Managed Identity authentication.**

### Security Changes Applied

| # | Resource | Change | Impact |
|---|----------|--------|--------|
| 1 | **Key Vault** | Disabled public network access | App may not resolve `@Microsoft.KeyVault(...)` references |
| 2 | **Bastion + Public IP** | Deleted | No way to access Devbox VM for testing |
| 3 | **AI Services** (`ais-csatguardian-dev`) | Disabled local auth | API key authentication stops working |
| 4 | **OpenAI** (`oai-csatguardian-dev`) | Disabled local auth | API key authentication stops working |
| 5 | **Azure SQL** | AD-only auth enabled | SQL username/password stops working |
| 6 | **Storage Account** | Disable shared key access | Shared key access stops working |
| 7 | **Storage Account** | Disable SFTP/Local Users | SFTP local user access stops |

### Code Changes Required to Remediate

| Component | Current Auth | Required Auth |
|-----------|-------------|---------------|
| Azure OpenAI | API Key from Key Vault | `DefaultAzureCredential` (MSI) |
| Azure SQL | Connection string with password | Access token from MSI |
| Key Vault | App setting reference | Code-based access with MSI (if PE issues) |
| Storage | Shared key (if used) | MSI + RBAC |

### Azure RBAC/Permissions Required

| Resource | Principal | Role/Permission |
|----------|-----------|-----------------|
| AI Services | App Service MSI | `Cognitive Services User` |
| SQL Database | App Service MSI | `db_datareader`, `db_datawriter` (via T-SQL) |
| Key Vault | App Service MSI | `Key Vault Secrets User` (already configured) |
| Storage Account | App Service MSI | `Storage Blob Data Contributor` (if needed) |

### SQL Database Setup Required

Run as Azure AD admin (Kyle Monteagudo):
```sql
CREATE USER [app-csatguardian-dev] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [app-csatguardian-dev];
ALTER ROLE db_datawriter ADD MEMBER [app-csatguardian-dev];
```

---

## Current State

### ✅ Completed (Production-Ready POC - Pre-Security Hardening)

1. **FastAPI Backend** - Production-ready REST API
   - File: `src/api.py`
   - All endpoints working with Azure SQL and Azure AI Services
   - Swagger docs at `/docs`

2. **Azure SQL Integration**
   - `src/db_sync.py` - Synchronous SQL client (per-query connections for thread safety)
   - `src/clients/azure_sql_adapter.py` - Async wrapper
   - Database seeded with 8 test cases and timeline data

3. **AI-Powered Analysis**
   - **Sentiment Analysis**: GPT-4o powered sentiment scoring (0-1 scale)
   - **Timeline Analysis**: Detects communication gaps and patterns
   - **CSAT Rules Engine**: Semantic Kernel agent with function calling
   - **Coaching Recommendations**: AI-generated actionable advice

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
| Jan 25 | Security hardening | Disabled local auth on AI Services, SQL, Storage |
| Jan 25 | Database concurrency | Changed to per-query connections to fix "Connection is busy" errors |
| Jan 25 | Agent analysis | Full sentiment, timeline, and coaching now working in production |
| Jan 24 | Deployment method | Documented Kudu drag-drop as working approach |

### ⏳ Next Steps (Blocked Until Security Remediation Complete)

1. **🔴 BLOCKED: MSI Auth Migration** - Update code to use DefaultAzureCredential
2. **🔴 BLOCKED: Grant MSI Permissions** - RBAC roles for AI Services, SQL user creation
3. **DfM Integration** - Replace seed data with real Dynamics case sync
4. **Teams Notifications** - Webhook alerts for managers on CSAT risks
5. **CI/CD Pipeline** - GitHub Actions for automated Kudu deployment
6. **User Authentication** - Azure AD integration for API access

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
