# CSAT Guardian - File Reference (Cheat Sheet)

> **Purpose:** Quick reference guide explaining what every file in the project does.
> 
> **Last Updated:** January 24, 2026

---

## 🌐 Deployed Azure Resources (Dev Environment)

All resources deployed with **private endpoints** in VNet `vnet-csatguardian-dev` (10.100.0.0/16).

| Resource | Name | Endpoint / Private IP |
|----------|------|----------------------|
| **Resource Group** | `rg-csatguardian-dev` | usgovvirginia |
| **Virtual Network** | `vnet-csatguardian-dev` | 10.100.0.0/16 |
| **Key Vault** | `kv-csatguardian-dev` | PE: 10.100.2.5 |
| **SQL Server** | `sql-csatguardian-dev` | PE: 10.100.2.4 |
| **SQL Database** | `csatdb` | (on above server) |
| **Azure OpenAI** | `oai-csatguardian-dev` | PE: 10.100.2.6 |
| **App Service** | `app-csatguardian-dev` | `https://app-csatguardian-dev.azurewebsites.us` |
| **App Service Plan** | `asp-csatguardian-dev` | Linux B1, Python 3.12 |
| **App Insights** | `appi-csatguardian-dev` | (connection string in Key Vault) |

### Private DNS Zones

| Zone | Purpose |
|------|---------|
| `privatelink.database.usgovcloudapi.net` | SQL Server private resolution |
| `privatelink.vaultcore.usgovcloudapi.net` | Key Vault private resolution |
| `privatelink.openai.azure.us` | Azure OpenAI private resolution |

### Key Vault Secrets

| Secret Name | Description |
|-------------|-------------|
| `AzureOpenAI--ApiKey` | Azure OpenAI API key |
| `AzureOpenAI--Endpoint` | `https://oai-csatguardian-dev.openai.azure.us/` |
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
│   ├── 📄 AZURE_GOVERNMENT.md   # Azure Gov specifics
│   ├── 📁 adr/                  # Architecture Decision Records
│   └── 📁 diagrams/             # Infrastructure diagrams
│       └── 📄 infrastructure.md # Mermaid diagrams for security reviews
│
├── 📁 infrastructure/           # Azure IaC
│   ├── 📁 bicep/                # Bicep templates
│   └── 📁 scripts/              # Deployment scripts
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

### `bicep/main-private.bicep`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Infrastructure as Code for Azure resources with private networking |
| **Deploys** | VNet, Private Endpoints, Key Vault, SQL, Azure OpenAI, App Service |
| **Cloud** | Azure Government (usgovvirginia) |

**What it creates:**
```bicep
// Resource Group: rg-csatguardian-{env}
// Virtual Network: vnet-csatguardian-{env} (10.100.0.0/16)
// Subnets: snet-appservice (10.100.1.0/24), snet-privateendpoints (10.100.2.0/24)
// Private DNS Zones: SQL, Key Vault, OpenAI
// Key Vault: kv-csatguardian-{env} + Private Endpoint
// SQL Server: sql-csatguardian-{env} + Private Endpoint
// Azure OpenAI: oai-csatguardian-{env} + Private Endpoint (gpt-4o)
// App Service Plan: asp-csatguardian-{env} (Linux B1)
// App Service: app-csatguardian-{env} (VNet Integrated)
// App Insights: appi-csatguardian-{env}
// Log Analytics: log-csatguardian-{env}
```

**Bicep Modules:**
| Module | Purpose |
|--------|---------|
| `modules/networking.bicep` | VNet and subnets |
| `modules/private-dns.bicep` | Private DNS zones with VNet links |
| `modules/openai.bicep` | Azure OpenAI with gpt-4o deployment |
| `modules/private-endpoints.bicep` | Private endpoints for SQL, Key Vault, OpenAI |
| `modules/appservice.bicep` | App Service Plan and Web App with VNet integration |

**Deployment Command:**
```powershell
az cloud set --name AzureUSGovernment
az deployment group create `
  --resource-group rg-csatguardian-dev `
  --template-file infrastructure/bicep/main-private.bicep `
  --parameters infrastructure/bicep/main-private.bicepparam
```

---

### `scripts/deploy-private-infra.ps1`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Deployment automation script for private networking infrastructure |
| **Runs** | Azure CLI + Bicep deployment |

**Usage:**
```powershell
./deploy-private-infra.ps1 -WhatIf  # Preview changes
./deploy-private-infra.ps1          # Deploy
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
- Streamlit/FastAPI compatibility issues with aioodbc
- pyodbc is more stable for Azure SQL in Government cloud
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

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `CSATGuardianApp` | Main application orchestrator |

**Flow:**
```
main() 
  → parse_arguments()
  → CSATGuardianApp.initialize()
      → Load config
      → Setup logging
      → Initialize database
      → Create services
  → Run command (setup/scan/monitor/chat)
  → cleanup()
```

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

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `from_environment()` | Load from env vars / Key Vault |
| `validate_for_production()` | Ensure all required settings exist |

---

### `logger.py` - Logging Setup

| Attribute | Value |
|-----------|-------|
| **Purpose** | Comprehensive logging with JSON support |
| **Output** | Console + file + Azure Monitor compatible |

**Key Functions:**
| Function | Purpose |
|----------|---------|
| `setup_logging()` | Initialize logging system |
| `get_logger(name)` | Get logger for a module |
| `log_case_event()` | Structured case event logging |
| `log_api_call()` | Log external API calls |
| `log_notification()` | Log Teams notifications |

**Log Format (JSON):**
```json
{
  "timestamp": "2026-01-23T10:30:00Z",
  "level": "INFO",
  "logger": "sentiment_service",
  "message": "Analyzed case sentiment",
  "case_id": "case-001",
  "sentiment": "negative"
}
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
| `ConversationSession` | Chat session state |

**Enums:**
| Enum | Values |
|------|--------|
| `CaseStatus` | Open, InProgress, Resolved, Closed |
| `CasePriority` | Low, Medium, High, Critical |
| `SentimentLabel` | Positive, Neutral, Negative |
| `AlertType` | NegativeSentiment, ComplianceWarning, etc. |

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
| `DBMetric` | Analytics metrics table |
| `DatabaseManager` | All database operations |

**Key Methods (DatabaseManager):**
| Method | Purpose |
|--------|---------|
| `initialize()` | Create tables if not exist |
| `get_case(id)` | Fetch single case |
| `get_cases_by_owner(id)` | Cases for an engineer |
| `create_alert(alert)` | Record sent alert |
| `record_metric(name, value)` | Store analytics |

---

### `sample_data.py` - POC Test Data

| Attribute | Value |
|-----------|-------|
| **Purpose** | Create realistic test scenarios |
| **When Used** | `python main.py setup` |

**Test Scenarios:**
| Case ID | Scenario | Expected Alert |
|---------|----------|----------------|
| `case-001` | Happy customer | None |
| `case-002` | Frustrated customer | Negative sentiment |
| `case-003` | Neutral customer | None |
| `case-004` | Declining sentiment | Trend alert |
| `case-005` | 5 days no update | Compliance warning |
| `case-006` | 8 days no update | Compliance breach |

**Key Function:**
```python
async def create_sample_data(database: DatabaseManager):
    # Creates engineers, customers, cases, and timeline entries
```

---

### `monitor.py` - Case Monitor

| Attribute | Value |
|-----------|-------|
| **Purpose** | Orchestrates case scanning workflow |
| **Pattern** | Single scan or continuous loop |

**Key Class: `CaseMonitor`**

| Method | Purpose |
|--------|---------|
| `run_scan()` | Single pass through all cases |
| `run_continuous(interval)` | Loop with sleep between scans |
| `stop()` | Gracefully stop monitoring |

**Scan Workflow:**
```
1. Fetch all active cases
2. For each case:
   a. Run sentiment analysis
   b. Check 7-day compliance
   c. Generate alerts if needed
3. Record metrics
4. Return summary
```

---

## 📁 src/agent/ - Conversational AI

### `guardian_agent.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Semantic Kernel agent for engineer chat |
| **Framework** | Semantic Kernel with Azure OpenAI |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `CasePlugin` | SK plugin exposing case functions |
| `CSATGuardianAgent` | Main conversational agent |

**CasePlugin Functions (callable by AI):**
| Function | Description |
|----------|-------------|
| `get_case_summary` | Get summary of a specific case |
| `analyze_case_sentiment` | Run sentiment analysis |
| `get_recommendations` | Get suggested actions |
| `list_my_cases` | List engineer's assigned cases |

**Usage:**
```python
agent = await create_agent(engineer, dfm_client, sentiment_service)
response = await agent.chat("Tell me about case 12345")
```

---

## 📁 src/clients/ - External Service Clients

### `azure_sql_adapter.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Async wrapper for synchronous db_sync module |
| **Pattern** | Adapter pattern using `run_in_executor` |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `AzureSQLDfMAdapter` | Async adapter wrapping SyncDatabaseManager |

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `get_case(id)` | Async fetch single case |
| `get_active_cases()` | Async get all active cases |
| `get_cases_by_owner(id)` | Async cases for engineer |
| `get_engineers()` | Async get all engineers |
| `close()` | Close database connection |

**Why this adapter?**
- FastAPI requires async operations
- pyodbc is synchronous
- Uses `asyncio.run_in_executor()` to bridge sync/async

**Factory:**
```python
adapter = await get_azure_sql_adapter()
cases = await adapter.get_active_cases()
```

---

### `dfm_client.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Interface for DfM (Dynamics) data access |
| **Pattern** | Abstract base + Mock/Real implementations |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `DfMClientBase` | Abstract interface |
| `MockDfMClient` | Reads from Azure SQL sample data |
| `RealDfMClient` | (TODO) Calls real DfM API |

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `get_case(id)` | Fetch single case |
| `get_active_cases()` | All active cases |
| `get_cases_by_owner(id)` | Cases for an engineer |
| `get_case_timeline(id)` | Timeline entries for case |

**Factory:**
```python
client = await get_dfm_client(config)
# Returns MockDfMClient if USE_MOCK_DFM=true
# Returns RealDfMClient if USE_MOCK_DFM=false
```

---

### `teams_client.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Send alerts to Microsoft Teams |
| **Pattern** | Abstract base + Mock/Real implementations |

**Key Classes:**
| Class | Purpose |
|-------|---------|
| `TeamsClientBase` | Abstract interface |
| `MockTeamsClient` | Prints to console |
| `RealTeamsClient` | (TODO) Sends to real Teams |

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `send_alert(engineer, alert)` | Send alert notification |
| `send_message(engineer, msg)` | Send plain message |
| `format_alert_card(alert)` | Create Adaptive Card |

---

## 📁 src/services/ - Business Logic

### `sentiment_service.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Azure OpenAI sentiment analysis |
| **AI Model** | GPT-4o via Azure OpenAI |

**Key Class: `SentimentAnalysisService`**

| Method | Purpose |
|--------|---------|
| `analyze_text(text)` | Analyze single text |
| `analyze_case(case)` | Analyze entire case |
| `_generate_summary(case)` | Create case summary |

**Prompts Used:**
| Prompt | Purpose |
|--------|---------|
| `SENTIMENT_ANALYSIS_PROMPT` | Classify text sentiment |
| `CASE_SUMMARY_PROMPT` | Summarize case context |
| `RECOMMENDATION_PROMPT` | Generate coaching tips |

**Output:**
```python
SentimentResult(
    label="negative",      # positive/neutral/negative
    score=0.2,             # 0-1 scale
    confidence=0.95,       # confidence level
    key_phrases=["frustrated", "waiting"],
    concerns=["Response time", "Repeated explanations"]
)
```

---

### `alert_service.py`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate and send alerts |
| **Features** | Deduplication, templates, urgency levels |

**Key Class: `AlertService`**

| Method | Purpose |
|--------|---------|
| `process_analysis(case, analysis)` | Check if alerts needed |
| `_is_duplicate(case_id, type)` | 24-hour deduplication |
| `_create_alert(case, type)` | Build alert from template |
| `_send_alert(alert)` | Send via Teams client |
| `_record_alert(alert)` | Save to database |

**Alert Types:**
| Type | Trigger |
|------|---------|
| `negative_sentiment` | Score < 0.3 |
| `declining_trend` | Sentiment dropping |
| `compliance_warning` | 5+ days no note |
| `compliance_breach` | 7+ days no note |
| `communication_gap` | No response in X hours |
| `escalation_risk` | Keywords detected |

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

## 📝 Adding New Files

When you add a new file:

1. **Add entry to this document** with:
   - Purpose
   - Key classes/functions
   - How it connects to other files

2. **Update `__init__.py`** in the appropriate package

3. **Add comments** at the top of the file explaining its purpose

4. **Commit with descriptive message:**
   ```
   feat(service): add new XYZ service
   
   - Added src/services/xyz_service.py
   - Updated FILE_REFERENCE.md
   - Added unit tests
   ```

---

*This document is maintained as part of the codebase and should be updated whenever files are added, modified, or removed.*
