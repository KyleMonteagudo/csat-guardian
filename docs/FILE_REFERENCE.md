# CSAT Guardian - File Reference (Cheat Sheet)

> **Purpose:** Quick reference guide explaining what every file in the project does.
> 
> **Last Updated:** January 23, 2026

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
│   └── 📁 adr/                  # Architecture Decision Records
│
├── 📁 infrastructure/           # Azure IaC
│   ├── 📁 bicep/                # Bicep templates
│   └── 📁 scripts/              # Deployment scripts
│
└── 📁 src/                      # Source code
    ├── 📄 main.py               # Application entry point
    ├── 📄 config.py             # Configuration management
    ├── 📄 logger.py             # Logging setup
    ├── 📄 models.py             # Data models
    ├── 📄 database.py           # Database operations
    ├── 📄 sample_data.py        # POC test data
    ├── 📄 monitor.py            # Case monitoring
    │
    ├── 📁 agent/                # Conversational AI
    │   └── 📄 guardian_agent.py
    │
    ├── 📁 clients/              # External service clients
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

### `bicep/main.bicep`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Infrastructure as Code for Azure resources |
| **Deploys** | Key Vault, SQL, Container Apps, etc. |

**What it creates:**
```bicep
// Resource Group: rg-csat-guardian-{env}
// Key Vault: kv-csat-guardian-{env}
// SQL Server: sql-csat-guardian-{env}
// Container App: ca-csat-guardian-{env}
// App Insights: appi-csat-guardian-{env}
```

---

### `scripts/deploy.ps1`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Deployment automation script |
| **Runs** | Azure CLI + Bicep deployment |

**Usage:**
```powershell
./deploy.ps1 -Environment dev -Location eastus
```

---

## 📁 src/ - Source Code

### `main.py` - Application Entry Point

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
