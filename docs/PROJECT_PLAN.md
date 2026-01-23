# CSAT Guardian - Project Plan & SDLC

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Kyle Monteagudo | Initial project plan |
| 1.1 | 2026-01-23 | Kyle Monteagudo | Updated Sprint 0 checklist with completed Azure Gov deployment |
| 1.2 | 2026-01-23 | Kyle Monteagudo | Marked database seeding and connectivity testing complete |
| 1.3 | 2026-01-23 | Kyle Monteagudo | Sprint 0 complete: branch protection, ADRs, issue templates |
| 1.4 | 2026-01-23 | Kyle Monteagudo | Sprint 0 validated: Application runs end-to-end with Azure SQL/OpenAI (0 errors) |
| 1.5 | 2026-01-24 | Kyle Monteagudo | Updated to App Service with VNet integration and private endpoints |

---

## 1. Executive Summary

This document outlines the Software Development Life Cycle (SDLC) plan for CSAT Guardian, including source control strategy, documentation requirements, secrets management, and cloud-first architecture decisions.

### Key Decisions

| Decision | Approach |
|----------|----------|
| **Source Control** | GitHub repository with branch protection |
| **SDLC Methodology** | Agile with 2-week sprints, GitHub Projects for tracking |
| **Documentation** | In-repo docs with file-level README files |
| **Secrets Management** | Azure Key Vault with Managed Identity (private endpoint) |
| **Data Storage** | Azure SQL Database via private endpoint (no local data) |
| **Application Hosting** | Azure App Service with VNet integration (no local hosting) |
| **Network Security** | Private endpoints for all Azure services (no public access) |
| **AI Services** | Azure OpenAI (gpt-4o) via private endpoint |

---

## 2. Source Control Strategy

### 2.1 Repository Structure

```
csat-guardian/
├── .github/
│   ├── workflows/              # GitHub Actions CI/CD
│   │   ├── ci.yml              # Continuous Integration
│   │   ├── cd-dev.yml          # Deploy to Dev
│   │   └── cd-prod.yml         # Deploy to Production
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── task.md
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── APPLICATION_SECURITY_REVIEW.md
│   ├── PROJECT_PLAN.md         # This document
│   ├── ARCHITECTURE.md         # Detailed architecture
│   ├── FILE_REFERENCE.md       # Cheat sheet for all files
│   ├── RUNBOOK.md              # Operations guide
│   └── API_REFERENCE.md        # API documentation
├── infrastructure/
│   ├── bicep/                  # Azure Infrastructure as Code
│   │   ├── main.bicep
│   │   ├── modules/
│   │   └── parameters/
│   └── scripts/
│       ├── deploy.ps1
│       └── seed-database.ps1
├── src/
│   ├── CsatGuardian.Api/       # Main API service
│   ├── CsatGuardian.Functions/ # Azure Functions (if needed)
│   ├── CsatGuardian.Core/      # Shared business logic
│   └── CsatGuardian.Tests/     # Unit & integration tests
├── .gitignore
├── .env.example                # Example environment (NO SECRETS)
├── README.md
└── LICENSE
```

### 2.2 Branch Strategy

```
main (protected)
  │
  ├── develop (integration branch)
  │     │
  │     ├── feature/CSAT-001-sentiment-analysis
  │     ├── feature/CSAT-002-teams-integration
  │     ├── bugfix/CSAT-003-alert-deduplication
  │     └── hotfix/CSAT-004-critical-fix
  │
  └── release/v1.0.0
```

| Branch | Purpose | Merges To |
|--------|---------|-----------|
| `main` | Production-ready code | N/A (protected) |
| `develop` | Integration branch | `main` via PR |
| `feature/*` | New features | `develop` via PR |
| `bugfix/*` | Bug fixes | `develop` via PR |
| `hotfix/*` | Critical production fixes | `main` and `develop` |
| `release/*` | Release preparation | `main` via PR |

### 2.3 Branch Protection Rules

**For `main` branch:**
- ✅ Require pull request reviews (1 reviewer minimum)
- ✅ Require status checks to pass (CI pipeline)
- ✅ Require conversation resolution
- ✅ Require signed commits (optional for POC)
- ✅ No direct pushes

**For `develop` branch:**
- ✅ Require pull request reviews
- ✅ Require status checks to pass

### 2.4 Commit Message Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
```
feat(sentiment): add Azure OpenAI integration for sentiment analysis
fix(alerts): prevent duplicate alerts within 24-hour window
docs(readme): update deployment instructions
ci(actions): add automated testing workflow
```

---

## 3. SDLC Methodology

### 3.1 Agile Framework

We will use **Agile Scrum** with:
- **Sprint Duration:** 2 weeks
- **Ceremonies:** Sprint Planning, Daily Standups (async), Sprint Review, Retrospective
- **Tracking:** GitHub Projects (Kanban board)

### 3.2 GitHub Projects Board

**Columns:**
| Column | Description |
|--------|-------------|
| 📋 Backlog | All planned work items |
| 🔖 Sprint Backlog | Items committed to current sprint |
| 🏗️ In Progress | Currently being worked on |
| 👀 In Review | PR submitted, awaiting review |
| ✅ Done | Completed and merged |

### 3.3 Issue Labels

| Label | Color | Description |
|-------|-------|-------------|
| `priority: critical` | 🔴 Red | Must be done immediately |
| `priority: high` | 🟠 Orange | Important, do soon |
| `priority: medium` | 🟡 Yellow | Normal priority |
| `priority: low` | 🟢 Green | Nice to have |
| `type: feature` | 🔵 Blue | New functionality |
| `type: bug` | 🔴 Red | Something broken |
| `type: docs` | 📄 Gray | Documentation |
| `type: infrastructure` | ⚙️ Purple | Azure/DevOps work |
| `type: security` | 🔒 Black | Security-related |
| `status: blocked` | 🚫 Red | Waiting on something |
| `status: needs-info` | ❓ Yellow | Needs clarification |

### 3.4 Sprint Schedule (POC Phase)

| Sprint | Dates | Focus |
|--------|-------|-------|
| Sprint 0 | Jan 23 - Feb 5 | Infrastructure setup, CI/CD, documentation framework |
| Sprint 1 | Feb 6 - Feb 19 | Core services: DfM client, sentiment analysis |
| Sprint 2 | Feb 20 - Mar 5 | Alert system, Teams integration |
| Sprint 3 | Mar 6 - Mar 19 | Conversational agent, monitoring |
| Sprint 4 | Mar 20 - Apr 2 | Testing, polish, pilot preparation |

---

## 4. Documentation Strategy

### 4.1 Documentation Types

| Document | Location | Purpose |
|----------|----------|---------|
| **README.md** | Root & each folder | Quick start, folder purpose |
| **FILE_REFERENCE.md** | `/docs/` | Cheat sheet for all files |
| **ARCHITECTURE.md** | `/docs/` | System design, data flows |
| **API_REFERENCE.md** | `/docs/` | API endpoints, contracts |
| **RUNBOOK.md** | `/docs/` | Operations, troubleshooting |
| **Code Comments** | In source files | Line-by-line explanations |
| **ADR (Architecture Decision Records)** | `/docs/adr/` | Why decisions were made |

### 4.2 File Reference Format

Every file will be documented in `FILE_REFERENCE.md` with:

```markdown
## src/services/sentiment_service.py

**Purpose:** Integrates with Azure OpenAI to analyze customer sentiment

**Dependencies:**
- `config.py` - Configuration settings
- `models.py` - Data models
- Azure OpenAI SDK

**Key Functions:**
| Function | Description |
|----------|-------------|
| `analyze_text()` | Analyzes a single text for sentiment |
| `analyze_case()` | Analyzes entire case timeline |
| `_generate_summary()` | Creates case summary using GPT |

**Configuration Required:**
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - (from Key Vault)

**Example Usage:**
```python
service = SentimentAnalysisService(config)
result = await service.analyze_text("I'm frustrated with this issue")
print(result.label)  # "negative"
```
```

### 4.3 Architecture Decision Records (ADR)

Each significant decision will be documented:

```markdown
# ADR-001: Use Azure SQL Database for Sample Data

## Status
Accepted

## Context
We need to store sample case data for the POC. Options considered:
1. Local SQLite database
2. Azure SQL Database
3. Cosmos DB

## Decision
Use Azure SQL Database because:
- Simulates production environment
- No local dependencies
- Supports API-based access pattern
- Easy to seed with test data

## Consequences
- Requires Azure subscription
- Small monthly cost (~$5/month for Basic tier)
- Need to manage connection strings via Key Vault
```

---

## 5. Secrets Management Strategy

### 5.1 Principles

1. **Never commit secrets** - No API keys, connection strings, or passwords in code
2. **Use Azure Key Vault** - All secrets stored in Key Vault
3. **Use Managed Identity** - No secrets in application configuration
4. **Environment separation** - Separate Key Vaults for Dev/Prod

### 5.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SECRETS MANAGEMENT FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

Developer Machine                    Azure Cloud
─────────────────                    ───────────
                                     
  .env.local                         ┌─────────────────┐
  (gitignored)     ───────────────▶  │  Azure Key Vault │
  - Only for                         │                  │
    local dev                        │  Secrets:        │
                                     │  - AzureOpenAI   │
                                     │  - SqlConnection │
                                     │  - TeamsWebhook  │
  GitHub Actions                     └────────┬─────────┘
  ─────────────                               │
                                              │ Managed Identity
  Secrets stored   ───────────────▶           │
  in GitHub                                   ▼
  (for CI/CD only)                   ┌─────────────────┐
                                     │  Container App  │
                                     │  (or Functions) │
                                     │                 │
                                     │  No secrets in  │
                                     │  app config!    │
                                     └─────────────────┘
```

### 5.3 Key Vault Secrets

| Secret Name | Description | Used By |
|-------------|-------------|---------|
| `AzureOpenAI--Endpoint` | Azure OpenAI endpoint URL | Sentiment Service |
| `AzureOpenAI--ApiKey` | Azure OpenAI API key | Sentiment Service |
| `SqlServer--ConnectionString` | Azure SQL connection string | Database layer |
| `Teams--WebhookUrl` | Teams incoming webhook URL | Alert Service |
| `DfM--ClientId` | DfM API client ID | DfM Client |
| `DfM--ClientSecret` | DfM API client secret | DfM Client |

### 5.4 Code Pattern for Secrets

```python
# ❌ BAD - Never do this
connection_string = "Server=myserver.database.windows.net;..."
api_key = "sk-abc123..."

# ✅ GOOD - Use Azure SDK with Managed Identity
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://csat-guardian-kv.vault.azure.net/", credential=credential)

# Secrets are retrieved at runtime, never stored in code
connection_string = client.get_secret("SqlServer--ConnectionString").value
```

### 5.5 Local Development

For local development only:

```bash
# .env.local (GITIGNORED - never committed)
# These override Key Vault for local dev

AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here

# OR use Azure CLI authentication
# az login
# Then DefaultAzureCredential will use your Azure CLI session
```

---

## 6. Cloud Architecture

### 6.1 No Local Hosting

**Principle:** The entire application runs in Azure. No components on local machines.

| Component | Azure Service | Why |
|-----------|--------------|-----|
| Application | Azure Container Apps | Serverless containers, auto-scale |
| Database | Azure SQL Database | Managed, secure, no local data |
| Secrets | Azure Key Vault | Centralized secret management |
| AI | Azure OpenAI | Enterprise AI service |
| Monitoring | Azure Monitor + App Insights | Full observability |
| CI/CD | GitHub Actions | Automated deployments |

### 6.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AZURE RESOURCE GROUP                                │
│                        (rg-csat-guardian-dev)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐         ┌─────────────────┐                          │
│   │  Azure OpenAI   │         │   Key Vault     │                          │
│   │  (Sentiment)    │◀────────│   (Secrets)     │                          │
│   └────────┬────────┘         └────────┬────────┘                          │
│            │                           │                                    │
│            │    ┌──────────────────────┴───────────────────────┐           │
│            │    │                                               │           │
│            ▼    ▼                                               │           │
│   ┌─────────────────────────────────┐                          │           │
│   │      Azure Container Apps       │                          │           │
│   │     (csat-guardian-api)         │                          │           │
│   │                                 │                          │           │
│   │  ┌─────────────────────────┐   │                          │           │
│   │  │    CSAT Guardian API    │   │                          │           │
│   │  │                         │   │                          │           │
│   │  │  • Monitor Service      │   │                          │           │
│   │  │  • Sentiment Service    │   │                          │           │
│   │  │  • Alert Service        │   │                          │           │
│   │  │  • Agent Service        │   │                          │           │
│   │  └─────────────────────────┘   │                          │           │
│   └────────────────┬────────────────┘                          │           │
│                    │                                            │           │
│            ┌───────┴───────┐                                   │           │
│            │               │                                   │           │
│            ▼               ▼                                   ▼           │
│   ┌─────────────┐   ┌─────────────┐                   ┌─────────────┐     │
│   │  Azure SQL  │   │  Microsoft  │                   │   App       │     │
│   │  Database   │   │   Teams     │                   │  Insights   │     │
│   │  (Cases)    │   │   (Alerts)  │                   │  (Logs)     │     │
│   └─────────────┘   └─────────────┘                   └─────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              │
                              │ HTTPS (API calls simulate DfM)
                              ▼
                    ┌─────────────────┐
                    │    Developer    │
                    │    (Testing)    │
                    └─────────────────┘
```

### 6.3 Azure Resources Required

| Resource | SKU | Est. Monthly Cost | Purpose |
|----------|-----|-------------------|---------|
| Resource Group | N/A | Free | Container for resources |
| Container Apps Environment | Consumption | ~$0-5 | Serverless compute |
| Container App | 0.5 vCPU, 1GB | ~$10-20 | Application hosting |
| Azure SQL Database | Basic (5 DTU) | ~$5 | Sample data storage |
| Key Vault | Standard | ~$0.03/secret | Secrets management |
| Azure OpenAI | Pay-per-use | ~$5-20 | Sentiment analysis |
| App Insights | Free tier | Free | Monitoring |
| Container Registry | Basic | ~$5 | Docker images |
| **Total Estimated** | | **~$25-55/month** | |

### 6.4 Sample Data in Azure SQL

Instead of local SQLite, sample data lives in Azure SQL:

```sql
-- Sample data is seeded via CI/CD or script
-- Connection is via Managed Identity (no password in code)

-- Cases table
CREATE TABLE Cases (
    Id NVARCHAR(50) PRIMARY KEY,
    Title NVARCHAR(500),
    Description NVARCHAR(MAX),
    Status NVARCHAR(50),
    Priority NVARCHAR(50),
    OwnerId NVARCHAR(50),
    CustomerId NVARCHAR(50),
    CreatedOn DATETIME2,
    ModifiedOn DATETIME2
);

-- Seed script creates 6 test scenarios
INSERT INTO Cases VALUES ('case-001', 'Happy Customer Scenario', ...);
```

### 6.5 API-Based Data Access

Even for sample data, we use API patterns:

```python
# The application calls its own API endpoints
# This simulates how we'll call DfM in production

# GET /api/cases - List all cases
# GET /api/cases/{id} - Get case details
# GET /api/cases/{id}/timeline - Get case timeline

# In POC: These hit Azure SQL with sample data
# In Production: These will proxy to DfM APIs
```

---

## 7. CI/CD Pipeline

### 7.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Push to        PR to           Merge to        Merge to
  feature/*      develop         develop         main
      │              │               │               │
      ▼              ▼               ▼               ▼
  ┌──────────┐  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  Build   │  │  Build   │   │  Build   │   │  Build   │
  │  & Test  │  │  & Test  │   │  & Test  │   │  & Test  │
  └────┬─────┘  └────┬─────┘   └────┬─────┘   └────┬─────┘
       │             │              │               │
       ▼             ▼              ▼               ▼
  ┌──────────┐  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  Lint    │  │  Lint    │   │  Push to │   │  Push to │
  │  Check   │  │  Check   │   │   ACR    │   │   ACR    │
  └──────────┘  └────┬─────┘   └────┬─────┘   └────┬─────┘
                     │              │               │
                     ▼              ▼               ▼
               ┌──────────┐   ┌──────────┐   ┌──────────┐
               │ Security │   │ Deploy   │   │ Deploy   │
               │   Scan   │   │  to DEV  │   │ to PROD  │
               └──────────┘   └──────────┘   └──────────┘
```

### 7.2 GitHub Actions Workflows

**CI Workflow (.github/workflows/ci.yml):**
```yaml
name: CI

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run linting
        run: ruff check .
      - name: Run tests
        run: pytest tests/ -v
      - name: Security scan
        uses: snyk/actions/python@master
```

---

## 8. Sprint 0 Checklist

### 8.1 Infrastructure Tasks

- [x] Create GitHub repository ✅ `kmonteagudo_microsoft/csat-guardian`
- [x] Configure branch protection rules ✅ (main: require PR, 1 reviewer, dismiss stale)
- [ ] Set up GitHub Projects board ⚠️ (requires `gh auth refresh -s project,read:project`)
- [x] Create issue templates ✅ (bug_report.md, feature_request.md, task.md)
- [x] Create PR template ✅ (PULL_REQUEST_TEMPLATE.md)
- [x] Set up GitHub Actions workflows ✅ (CI/CD files created)

### 8.2 Azure Setup Tasks

- [x] Create Azure Resource Group ✅ `rg-csatguardian-dev` (usgovvirginia)
- [x] Deploy Virtual Network ✅ `vnet-csatguardian-dev` (10.100.0.0/16)
- [x] Deploy Key Vault ✅ `kv-csatguardian-dev.vault.usgovcloudapi.net`
- [x] Deploy Azure SQL Database ✅ `sql-csatguardian-dev.database.usgovcloudapi.net`
- [x] Deploy Azure OpenAI ✅ `oai-csatguardian-dev.openai.azure.us` (gpt-4o)
- [x] Deploy App Service ✅ `app-csatguardian-dev.azurewebsites.us` (Python 3.12, Linux)
- [x] Deploy App Service Plan ✅ `asp-csatguardian-dev` (Linux B1)
- [x] Configure Private Endpoints ✅ (SQL: 10.100.2.4, Key Vault: 10.100.2.5, OpenAI: 10.100.2.6)
- [x] Configure Private DNS Zones ✅ (3 zones with VNet links)
- [x] Configure VNet Integration ✅ (App Service → snet-appservice)
- [x] Configure Managed Identities ✅ (App Service has system-assigned identity)
- [x] Store secrets in Key Vault ✅ (Azure OpenAI + SQL + App Insights)
- [x] Seed sample data ✅ (6 cases, 17 timeline entries, 3 engineers, 6 customers)

### 8.3 Documentation Tasks

- [x] Finalize PROJECT_PLAN.md ✅
- [x] Create FILE_REFERENCE.md structure ✅
- [x] Create ARCHITECTURE.md ✅
- [x] Set up ADR folder ✅ (3 ADRs: Azure Gov, Key Vault, Container Apps)
- [x] Create initial README files ✅

### 8.4 Development Environment

- [x] Document local setup process ✅
- [x] Create .env.example ✅
- [x] Test Azure CLI authentication ✅ (Azure Government)
- [x] Verify Key Vault access ✅ (Secrets Officer role assigned)
- [x] Test database connectivity ✅ (via scripts/test_db_connection.py)

### 8.5 Application Validation

- [x] Run monitoring scan ✅ (`python main.py scan`)
- [x] Verify Azure OpenAI connectivity ✅ (sentiment analysis working)
- [x] Verify Azure SQL connectivity ✅ (6 cases, 17 timeline entries)
- [x] Test alert generation ✅ (7 alerts generated correctly)
- [x] Confirm zero errors ✅ (all 6 cases analyzed successfully)

---

## 9. Definition of Done

A feature/task is considered "Done" when:

- [ ] Code is complete and follows coding standards
- [ ] All code is commented explaining what each section does
- [ ] Unit tests are written and passing
- [ ] Code review completed and approved
- [ ] Documentation updated (FILE_REFERENCE.md, README, etc.)
- [ ] No secrets or sensitive data in code
- [ ] CI pipeline passes
- [ ] Deployed to Dev environment
- [ ] Smoke tested in Dev

---

## 10. Appendix: GitHub Repository Setup Commands

```bash
# Create repository (do this on GitHub.com first, then:)

# Clone the repository
git clone https://github.com/your-org/csat-guardian.git
cd csat-guardian

# Create develop branch
git checkout -b develop
git push -u origin develop

# Set up branch protection (do in GitHub Settings > Branches)

# Create initial structure
mkdir -p .github/workflows .github/ISSUE_TEMPLATE docs infrastructure/bicep src

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
.env
.env.local

# IDE
.vscode/
.idea/

# Azure
.azure/

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Build
dist/
build/
*.egg-info/
EOF

# Commit and push
git add .
git commit -m "chore: initial project structure"
git push
```

---

*Document Version: 1.0*  
*Last Updated: January 23, 2026*
