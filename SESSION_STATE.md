# CSAT Guardian - Session State

> **Last Updated**: February 5, 2026
> **Status**: ✅ ALL SYSTEMS HEALTHY | ✅ ULTRA PREMIUM UI Complete | ⏳ Waiting on DfM/Kusto Access

---

## Quick Context for AI Assistant

**READ THIS FIRST** - This file contains everything you need to continue work on this project.

```
The CSAT Guardian project is FULLY FUNCTIONAL in dev environment.
All services healthy. All bugs fixed. ULTRA PREMIUM UI deployed.
Features: Mobile responsive, Filtering/Search, Export (CSV/PDF/JSON), Particle effects
Next work: DfM/Kusto integration (awaiting external access).
Built with Claude Opus 4.5 🚀
```

---

## 🎨 MILESTONE: ULTRA PREMIUM UI Complete (February 5, 2026)

**Implemented jaw-dropping visual upgrades + new features:**

### New User Features
| Feature | Description |
|---------|-------------|
| **Mobile Responsive** | Full mobile-first design with hamburger menu |
| **Slide-Out Menu** | Touch-friendly navigation with swipe-to-close |
| **Case Filtering** | Filter by severity, sentiment, days inactive, text search |
| **Quick Filter Pills** | One-click Critical/At-Risk/Healthy filters |
| **Export to CSV** | Download case data for Excel/Sheets |
| **Export to PDF** | Executive summary report with print dialog |
| **Export to JSON** | Raw data export for integration |

### Visual WOW Effects
| Feature | Description |
|---------|-------------|
| **Particle Canvas** | Animated network of interconnected particles |
| **Aurora Background** | Morphing gradient blob animations |
| **Glassmorphism** | Enhanced frosted glass with deeper blur |
| **Animated Sentiment Rings** | SVG circular progress with gradients |
| **Gradient Text Animation** | Color-shifting animated titles |
| **Neon Border Effects** | Glowing borders on card hover |
| **3D Card Transforms** | Perspective-based tilt effects |
| **Confetti Celebration** | Success animation on exports |
| **Animated Counters** | Numbers count up with easing |
| **Skeleton Loading** | Shimmer placeholders |
| **Page Transitions** | Staggered fade-in-up animations |

### Mobile/Touch Optimizations
- 44px minimum touch targets
- No zoom on input focus (16px font)
- Safe area insets for notched phones
- Swipe gestures for mobile menu
- Print-optimized styles

**File Stats:**
- `src/static/css/styles.css`: ~4,500 lines
- `src/static/js/app.js`: ~3,600 lines
- `src/static/index.html`: ~180 lines

**Git Configuration:**
- `origin` remote pushes to BOTH repositories
- `git push origin main` deploys to KyleMonteagudo AND kmonteagudo_microsoft repos

---

## 🎨 Previous: UI Enhancements (February 5, 2026 - Earlier)

**Implemented stunning visual upgrades for hackathon demo:**

| Feature | Description |
|---------|-------------|
| **Glassmorphism** | Frosted glass cards with `backdrop-filter: blur(12px)` |
| **Animated Sentiment Rings** | SVG circular progress indicators with gradient fills |
| **Animated Counters** | Numbers count up with easing on dashboard load |
| **Skeleton Loading** | Shimmer placeholders while API calls complete |
| **Micro-interactions** | Button ripples, card hover lifts, focus states |
| **Gradient Accents** | Dynamic gradients on metrics, buttons, titles |
| **Page Transitions** | Staggered fade-in-up animations on view changes |

---

## 📚 MILESTONE: Enterprise Documentation Complete (January 28, 2026)

**Created comprehensive documentation suite (~2,800 lines):**

| Document | Lines | Purpose |
|----------|-------|---------|
| `docs/FILE_REFERENCE.md` | ~850 | Complete file-by-file project reference |
| `docs/GETTING_STARTED.md` | ~250 | Entry point for newcomers |
| `docs/CODE_GUIDE_FOR_NON_DEVELOPERS.md` | ~500 | Python explained for non-programmers |
| `README.md` | Updated | Added documentation table |

**Committed**: `a23ed92` on develop, merged to main as `eb1805a`

---

## 🐛 BUGS FIXED (January 28, 2026)

### 1. Content Safety Boolean Bug
**File**: `src/services/privacy.py` (line ~467)
**Problem**: `use_content_safety` returned the endpoint string instead of True/False
**Fix**: Changed from `config.content_safety.endpoint` to `bool(config.content_safety.endpoint)`

### 2. CasePriority → CaseSeverity Migration
**Files**: `src/db_sync.py`, `src/sample_data_rich.py`
**Problem**: Code still referenced old `CasePriority` enum that was renamed to `CaseSeverity`
**Fix**: Updated all imports and usages to `CaseSeverity`

### 3. Duplicate requirements.txt
**Problem**: Two requirements.txt files (root and src/) causing confusion
**Fix**: Deleted root `requirements.txt`, consolidated to `src/requirements.txt` only
**Added**: `azure-ai-contentsafety>=1.0.0` to src/requirements.txt

### 4. Deployment Guide Updates
**File**: `infrastructure/DEPLOYMENT_GUIDE.md`
**Fix**: Updated deployment commands for new file structure (src/requirements.txt)

---

## 🎉 MILESTONE: Azure AI Content Safety Enabled (January 28, 2026)

**Two-layer PII protection now active:**

| Layer | What It Catches | Latency |
|-------|-----------------|---------|
| **Regex Scrubbing** | Emails, phones, SSNs, IPs, credit cards | ~0ms |
| **Content Safety** | Names, addresses, contextual PII | +100-300ms |

**Configuration:**
- Endpoint: `https://csatguardcs.cognitiveservices.azure.com/`
- Auth: Managed Identity (App Service MSI)
- Enabled via: `ENABLE_CONTENT_SAFETY_PII=true` (set in App Service config)

**Verified Working**: `/api/test-pii` endpoint confirms both layers active

---

## 🎉 MILESTONE: MSI Authentication Working (January 26, 2026)

**All services are now authenticating via Managed Identity:**

| Service | Status | Auth Method |
|---------|--------|-------------|
| Azure SQL | ✅ Working | MSI token via `DefaultAzureCredential` |
| Azure OpenAI | ✅ Working | MSI token via `get_bearer_token_provider` |
| Key Vault | ✅ Working | `@Microsoft.KeyVault` references with MSI |
| Content Safety | ✅ Working | MSI via `DefaultAzureCredential` |
| API Health | ✅ Working | All services reporting "healthy" |

### Key Finding: Directory Readers Workaround

**Root Cause**: Azure SQL Server MSI (`04199892-389c-4531-97a7-42eda6734c28`) does not have Directory Readers role in Azure AD, which is required to validate incoming AAD tokens from non-admin users.

**Current Workaround**: Made App Service MSI (`7b0f0d42-0f23-48cd-b982-41abad5f1927`) a SQL Server admin. This bypasses the Directory Readers requirement.

**Production Fix**: Request AAD admin to grant Directory Readers role to SQL Server MSI, then demote App Service to database user with least privilege.

---

## 🔄 KEY UPDATE: DfM Data via Azure Data Explorer (January 27, 2026)

**Important Discovery**: DfM case data for Azure Gov is stored in **Azure Data Explorer (Kusto)**, not via D365 OData APIs.

**What This Means**:
- Need to query Kusto directly using `azure-kusto-data` SDK
- Requires **user-assigned managed identity** specifically for ADX access
- App Service already has an Enterprise Application (`app-csatguardian-dev`) that can be used

**Information Still Needed from DfM/Kusto Team**:
- ADX Cluster URL (e.g., `https://dfmgov.kusto.windows.net`)
- Database name
- Table names and schema
- MSI granted Viewer access to the database

---

## ⏳ Pending Approvals / External Dependencies

| Item | Owner | Status | Notes |
|------|-------|--------|-------|
| **DfM/Kusto Access** | DfM Team | ⏳ Request submitted | Need cluster URL, database, tables, MSI access granted |
| **Teams Bot Security** | Security Lead | ⏳ Email sent Jan 26 | Need approval for public bot endpoint (Azure Function gateway) |
| **Directory Readers Role** | Entra Admin | ⏳ Low priority | SQL Server MSI needs this (workaround in place) |

---

## Code Changes Made (January 26-27, 2026)

| Change | Files | Details |
|--------|-------|---------|
| MSI auth for Azure SQL | `db_sync.py` | Token-based auth via `DefaultAzureCredential` |
| MSI auth for Azure OpenAI | `sentiment_service.py`, `guardian_agent.py` | `get_bearer_token_provider()` and `ad_token_provider` |
| Renamed priority → severity | `models.py`, `api.py`, `dfm_client.py` | Now uses Sev A/B/C/D to match DfM terminology |
| Debug endpoints removed | `api.py` | Cleaned up `/api/debug/*` endpoints |
| Health endpoint fix | `api.py` | Restored missing return statement |
| DfM request doc | `docs/DFM_INTEGRATION_REQUEST.md` | Formal request for DfM team |

---

## Teams Bot Integration Plan

**Why Azure Bot Service is Required:**
- Teams doesn't allow direct messaging to users
- Bot Service acts as intermediary: Teams → Bot Service → Your endpoint
- Bot Service must be able to reach your endpoint (requires public URL)

**Recommended Architecture: Azure Function Gateway**
```
Teams ←→ Bot Service ←→ Azure Function (PUBLIC) ←→ App Service (PRIVATE)
                              │
                        Validates Bot tokens
                        Minimal attack surface
```

**Why This Is Best:**
1. Only a tiny Function is public, not the whole app
2. Function validates Bot Framework JWT tokens before forwarding
3. Function has VNet integration to call private App Service
4. Separate concerns - bot logic isolated from main app

**Security Approval Needed For:**
- One Azure Function with public endpoint
- Function validates Bot Framework tokens
- Function calls private App Service via VNet

---

## Target Audience: GSX (Government Support Engineers)

**Note**: This application is designed for **GSX (Government Support Engineers)**, not CSS.

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

### ✅ Recent Changes (January 26-27, 2026)

| Change | Details |
|--------|---------|
| MSI auth for Azure SQL | Token-based auth via `DefaultAzureCredential` |
| MSI auth for Azure OpenAI | `get_bearer_token_provider()` and `ad_token_provider` |
| SQL Admin workaround | App Service MSI set as SQL admin (Directory Readers unavailable) |
| Renamed priority → severity | Matches DfM terminology (Sev A/B/C/D) |
| Health endpoint fix | Restored missing return statement |
| Debug endpoints removed | Cleaned up `/api/debug/*` endpoints |
| DfM integration request | Created `docs/DFM_INTEGRATION_REQUEST.md`, email sent |
| Deployed | All changes live on `app-csatguardian-dev` |
| **Kusto discovery** | DfM data is in Azure Data Explorer, not D365 OData |

### ⏳ Next Steps (Priority Order)

1. **DfM/Kusto Integration** *(Awaiting access approval)*
   - Get cluster URL, database name, table names, schema
   - Create user-assigned MSI for ADX access (or use existing Enterprise App)
   - Update `src/clients/dfm_client.py` to query Kusto
   - Add `azure-kusto-data` to requirements

2. **Teams Bot Integration** *(Awaiting security approval)*
   - Need approval for Azure Function gateway approach
   - Build Azure Function to validate Bot Framework tokens
   - Connect to private App Service via VNet
   - Build notification service with detailed alert messages

3. **Directory Readers Fix** *(Awaiting Entra Admin - Low Priority)*
   - Grant Directory Readers to SQL Server MSI (`04199892-389c-4531-97a7-42eda6734c28`)
   - Then demote App Service from SQL admin to db_datareader/db_datawriter

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
| Content Safety | `csatguardcs` | PII detection service |
| Key Vault | `kv-csatguard-dev` | Private endpoint only |
| VNet | `vnet-csatguardian-dev` | 10.100.0.0/16 |
| Dev VM | `vm-devbox-csatguardian` | For testing private endpoints |

**Testing Access:**
- No Bastion (deleted for security)
- Use `az vm run-command invoke` to test via VM
- Or access via Cloud Shell → Kudu console

---

## Development Workflow

### Deploy to Azure (from Cloud Shell):
```bash
cd ~/csat-guardian && git pull origin develop
zip -r deploy.zip src
az webapp deploy --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --src-path deploy.zip --type zip --clean
```

### Test via VM:
```bash
az vm run-command invoke \
    --resource-group CSAT_Guardian_Dev \
    --name vm-devbox-csatguardian \
    --command-id RunPowerShellScript \
    --scripts "Invoke-RestMethod -Uri 'https://app-csatguardian-dev.azurewebsites.net/api/health'"
```

### Git Workflow:
- Development branch: `develop`
- Production branch: `main`
- Always push to `develop` first, then merge to `main`

---

## File Structure (Key Files)

```
csat-guardian/
├── src/
│   ├── api.py              # Main FastAPI application
│   ├── config.py           # Configuration loading
│   ├── models.py           # Data models (Case, Engineer, etc.)
│   ├── db_sync.py          # Azure SQL with MSI auth
│   ├── requirements.txt    # Python dependencies (ONLY requirements file!)
│   ├── agent/
│   │   ├── guardian_agent.py      # Semantic Kernel AI agent
│   │   └── csat_rules_plugin.py   # Business rules plugin
│   ├── services/
│   │   ├── privacy.py             # PII scrubbing (regex + Content Safety)
│   │   ├── sentiment_service.py   # AI sentiment analysis
│   │   └── alert_service.py       # Alert generation
│   └── clients/
│       ├── dfm_client.py          # DfM data abstraction
│       └── teams_client.py        # Teams notifications (mock)
├── docs/
│   ├── FILE_REFERENCE.md          # Complete file reference
│   ├── GETTING_STARTED.md         # Entry point for newcomers
│   ├── CODE_GUIDE_FOR_NON_DEVELOPERS.md  # Python for non-programmers
│   ├── ARCHITECTURE.md            # Technical architecture
│   └── QUICK_REFERENCE.md         # Developer cheat sheet
└── infrastructure/
    ├── DEPLOYMENT_GUIDE.md        # How to deploy
    ├── bicep/                     # Infrastructure as Code
    └── sql/                       # Database schemas
```

---

## API Endpoints (All Working)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check (shows all service status) |
| `/api/engineers` | GET | List all engineers |
| `/api/cases` | GET | List cases (filter by engineer_id, status) |
| `/api/cases/{id}` | GET | Get single case with timeline |
| `/api/analyze/{id}` | POST | Run AI sentiment analysis |
| `/api/chat` | POST | Chat with AI agent |
| `/api/test-pii` | POST | Test PII scrubbing |

---

## What's NOT Working / Known Issues

1. **DfM Integration**: Using mock data, not real DfM/Kusto data (awaiting access)
2. **Teams Bot**: Not implemented (awaiting security approval)
3. **SCM Basic Auth**: DISABLED on App Service - must use `az webapp deploy` with AAD auth
4. **CI/CD**: Not possible with current network restrictions

---

## Session History

| Date | Key Accomplishments |
|------|---------------------|
| Jan 28 | Fixed Content Safety boolean bug, CaseSeverity migration, comprehensive documentation |
| Jan 27 | Discovered DfM data is in Kusto, created integration request |
| Jan 26 | MSI authentication for SQL and OpenAI, SQL Admin workaround |
| Jan 25 | Security hardening, database concurrency fix, all analysis features working |
| Jan 24 | Private networking, deployment method documented |
| Jan 23 | Initial deployment, FastAPI + Semantic Kernel setup |

---

## Contact / Ownership

- **Project Owner**: Kyle Monteagudo
- **Repository**: github.com/kmonteagudo_microsoft/csat-guardian
- **Target Users**: GSX (Government Support Engineers)


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
