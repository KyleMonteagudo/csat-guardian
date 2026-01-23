# CSAT Guardian - File Reference (Cheat Sheet)

> **Purpose:** Quick reference guide explaining what every file in the project does.
> 
> **Last Updated:** January 25, 2026

---

## 🌐 Deployed Azure Resources (Commercial Azure - East US)

All resources deployed with **private endpoints** in VNet `vnet-csatguardian` (10.100.0.0/16).

| Resource | Name | Endpoint / Private IP |
|----------|------|----------------------|
| **Resource Group** | `KMonteagudo_CSAT_Guardian` | East US |
| **Virtual Network** | `vnet-csatguardian` | 10.100.0.0/16 |
| **Key Vault** | `kv-csatguardian` | PE: 10.100.2.5 |
| **SQL Server** | `sql-csatguardian` | PE: 10.100.2.4 |
| **SQL Database** | `csatdb` | (on above server) |
| **Azure OpenAI** | `oai-csatguardian` | PE: 10.100.2.6 |
| **App Service** | `app-csatguardian` | `https://app-csatguardian.azurewebsites.net` |
| **App Service Plan** | `asp-csatguardian` | Linux B1, Python 3.12 |
| **App Insights** | `appi-csatguardian` | (connection string in Key Vault) |

### Private DNS Zones

| Zone | Purpose |
|------|---------|
| `privatelink.database.windows.net` | SQL Server private resolution |
| `privatelink.vaultcore.azure.net` | Key Vault private resolution |
| `privatelink.openai.azure.com` | Azure OpenAI private resolution |

### Key Vault Secrets

| Secret Name | Description |
|-------------|-------------|
| `AzureOpenAI--ApiKey` | Azure OpenAI API key |
| `AzureOpenAI--Endpoint` | `https://oai-csatguardian.openai.azure.com/` |
| `AzureOpenAI--DeploymentName` | `gpt-4o` |
| `AzureOpenAI--ApiVersion` | `2025-01-01-preview` |
| `SqlServer--ConnectionString` | SQL connection string (auto-generated) |
| `AppInsights--ConnectionString` | App Insights connection (auto-generated) |

---

## 📁 Directory Structure Overview

```
csat-guardian/
├── 📄 .env.example              # Environment template (NO secrets)
├── 📄 .gitignore                # Files to exclude from git
├── 📄 README.md                 # Project overview
├── 📄 requirements.txt          # Python dependencies
│
├── 📁 .github/                  # GitHub configuration
│   ├── 📁 workflows/            # CI/CD automation
│   └── 📁 ISSUE_TEMPLATE/       # Issue templates
│
├── 📁 docs/                     # Documentation
│   ├── 📄 APPLICATION_SECURITY_REVIEW.md
│   ├── 📄 PROJECT_PLAN.md
│   ├── 📄 FILE_REFERENCE.md     # THIS FILE
│   ├── 📄 ARCHITECTURE.md
│   ├── 📁 adr/                  # Architecture Decision Records
│   └── 📁 diagrams/             # Infrastructure diagrams
│       └── 📄 infrastructure.md # Mermaid diagrams for security reviews
│
├── 📁 infrastructure/           # Azure IaC
│   ├── 📁 bicep/                # Bicep templates
│   │   ├── main-commercial.bicep      # Complete Bicep template
│   │   └── main-commercial.bicepparam # Parameters
│   ├── deploy-all.ps1           # All-in-one deployment script
│   ├── DEPLOYMENT_GUIDE.md      # Step-by-step deployment guide
│   └── 📁 scripts/              # Legacy scripts
│
└── 📁 src/                      # Source code
    ├── 📄 api.py                # FastAPI REST backend (main entry)
    ├── 📄 db_sync.py            # Synchronous Azure SQL client (pyodbc)
    ├── 📄 main.py               # CLI entry point
    ├── 📄 config.py             # Configuration management
    ├── 📄 logger.py             # Logging setup
    ├── 📄 models.py             # Data models
    ├── 📄 database.py           # Async database operations
    ├── 📄 sample_data.py        # POC test data
    ├── 📄 monitor.py            # Case monitoring
    ├── 📄 interactive_demo.py   # Teams-like chat demo
    │
    ├── 📁 agent/                # Conversational AI
    │   └── 📄 guardian_agent.py
    │
    ├── 📁 clients/              # External service clients
    │   ├── 📄 azure_sql_adapter.py # Async wrapper for db_sync
    │   ├── 📄 dfm_client.py
    │   └── 📄 teams_client.py
    │
    └── 📁 services/             # Business logic services
        ├── 📄 sentiment_service.py
        └── 📄 alert_service.py
```

---

## 📄 Root Level Files

### `.env.example`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Template for environment variables |
| **Contains Secrets?** | ❌ No - only placeholder values |
| **Committed to Git?** | ✅ Yes |

**What it does:**
- Shows all required environment variables
- Developers copy this to `.env.local` (gitignored) for local development
- In production, these come from Azure Key Vault

**Key Variables:**
```
AZURE_OPENAI_ENDPOINT      # Azure OpenAI URL
AZURE_OPENAI_API_KEY       # (from Key Vault in prod)
DATABASE_CONNECTION_STRING # Azure SQL connection
USE_MOCK_DFM              # true = use sample data
USE_MOCK_TEAMS            # true = print to console
```

---

### `requirements.txt`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Python package dependencies |
| **When to Update** | When adding new packages |

**Key Packages:**
| Package | Purpose |
|---------|---------|
| `semantic-kernel` | AI orchestration framework |
| `openai` | Azure OpenAI SDK |
| `sqlalchemy` | Database ORM |
| `pydantic` | Data validation |
| `httpx` | Async HTTP client |
| `azure-identity` | Azure authentication |
| `azure-keyvault-secrets` | Key Vault access |

---

## 📁 docs/ - Documentation

### `APPLICATION_SECURITY_REVIEW.md`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Security review documentation for API approval |
| **Audience** | Security team, reviewers |
| **Status** | Living document |

**Sections:**
1. Business justification for the application
2. Architecture diagrams
3. Data access requirements (DfM, Graph, OpenAI)
4. Security controls
5. Risk assessment

---

### `PROJECT_PLAN.md`

| Attribute | Value |
|-----------|-------|
| **Purpose** | SDLC methodology, source control strategy |
| **Audience** | Development team |

**Covers:**
- Git branching strategy
- Sprint planning
- CI/CD pipeline design
- Secrets management approach
- Cloud architecture decisions

---

### `FILE_REFERENCE.md` (This File)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Quick reference for all project files |
| **When to Update** | When adding/modifying any file |

---

## 📁 infrastructure/ - Azure Resources

### `bicep/main-commercial.bicep`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Complete Infrastructure as Code for Azure resources with private networking |
| **Deploys** | VNet, Private Endpoints, Key Vault, SQL, Azure OpenAI, App Service |
| **Cloud** | Commercial Azure (East US) |

**What it creates:**
```bicep
// Resource Group: KMonteagudo_CSAT_Guardian
// Virtual Network: vnet-csatguardian (10.100.0.0/16)
// Subnets: snet-appservice (10.100.1.0/24), snet-privateendpoints (10.100.2.0/24)
// Private DNS Zones: SQL, Key Vault, OpenAI
// Key Vault: kv-csatguardian + Private Endpoint
// SQL Server: sql-csatguardian + Private Endpoint
// Azure OpenAI: oai-csatguardian + Private Endpoint (gpt-4o)
// App Service Plan: asp-csatguardian (Linux B1)
// App Service: app-csatguardian (VNet Integrated)
// App Insights: appi-csatguardian
// Log Analytics: log-csatguardian
```

**Deployment Command:**
```powershell
.\infrastructure\deploy-all.ps1 `
    -SubscriptionId "a20d761d-cb36-4f83-b827-58ccdb166f39" `
    -ResourceGroup "KMonteagudo_CSAT_Guardian" `
    -Location "eastus"
```

---

### `deploy-all.ps1`

| Attribute | Value |
|-----------|-------|
| **Purpose** | All-in-one deployment script |
| **Runs** | Azure CLI + Bicep deployment + DB seeding + App deployment |

**Usage:**
```powershell
.\deploy-all.ps1 `
    -SubscriptionId "a20d761d-cb36-4f83-b827-58ccdb166f39" `
    -ResourceGroup "KMonteagudo_CSAT_Guardian" `
    -Location "eastus"
```

---

## 📁 src/ - Source Code

### `api.py` - FastAPI REST Backend

| Attribute | Value |
|-----------|-------|
| **Purpose** | Production-ready REST API for CSAT Guardian |
| **Run Command** | `python -m uvicorn api:app --host 0.0.0.0 --port 8000` |
| **Docs URL** | `http://localhost:8000/docs` |

**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and status |
| `/api/health` | GET | Health check with service status |
| `/api/engineers` | GET | List all engineers |
| `/api/cases` | GET | List cases (with filters) |
| `/api/cases/{id}` | GET | Get case details with timeline |
| `/api/analyze/{id}` | POST | Sentiment analysis via Azure OpenAI |
| `/api/chat` | POST | Chat with the Guardian agent |
| `/api/alerts` | GET | List active alerts |

**Key Features:**
- Async request handling
- Automatic OpenAPI docs
- CORS middleware
- Lifecycle management (startup/shutdown)

---

### `db_sync.py` - Synchronous Azure SQL Client

| Attribute | Value |
|-----------|-------|
| **Purpose** | Direct Azure SQL access using pyodbc (sync) |
| **Pattern** | Synchronous database operations |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `SyncDatabaseManager` | All sync database operations |

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `connect()` | Get/create database connection |
| `get_engineers()` | Get all engineers |
| `get_cases_for_engineer(id)` | Get cases for an engineer |
| `get_all_active_cases()` | Get all active cases |
| `get_timeline_entries(case_id)` | Get timeline for a case |

**Why synchronous?**
- pyodbc is synchronous-only
- Wrapped by `azure_sql_adapter.py` for async FastAPI

---

### `main.py` - CLI Entry Point

| Attribute | Value |
|-----------|-------|
| **Purpose** | CLI entry point, orchestrates startup |
| **Run Command** | `python main.py <command>` |

**Commands:**
| Command | Description |
|---------|-------------|
| `setup` | Initialize database with sample data |
| `scan` | Run single monitoring scan |
| `monitor` | Continuous monitoring loop |
| `chat` | Interactive conversation mode |

---

### `config.py` - Configuration Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Centralized configuration using Pydantic |
| **Pattern** | Singleton with environment variable loading |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `AzureOpenAIConfig` | OpenAI endpoint, key, deployment |
| `DatabaseConfig` | SQL connection string |
| `DfMConfig` | DfM API settings (for production) |
| `TeamsConfig` | Teams webhook URL |
| `AlertThresholds` | When to trigger alerts |
| `FeatureFlags` | Toggle mock vs real services |
| `AppConfig` | Master config combining all above |

**Usage:**
```python
from config import get_config
config = get_config()
print(config.azure_openai.endpoint)
```

---

### `models.py` - Data Models

| Attribute | Value |
|-----------|-------|
| **Purpose** | Pydantic models for type safety |
| **Pattern** | Immutable data classes with validation |

**Key Models:**
| Model | Purpose |
|-------|---------|
| `Engineer` | Support engineer (id, name, email) |
| `Customer` | Customer info (id, company) |
| `Case` | Support case with all details |
| `TimelineEntry` | Note, email, or call on a case |
| `SentimentResult` | Sentiment analysis output |
| `CaseAnalysis` | Full case analysis result |
| `Alert` | Alert to send to engineer |

---

### `database.py` - Database Layer

| Attribute | Value |
|-----------|-------|
| **Purpose** | SQLAlchemy ORM for Azure SQL |
| **Pattern** | Async database operations |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `DBEngineer` | Engineer table mapping |
| `DBCustomer` | Customer table mapping |
| `DBCase` | Case table mapping |
| `DBTimelineEntry` | Timeline entries table |
| `DBAlert` | Sent alerts table |
| `DatabaseManager` | All database operations |

---

## 📁 src/clients/ - External Service Clients

### `azure_sql_adapter.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Async wrapper for synchronous db_sync module |
| **Pattern** | Adapter pattern using `run_in_executor` |

**Why this adapter?**
- FastAPI requires async operations
- pyodbc is synchronous
- Uses `asyncio.run_in_executor()` to bridge sync/async

---

### `dfm_client.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Interface for DfM (Dynamics) data access |
| **Pattern** | Abstract base + Mock/Real implementations |

---

### `teams_client.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Send alerts to Microsoft Teams |
| **Pattern** | Abstract base + Mock/Real implementations |

---

## 📁 src/services/ - Business Logic

### `sentiment_service.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Azure OpenAI sentiment analysis |
| **AI Model** | GPT-4o via Azure OpenAI |

---

### `alert_service.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate and send alerts |
| **Features** | Deduplication, templates, urgency levels |

---

## 🔄 How Files Work Together

```
┌─────────────┐
│   main.py   │  Entry point - parses commands, initializes app
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  config.py  │────▶│  logger.py  │  Configuration & logging
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ database.py │◀───▶│  models.py  │  Data layer
└──────┬──────┘     └─────────────┘
       │
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐     ┌─────────────┐
│ dfm_client  │     │teams_client │  External clients
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────┐
│           monitor.py             │  Orchestration
└──────────────────────────────────┘
       │
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐     ┌─────────────┐
│  sentiment  │     │   alert     │  Business services
│  _service   │     │  _service   │
└─────────────┘     └─────────────┘
       │
       ▼
┌─────────────────────────────────┐
│       guardian_agent.py         │  Conversational AI
└─────────────────────────────────┘
```

---

*This document is maintained as part of the codebase and should be updated whenever files are added, modified, or removed.*
