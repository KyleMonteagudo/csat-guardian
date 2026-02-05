# CSAT Guardian - Complete Project Reference

> **Purpose:** This document explains every file and folder in the CSAT Guardian project in plain English. It is designed so that anyone—regardless of technical background—can understand what this application does and how it works.
> 
> **Audience:** Developers, security auditors, project managers, and anyone who needs to understand this codebase.
> 
> **Last Updated:** February 5, 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Problem Does This Solve?](#2-what-problem-does-this-solve)
3. [How The Application Works](#3-how-the-application-works)
4. [Azure Infrastructure](#4-azure-infrastructure)
5. [Complete File Inventory](#5-complete-file-inventory)
6. [Source Code Deep Dive](#6-source-code-deep-dive)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Security Architecture](#8-security-architecture)
9. [Deployment Guide Summary](#9-deployment-guide-summary)
10. [Glossary of Terms](#10-glossary-of-terms)
11. [Quick Reference Card](#11-quick-reference-card)

---

## 1. Executive Summary

**CSAT Guardian** is an AI-powered coaching tool that helps Microsoft Government Support Engineers (GSX) keep their customers satisfied. 

### What It Does (In Plain English)

Imagine you're a support engineer with 10 open cases. It's hard to remember:
- Which customer hasn't heard from you in a while?
- Which case is about to violate the 7-day update requirement?
- Which customer is getting frustrated based on their recent emails?

**CSAT Guardian watches all your cases and tells you when something needs attention BEFORE it becomes a problem.**

### Key Capabilities

| Feature | What It Does | Business Value |
|---------|--------------|----------------|
| **Sentiment Analysis** | AI reads customer messages and detects frustration | Catch unhappy customers early |
| **Compliance Monitoring** | Tracks 2-day communication and 7-day notes rules | Avoid policy violations |
| **Conversational Coaching** | Chat interface to ask questions about cases | Get instant, specific advice |
| **Proactive Alerts** | Notifications when cases need attention | Never miss an at-risk case |

### Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Working | All endpoints functional |
| **Frontend UI** | ✅ Working | **Microsoft Learn-style with glassmorphism, animations** |
| AI Analysis | ✅ Working | Azure OpenAI GPT-4o |
| Database | ✅ Working | Azure SQL with MSI auth |
| PII Protection | ✅ Working | Two-layer scrubbing |
| **UI Animations** | ✅ Working | **Sentiment rings, counters, skeleton loading** |
| Teams Integration | ⏳ Pending | Awaiting security approval |
| Real DfM Data | ⏳ Pending | Using mock data for now |

---

## 2. What Problem Does This Solve?

### The Challenge

Support engineers handle multiple cases simultaneously. Customer satisfaction (CSAT) scores depend on:

1. **Communication frequency** - Customers feel ignored if they don't hear from you
2. **Timely updates** - Case notes must be current for handoffs and audits
3. **Resolution quality** - Actually solving the customer's problem

**The problem:** Engineers are busy. It's easy to forget to update a case or miss signs that a customer is getting frustrated.

### The Solution

CSAT Guardian acts like a vigilant assistant that:

1. **Watches** all your cases continuously
2. **Analyzes** customer communications for sentiment
3. **Alerts** you when something needs attention
4. **Coaches** you on what to do next

### Business Rules Encoded

| Rule | Description | Consequence of Violation |
|------|-------------|-------------------------|
| **2-Day Communication** | Customer should hear from you at least every 2 days | Customer anxiety, lower CSAT |
| **7-Day Notes** | Case notes must be updated at least every 7 days | Audit failures, poor handoffs |
| **5-Hour Email-to-Notes** | After emailing a customer, add case notes within 5 hours | Lost context during handoffs |

---

## 3. How The Application Works

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                               │
│                                                                          │
│   ┌───────────────────────────────────────────────────────────────┐      │
│   │                    STATIC FRONTEND (src/static/)                  │      │
│   │                                                                   │      │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │      │
│   │   │  index.html  │  │ styles.css   │  │   app.js     │          │      │
│   │   │  (HTML5 UI)  │  │ (2,770 lines)│  │(2,793 lines) │          │      │
│   │   └──────────────┘  └──────────────┘  └──────────────┘          │      │
│   │                                                                   │      │
│   │   Features:                                                       │      │
│   │   • Glassmorphism cards with backdrop-filter blur                │      │
│   │   • Animated sentiment rings with SVG gradients                  │      │
│   │   • Animated number counters with easing                         │      │
│   │   • Skeleton loading states with shimmer effect                  │      │
│   │   • Micro-interactions (button ripples, card hover)              │      │
│   │   • Theme support (dark/light mode)                              │      │
│   └───────────────────────────┬───────────────────────────────────┘      │
│                                  │ fetch() API calls                         │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CSAT GUARDIAN CORE                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Application (api.py)                  │   │
│  │                                                                   │   │
│  │  • Serves static frontend at /ui                                 │   │
│  │  • Receives HTTP requests at /api/*                              │   │
│  │  • Routes to appropriate services                                │   │
│  │  • Returns JSON responses                                        │   │
│  └───────────────────────────┬──────────────────────────────────────┘   │
│                              │                                          │
│          ┌───────────────────┼───────────────────┐                     │
│          │                   │                   │                     │
│          ▼                   ▼                   ▼                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │  Sentiment   │    │    CSAT      │    │   Privacy    │            │
│  │  Analysis    │    │    Rules     │    │   Service    │            │
│  │  Service     │    │   Plugin     │    │  (PII Scrub) │            │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘            │
│         │                   │                                          │
│         ▼                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   AI Agent (Semantic Kernel)                     │   │
│  │                                                                  │   │
│  │  • Understands natural language questions                       │   │
│  │  • Calls appropriate plugins for case data                      │   │
│  │  • Generates helpful, contextual responses                      │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                          │
└─────────────────────────────┼──────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Azure SQL   │    │ Azure OpenAI │    │   Content    │              │
│  │  Database    │    │   (GPT-4o)   │    │   Safety     │              │
│  │              │    │              │    │              │              │
│  │ Cases, Users │    │ AI Analysis  │    │ PII Detect   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Request Flow

**Example: Engineer asks "Why is my customer frustrated on case-002?"**

```
Step 1: RECEIVE REQUEST
┌────────────────────────────────────────────────────────────┐
│ POST /api/chat                                              │
│ Body: { "message": "Why is my customer frustrated?",        │
│         "case_id": "case-002", "engineer_id": "eng-001" }  │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 2: FETCH CASE DATA
┌────────────────────────────────────────────────────────────┐
│ DfM Client → Azure SQL Database                            │
│ • Get case details (title, description, status)            │
│ • Get timeline entries (emails, notes, calls)              │
│ • Verify engineer owns this case (security check)          │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 3: SCRUB PII
┌────────────────────────────────────────────────────────────┐
│ Privacy Service                                             │
│ • Remove email addresses from text                         │
│ • Remove phone numbers                                      │
│ • Remove SSNs, credit cards, IPs                           │
│ • Optionally: Azure AI Content Safety for names/addresses  │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 4: AI ANALYSIS
┌────────────────────────────────────────────────────────────┐
│ Sentiment Service → Azure OpenAI                           │
│ • Send scrubbed text to GPT-4o                             │
│ • Receive sentiment score (0-1)                            │
│ • Get key phrases indicating frustration                   │
│ • Get specific concerns identified                         │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 5: GENERATE RESPONSE
┌────────────────────────────────────────────────────────────┐
│ AI Agent (Semantic Kernel)                                 │
│ • Combine case data with sentiment analysis                │
│ • Apply CSAT business rules                                │
│ • Generate contextual, helpful response                    │
│ • Include specific recommendations                         │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
Step 6: RETURN RESPONSE
┌────────────────────────────────────────────────────────────┐
│ Response: {                                                 │
│   "response": "Looking at case-002, I can see several      │
│                factors contributing to frustration:         │
│                1. Critical severity with $50K/hour impact  │
│                2. Last engineer communication was 2 days ago│
│                3. Customer mentioned 'unacceptable' twice   │
│                                                             │
│                Recommendation: Send immediate status update │
│                and consider escalation.",                   │
│   "case_context": { ... },                                  │
│   "suggestions": ["Update case notes", "Schedule call"]    │
│ }                                                           │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Azure Infrastructure

### Resource Group Overview

All resources are deployed in **Commercial Azure** (not Government), **Central US** region.

**Resource Group:** `CSAT_Guardian_Dev`  
**Subscription:** `a20d761d-cb36-4f83-b827-58ccdb166f39`

### Complete Resource List

| Resource | Name | Type | Purpose |
|----------|------|------|---------|
| Virtual Network | `vnet-csatguardian-dev` | Microsoft.Network/virtualNetworks | Private networking (10.100.0.0/16) |
| App Service Plan | `asp-csatguardian-dev` | Microsoft.Web/serverfarms | Linux P1v3 Premium hosting |
| App Service | `app-csatguardian-dev` | Microsoft.Web/sites | Hosts the Python FastAPI application |
| SQL Server | `sql-csatguardian-dev` | Microsoft.Sql/servers | Database server (Azure AD auth only) |
| SQL Database | `sqldb-csatguardian-dev` | Microsoft.Sql/servers/databases | Stores case data (12 tables) |
| AI Services | `ais-csatguardian-dev` | Microsoft.CognitiveServices/accounts | Azure OpenAI with GPT-4o |
| Content Safety | `csatguardcs` | Microsoft.CognitiveServices/accounts | AI-powered PII detection |
| Key Vault | `kv-csatguard-dev` | Microsoft.KeyVault/vaults | Stores secrets |
| Dev-box VM | `vm-devbox-csatguardian` | Microsoft.Compute/virtualMachines | Windows 11 for testing |

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VIRTUAL NETWORK: vnet-csatguardian-dev                   │
│                         Address Space: 10.100.0.0/16                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    snet-appservice (10.100.1.0/24)                    │ │
│  │                                                                        │ │
│  │   ┌────────────────────────────────────────────────────────────────┐  │ │
│  │   │              App Service: app-csatguardian-dev                 │  │ │
│  │   │                                                                 │  │ │
│  │   │   • VNet Integration enabled                                   │  │ │
│  │   │   • Routes all traffic through VNet                           │  │ │
│  │   │   • Can reach private endpoints                                │  │ │
│  │   └────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│                                      │ (VNet Integration)                   │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │               snet-private-endpoints (10.100.2.0/24)                  │ │
│  │                                                                        │ │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │ │
│  │   │   SQL Server    │  │   Key Vault     │  │   AI Services   │      │ │
│  │   │  Private EP     │  │  Private EP     │  │  Private EP     │      │ │
│  │   │                 │  │                 │  │                 │      │ │
│  │   │  10.100.2.4     │  │  10.100.2.5     │  │  10.100.2.6     │      │ │
│  │   └─────────────────┘  └─────────────────┘  └─────────────────┘      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    snet-devbox (10.100.3.0/24)                        │ │
│  │                                                                        │ │
│  │   ┌────────────────────────────────────────────────────────────────┐  │ │
│  │   │                vm-devbox-csatguardian (Windows 11)             │  │ │
│  │   │                                                                 │  │ │
│  │   │   • Used for testing from within VNet                          │  │ │
│  │   │   • Can reach App Service and all private endpoints           │  │ │
│  │   └────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                   AzureBastionSubnet (10.100.4.0/26)                  │ │
│  │                                                                        │ │
│  │   Azure Bastion for secure RDP access to VM (no public IP needed)    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

Private DNS Zones (ensure internal name resolution):
• privatelink.database.windows.net → SQL Server
• privatelink.vaultcore.azure.net → Key Vault  
• privatelink.cognitiveservices.azure.com → AI Services
```

### Security Features

| Feature | Implementation | Why It Matters |
|---------|---------------|----------------|
| **Private Endpoints** | All PaaS services accessed via VNet only | No public internet exposure |
| **Managed Identity** | App Service uses MSI for all Azure services | No passwords in code or config |
| **Azure AD Only** | SQL Server requires Azure AD authentication | No SQL authentication (more secure) |
| **PII Scrubbing** | Two-layer approach before any AI calls | Protects customer data |
| **Key Vault** | All secrets stored in vault, accessed via MSI | Centralized secret management |

---

## 5. Complete File Inventory

### Root Directory

| File | Type | Purpose | Who Should Read |
|------|------|---------|-----------------|
| `README.md` | Documentation | Project overview and quick start | Everyone |
| `SESSION_STATE.md` | Documentation | Current dev status for AI assistants | AI assistants, developers |
| `.env.example` | Configuration | Template for environment variables | Developers |
| `.gitignore` | Git config | Files excluded from version control | Developers |
| `Dockerfile` | Container | Build instructions for Docker image | DevOps |
| `deploy.zip` | Artifact | Deployment package (gitignored) | - |
| `deploy.b64` | Artifact | Base64-encoded deployment (legacy) | - |

### /src (Source Code)

| File | Lines | Purpose | Key Contents |
|------|-------|---------|--------------|
| `api.py` | ~805 | REST API endpoints | FastAPI app, all HTTP handlers |
| `config.py` | ~707 | Configuration management | Settings classes, env var loading |
| `models.py` | ~677 | Data structures | Case, Engineer, Alert, etc. |
| `database.py` | ~754 | Async DB operations | SQLAlchemy ORM, DB manager |
| `db_sync.py` | ~457 | Sync DB operations | pyodbc, Azure SQL connection |
| `logger.py` | ~471 | Logging setup | JSON formatter, context logging |
| `main.py` | ~433 | CLI entry point | scan, monitor, chat commands |
| `monitor.py` | ~416 | Background monitoring | Case scanning orchestration |
| `sample_data.py` | ~200 | Basic test data | Simple mock cases |
| `sample_data_rich.py` | ~799 | Detailed test data | 8 test scenarios |
| `interactive_demo.py` | ~300 | Demo interface | Console-based chat demo |
| `requirements.txt` | ~103 | Python dependencies | All pip packages |
| `__init__.py` | ~5 | Package marker | Empty or minimal |

### /src/static (Frontend UI)

| File | Lines | Purpose | Key Contents |
|------|-------|---------|--------------|
| `index.html` | ~300 | Main HTML page | SPA structure, semantic markup |
| `css/styles.css` | ~2,770 | Design system | Glassmorphism, animations, Fluent Design tokens |
| `js/app.js` | ~2,793 | Frontend logic | State management, API calls, rendering |

**CSS Features (styles.css):**
| Feature | Description |
|---------|-------------|
| CSS Variables | Complete design token system for colors, spacing, shadows |
| Glassmorphism | `--glass-background`, `backdrop-filter: blur()` |
| Gradient Accents | `--gradient-primary`, `--gradient-success`, `--gradient-danger` |
| Keyframe Animations | `fadeInUp`, `slideInRight`, `shimmer`, `countUp`, `ringFill` |
| Skeleton Loading | `.skeleton` class with shimmer animation |
| Theme Support | `[data-theme="light"]` and `[data-theme="dark"]` variables |

**JavaScript Features (app.js):**
| Feature | Description |
|---------|-------------|
| `animateCounter()` | Animated number counting with easing |
| `createSentimentRing()` | SVG circular progress with gradient fills |
| `createSkeleton()` | Dynamic skeleton placeholder generation |
| `animatePageTransition()` | Staggered fade-in animations on view change |
| `calculateCSATPrediction()` | AI-like CSAT score prediction algorithm |

### /src/agent (AI Agent)

| File | Lines | Purpose | Key Contents |
|------|-------|---------|--------------|
| `guardian_agent.py` | ~640 | Conversational AI | Semantic Kernel agent, chat handling |
| `csat_rules_plugin.py` | ~612 | Business rules | 2-day, 7-day, 5-hour rule checks |
| `__init__.py` | ~5 | Package marker | Exports |

### /src/clients (External Services)

| File | Lines | Purpose | Key Contents |
|------|-------|---------|--------------|
| `dfm_client.py` | ~606 | DfM data interface | Abstract class + SQLite mock |
| `dfm_client_memory.py` | ~96 | In-memory mock | Uses sample_data_rich directly |
| `azure_sql_adapter.py` | ~89 | Azure SQL adapter | Async wrapper for db_sync |
| `teams_client.py` | ~396 | Teams notifications | Mock (prints to console) |
| `__init__.py` | ~10 | Package marker | Exports |

### /src/services (Business Logic)

| File | Lines | Purpose | Key Contents |
|------|-------|---------|--------------|
| `sentiment_service.py` | ~643 | AI sentiment analysis | Azure OpenAI integration |
| `alert_service.py` | ~435 | Alert generation | Templates, deduplication |
| `privacy.py` | ~515 | PII scrubbing | Regex + Content Safety |
| `__init__.py` | ~5 | Package marker | Exports |

### /docs (Documentation)

| File | Purpose | Audience |
|------|---------|----------|
| `ARCHITECTURE.md` | System architecture deep dive | Architects, developers |
| `FILE_REFERENCE.md` | This file! | Everyone |
| `PROJECT_PLAN.md` | Development roadmap | Project managers |
| `QUICK_REFERENCE.md` | Developer cheat sheet | Developers |
| `APPLICATION_SECURITY_REVIEW.md` | Security documentation | Security team |
| `ACCESS_GRANTS.md` | Required permissions | IT admins |
| `CSAT_REQUIREMENTS.md` | Business requirements | Product owners |
| `DFM_INTEGRATION_REQUEST.md` | API access request | DfM team |

### /infrastructure (Deployment)

| File/Folder | Purpose | Contents |
|-------------|---------|----------|
| `DEPLOYMENT_GUIDE.md` | Step-by-step deployment | Commands, troubleshooting |
| `deploy-all.ps1` | One-click deployment | PowerShell script |
| `bicep/main-commercial.bicep` | Infrastructure as Code | All Azure resources |
| `bicep/main-commercial.bicepparam` | Bicep parameters | Environment-specific values |
| `sql/001-schema-complete.sql` | Database schema | Table definitions |
| `sql/002-seed-data.sql` | Test data | Sample engineers, cases |

### /scripts (Utilities)

| File | Purpose |
|------|---------|
| `seed_database.py` | Populate database with test data |
| `test_db_connection.py` | Verify database connectivity |

---

## 6. Source Code Deep Dive

### api.py - The Main Application

**What it is:** The heart of the application. This is the web server that receives all requests.

**Framework:** FastAPI - a modern Python web framework that's fast and auto-generates documentation.

**Structure:**

```python
# SECTION 1: Imports and Setup
from fastapi import FastAPI, HTTPException
app = FastAPI(title="CSAT Guardian API")

# SECTION 2: Request/Response Models (what data looks like)
class ChatRequest(BaseModel):
    message: str           # The user's question
    case_id: Optional[str] # Which case they're asking about
    engineer_id: str       # Who is asking

class ChatResponse(BaseModel):
    response: str          # The AI's answer
    suggestions: List[str] # Suggested follow-up actions

# SECTION 3: Application State (global services)
class AppState:
    dfm_client = None           # Gets case data
    sentiment_service = None    # Analyzes sentiment
    initialized: bool = False

# SECTION 4: Lifecycle (startup and shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ON STARTUP: Initialize all services
    app_state.dfm_client = await get_azure_sql_adapter()
    app_state.sentiment_service = SentimentAnalysisService()
    yield
    # ON SHUTDOWN: Clean up connections
    await app_state.dfm_client.close()

# SECTION 5: Endpoints (the actual API)
@app.get("/api/health")
async def health_check():
    """Returns status of all services"""
    return {"status": "healthy", "services": {...}}

@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get details of a specific case"""
    case = await app_state.dfm_client.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with the AI agent"""
    agent = CSATGuardianAgent(engineer_id=request.engineer_id)
    response = await agent.chat(request.message, request.case_id)
    return ChatResponse(response=response, suggestions=[...])
```

**Key Endpoints Explained:**

| Endpoint | What It Does | Example Use |
|----------|--------------|-------------|
| `GET /` | Basic health check | Load balancer checking if app is alive |
| `GET /api/health` | Detailed service status | Monitoring dashboard |
| `GET /api/engineers` | List all engineers | Populate dropdown in UI |
| `GET /api/cases` | List cases with filters | Dashboard view |
| `GET /api/cases/{id}` | Single case details | Case detail page |
| `POST /api/analyze/{id}` | Run sentiment analysis | "Analyze" button click |
| `POST /api/chat` | Chat with AI | Chat interface |
| `POST /api/test-pii` | Test PII scrubbing | Development verification |

---

### config.py - Configuration Management

**What it is:** Loads all application settings from environment variables and Azure Key Vault.

**Why it matters:** Settings should never be hardcoded. This file provides a single source of truth.

**How configuration loading works:**

```python
def get_config_value(env_var_name, keyvault_secret_name, default):
    """
    Load a configuration value with fallback chain:
    
    1. First, check environment variable (for local development)
    2. If not found, check Azure Key Vault (for production)
    3. If still not found, use the default value
    """
    # Try environment variable first
    value = os.getenv(env_var_name)
    if value:
        return value
    
    # Try Key Vault if secret name provided
    if keyvault_secret_name:
        value = get_secret_from_keyvault(keyvault_secret_name)
        if value:
            return value
    
    # Fall back to default
    return default
```

**Configuration Classes:**

| Class | What It Configures |
|-------|-------------------|
| `AzureOpenAIConfig` | AI service endpoint, deployment name, API version |
| `DatabaseConfig` | SQL connection string |
| `ContentSafetyConfig` | PII detection service settings |
| `AlertThresholds` | When to trigger alerts (e.g., 7 days) |
| `FeatureFlags` | Toggle features on/off (e.g., use_mock_dfm) |
| `AppConfig` | Container for all above |

---

### models.py - Data Structures

**What it is:** Defines the "shape" of all data in the application using Pydantic.

**Why Pydantic:** Automatically validates data (wrong type = error), generates documentation, and provides IDE autocomplete.

**Core Models:**

```python
class Engineer(BaseModel):
    """
    A support engineer who handles cases.
    
    Attributes:
        id: Unique identifier (e.g., "eng-001")
        name: Display name (e.g., "John Smith")
        email: Work email (e.g., "jsmith@microsoft.com")
        teams_id: Optional Teams user ID for notifications
    """
    id: str
    name: str
    email: str
    teams_id: Optional[str] = None

class Case(BaseModel):
    """
    A support case from DfM.
    
    This is the main data structure that CSAT Guardian monitors.
    Contains case metadata and a timeline of all activities.
    """
    id: str                    # e.g., "case-002"
    title: str                 # e.g., "Production SQL down"
    description: str           # Initial problem description
    status: CaseStatus         # active, resolved, etc.
    severity: CaseSeverity     # sev_a (critical) to sev_d (low)
    created_on: datetime       # When case was opened
    modified_on: datetime      # Last update time
    owner: Engineer            # Assigned engineer
    customer: Customer         # Who opened the case
    timeline: List[TimelineEntry]  # All notes, emails, calls
    
    @property
    def days_since_last_note(self) -> float:
        """Calculate days since last case note was added."""
        notes = [e for e in self.timeline if e.entry_type == "note"]
        if not notes:
            return self.days_since_creation
        latest = max(notes, key=lambda x: x.created_on)
        return (datetime.utcnow() - latest.created_on).days
```

**Enumerations (Fixed Lists):**

```python
class CaseSeverity(str, Enum):
    """
    Case severity levels matching DfM terminology.
    """
    SEV_A = "sev_a"  # Critical - Production down
    SEV_B = "sev_b"  # High - Major impact
    SEV_C = "sev_c"  # Medium - Moderate impact
    SEV_D = "sev_d"  # Low - Minimal impact

class SentimentLabel(str, Enum):
    """
    Sentiment categories from AI analysis.
    """
    POSITIVE = "positive"  # Score > 0.6 (customer happy)
    NEUTRAL = "neutral"    # Score 0.4-0.6 (customer okay)
    NEGATIVE = "negative"  # Score < 0.4 (customer frustrated)
```

---

### services/privacy.py - PII Protection

**What it is:** Removes personally identifiable information before any text goes to AI.

**Why this is critical:** We cannot send customer emails, phone numbers, or SSNs to Azure OpenAI.

**Two-Layer Approach:**

| Layer | What It Catches | Speed | How It Works |
|-------|-----------------|-------|--------------|
| **Regex** | Emails, phones, SSNs, IPs, credit cards | ~0ms | Pattern matching |
| **Content Safety** | Names, addresses, contextual PII | +100-300ms | AI-powered |

**Example Transformation:**

```
BEFORE:
"Hi, my name is John Smith. Call me at 555-123-4567 or 
email john.smith@contoso.com. My SSN is 123-45-6789."

AFTER:
"Hi, my name is [NAME_REDACTED]. Call me at [PHONE_REDACTED] or 
email [EMAIL_REDACTED]. My SSN is [SSN_REDACTED]."
```

**Regex Patterns:**

```python
# Email addresses
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# US phone numbers (multiple formats)
PHONE_PATTERN = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

# Social Security Numbers
SSN_PATTERN = r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'

# Credit card numbers (basic)
CREDIT_CARD_PATTERN = r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'
```

---

### agent/guardian_agent.py - The AI Brain

**What it is:** The conversational AI agent built on Microsoft's Semantic Kernel framework.

**How it works:**

1. **Receives** natural language questions from engineers
2. **Understands** the intent using GPT-4o
3. **Calls plugins** to get data (case details, sentiment, rules)
4. **Generates** helpful, contextual responses

**Plugin Architecture:**

```python
class CasePlugin:
    """
    Plugin that provides case data to the AI agent.
    
    The agent can call these functions to get information:
    - get_case_summary: Overview of a case
    - analyze_case_sentiment: Sentiment analysis results
    - get_recommendations: What actions to take
    - list_my_cases: All cases for the engineer
    """
    
    @kernel_function(
        name="get_case_summary",
        description="Get a summary of a specific case"
    )
    async def get_case_summary(self, case_id: str) -> str:
        # Fetch case from database
        case = await self.dfm_client.get_case(case_id)
        
        # Security check: only allow access to own cases
        if case.owner.id != self.current_engineer_id:
            return "You don't have access to this case."
        
        # Return formatted summary
        return f"""
        📋 Case {case_id}
        Title: {case.title}
        Status: {case.status}
        Days Open: {case.days_since_creation}
        Last Update: {case.days_since_last_note} days ago
        """
```

**Conversation Example:**

```
Engineer: "How are my cases doing?"

Agent: (internally calls list_my_cases plugin)

Agent: "📂 You have 4 active cases:

🚨 case-002 - Production SQL down (CRITICAL)
   ⚠️ Last update: 3 days ago - NEEDS ATTENTION

⚠️ case-004 - AKS pod failures (HIGH)  
   Last update: 12 hours ago

✅ case-001 - Azure AD B2C config (MEDIUM)
   Last update: 4 hours ago

✅ case-005 - Synapse cost optimization (MEDIUM)
   Last update: 3 days ago - approaching 7-day limit

Would you like me to analyze any specific case?"
```

---

### agent/csat_rules_plugin.py - Business Rules Engine

**What it is:** Encodes the CSS CSAT business rules so the agent can check compliance.

**Rules Implemented:**

| Rule | Check | Warning | Breach |
|------|-------|---------|--------|
| **2-Day Communication** | Days since last customer contact | 2 days | 3 days |
| **7-Day Notes** | Days since last case note | 5 days | 7 days |
| **5-Hour Email-to-Notes** | Hours between email sent and note added | 5 hours | - |

**Code Example:**

```python
@kernel_function(
    name="check_csat_rules",
    description="Check a case against all CSAT rules"
)
async def check_csat_rules(self, case_id: str) -> str:
    case = await self.dfm_client.get_case(case_id)
    violations = []
    
    # Check 7-day notes rule
    days_since_note = case.days_since_last_note
    if days_since_note >= 7:
        violations.append({
            "rule": "7-Day Notes",
            "severity": "BREACH",
            "exceeded_by": f"{days_since_note - 7:.1f} days",
            "recommendation": "Add a case note immediately"
        })
    elif days_since_note >= 5:
        violations.append({
            "rule": "7-Day Notes",
            "severity": "WARNING",
            "exceeded_by": f"approaching ({days_since_note:.1f} days)",
            "recommendation": "Plan to add a note within 2 days"
        })
    
    # Check 2-day communication rule
    # ... similar logic ...
    
    if not violations:
        return "✅ All CSAT rules are being followed!"
    else:
        return format_violations(violations)
```

---

### services/sentiment_service.py - AI Sentiment Analysis

**What it is:** Uses Azure OpenAI to analyze customer communications for sentiment.

**How it works:**

1. Takes case description and/or timeline entries
2. Scrubs PII from the text
3. Sends to GPT-4o with a specialized prompt
4. Parses the response into a structured result

**Sentiment Scoring:**

| Score Range | Label | Meaning |
|-------------|-------|---------|
| 0.0 - 0.4 | NEGATIVE | Customer is frustrated/angry |
| 0.4 - 0.6 | NEUTRAL | Customer is neither happy nor upset |
| 0.6 - 1.0 | POSITIVE | Customer is satisfied |

**What the AI Looks For:**

- **Frustration indicators:** "unacceptable", "waiting for days", "still not working"
- **Urgency markers:** "critical", "production down", "revenue loss"
- **Positive signals:** "thanks", "great help", "working now"

---

## 7. Data Flow Diagrams

### Authentication Flow (MSI)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MANAGED IDENTITY AUTHENTICATION                          │
│                                                                              │
│   ┌─────────────┐                                                           │
│   │ App Service │                                                           │
│   │             │ ──1. Request token for SQL scope──▶ ┌─────────────────┐  │
│   │ (has MSI    │                                      │  Azure AD       │  │
│   │  enabled)   │ ◀──2. Return access token──────────  │  Token Service  │  │
│   └──────┬──────┘                                      └─────────────────┘  │
│          │                                                                   │
│          │ 3. Connect with access token                                     │
│          │    (no password!)                                                │
│          ▼                                                                   │
│   ┌─────────────┐                                                           │
│   │ Azure SQL   │                                                           │
│   │             │ 4. Validate token against Azure AD                        │
│   │ (AD-only    │ 5. If valid, allow connection                            │
│   │  auth)      │                                                           │
│   └─────────────┘                                                           │
│                                                                              │
│   BENEFITS:                                                                  │
│   • No passwords in code or config files                                    │
│   • Tokens expire automatically (short-lived)                               │
│   • Azure handles credential rotation                                       │
│   • Audit trail in Azure AD                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PII Scrubbing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PII SCRUBBING PIPELINE                              │
│                                                                              │
│  ORIGINAL TEXT                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ "Hi, my name is John Smith. Email me at john@contoso.com or call      │ │
│  │ 555-123-4567. My SSN is 123-45-6789 for identity verification."       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│                                       ▼                                      │
│                            ┌──────────────────┐                             │
│                            │  LAYER 1: REGEX  │                             │
│                            │  (< 1ms)         │                             │
│                            │                  │                             │
│                            │  Patterns:       │                             │
│                            │  • Email         │                             │
│                            │  • Phone         │                             │
│                            │  • SSN           │                             │
│                            │  • Credit Card   │                             │
│                            │  • IP Address    │                             │
│                            └────────┬─────────┘                             │
│                                     │                                        │
│                                     ▼                                        │
│  AFTER REGEX                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ "Hi, my name is John Smith. Email me at [EMAIL_REDACTED] or call      │ │
│  │ [PHONE_REDACTED]. My SSN is [SSN_REDACTED] for identity verification."│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│                                       ▼                                      │
│                      ┌────────────────────────────────┐                     │
│                      │  LAYER 2: CONTENT SAFETY (AI)  │                     │
│                      │  (100-300ms, optional)         │                     │
│                      │                                │                     │
│                      │  Detects:                      │                     │
│                      │  • Names (John Smith)          │                     │
│                      │  • Addresses                   │                     │
│                      │  • Contextual PII              │                     │
│                      └────────────────┬───────────────┘                     │
│                                       │                                      │
│                                       ▼                                      │
│  AFTER CONTENT SAFETY                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ "Hi, my name is [NAME_REDACTED]. Email me at [EMAIL_REDACTED] or call │ │
│  │ [PHONE_REDACTED]. My SSN is [SSN_REDACTED] for identity verification."│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│                                       ▼                                      │
│                              ┌─────────────────┐                            │
│                              │  AZURE OPENAI   │                            │
│                              │  (GPT-4o)       │                            │
│                              │                 │                            │
│                              │  Receives NO    │                            │
│                              │  real PII ✓     │                            │
│                              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY LAYERS                                    │
│                                                                              │
│  LAYER 1: NETWORK ISOLATION                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • All resources in private VNet (no public IPs)                        │ │
│  │ • Private Endpoints for all PaaS services                             │ │
│  │ • App Service accessible only via VNet or specific IPs                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  LAYER 2: IDENTITY                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • Managed Identity (MSI) for all Azure service authentication         │ │
│  │ • Azure AD-only authentication for SQL Server                         │ │
│  │ • No passwords or API keys in code                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  LAYER 3: DATA PROTECTION                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • PII scrubbed before any AI processing                               │ │
│  │ • Secrets stored in Key Vault (RBAC protected)                        │ │
│  │ • TLS 1.2+ for all connections                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  LAYER 4: APPLICATION                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ • Engineers can only access their own cases                           │ │
│  │ • Input validation on all endpoints                                   │ │
│  │ • Structured logging for audit                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Security Controls

| Control | Implementation | Risk Mitigated |
|---------|---------------|----------------|
| **Network Isolation** | Private endpoints, VNet integration | Data exfiltration |
| **MSI Authentication** | DefaultAzureCredential | Credential theft |
| **PII Scrubbing** | Regex + Content Safety | Data leakage to AI |
| **Azure AD Only** | SQL AD authentication | Brute force attacks |
| **Key Vault** | Centralized secrets | Configuration exposure |
| **RBAC** | Role-based access to resources | Unauthorized access |

---

## 9. Deployment Guide Summary

### Prerequisites

1. **Azure subscription** with Owner or Contributor access
2. **Azure Cloud Shell** (Cloud Shell has all required tools)
3. **GitHub access** to clone the repository

### Deployment Steps (Summary)

```bash
# 1. Clone repository in Cloud Shell
cd ~
gh repo clone kmonteagudo_microsoft/csat-guardian
cd csat-guardian
git checkout develop

# 2. Create deployment package
zip -r deploy.zip src

# 3. Deploy to Azure App Service
az webapp deploy \
  --resource-group CSAT_Guardian_Dev \
  --name app-csatguardian-dev \
  --src-path deploy.zip \
  --type zip \
  --clean

# 4. Verify deployment
az vm run-command invoke \
  --resource-group CSAT_Guardian_Dev \
  --name vm-devbox-csatguardian \
  --command-id RunPowerShellScript \
  --scripts "Invoke-RestMethod -Uri 'https://app-csatguardian-dev.azurewebsites.net/api/health'"
```

### Startup Command

The App Service is configured with this startup command:

```bash
cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

This:
1. Changes to the source directory
2. Installs Python dependencies
3. Starts the FastAPI server on port 8000

---

## 10. Glossary of Terms

| Term | Definition |
|------|------------|
| **API** | Application Programming Interface - a way for programs to communicate |
| **App Service** | Azure's managed web hosting platform |
| **Bicep** | Azure's infrastructure-as-code language (like Terraform) |
| **CSAT** | Customer Satisfaction (a score from 1-5 typically) |
| **CSS** | Customer Service & Support (Microsoft organization) |
| **DfM** | Dynamics for Microsoft - the case management system |
| **Endpoint** | A URL that accepts requests (e.g., `/api/cases`) |
| **FastAPI** | A modern Python web framework |
| **GPT-4o** | OpenAI's latest AI model (the "o" is for "omni") |
| **GSX** | Government Support Engineers |
| **JSON** | JavaScript Object Notation - a data format |
| **Key Vault** | Azure's secret management service |
| **Kusto** | Azure Data Explorer query language |
| **MSI** | Managed Service Identity - passwordless Azure authentication |
| **ORM** | Object-Relational Mapping - maps code objects to database tables |
| **PII** | Personally Identifiable Information (names, SSNs, etc.) |
| **Private Endpoint** | Azure feature that gives a private IP to a PaaS service |
| **Pydantic** | Python library for data validation |
| **REST** | Representational State Transfer - an API architecture style |
| **Semantic Kernel** | Microsoft's AI orchestration framework |
| **Sentiment** | The emotional tone of text (positive/neutral/negative) |
| **SQLAlchemy** | Python SQL toolkit and ORM |
| **VNet** | Virtual Network - Azure's private networking |

---

## 11. Quick Reference Card

### Key URLs

| Resource | URL |
|----------|-----|
| App Service | https://app-csatguardian-dev.azurewebsites.net |
| API Documentation | https://app-csatguardian-dev.azurewebsites.net/docs |
| Kudu (SCM) | https://app-csatguardian-dev.scm.azurewebsites.net |

### Common Commands

```bash
# Deploy code (from Cloud Shell)
cd ~/csat-guardian && git pull origin develop
zip -r deploy.zip src
az webapp deploy --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --src-path deploy.zip --type zip --clean

# Restart app
az webapp restart --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev

# View logs
az webapp log tail --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev

# Test from DevBox
az vm run-command invoke --resource-group CSAT_Guardian_Dev --name vm-devbox-csatguardian --command-id RunPowerShellScript --scripts "Invoke-RestMethod -Uri 'https://app-csatguardian-dev.azurewebsites.net/api/health'"
```

### API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if app is healthy |
| `/api/engineers` | GET | List all engineers |
| `/api/cases` | GET | List cases (filter by engineer_id, status) |
| `/api/cases/{id}` | GET | Get single case with timeline |
| `/api/analyze/{id}` | POST | Run AI sentiment analysis |
| `/api/chat` | POST | Chat with the AI agent |
| `/api/test-pii` | POST | Test PII scrubbing |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | AI Services URL |
| `AZURE_OPENAI_DEPLOYMENT` | Model name (gpt-4o) |
| `DATABASE_CONNECTION_STRING` | SQL connection string |
| `ENABLE_CONTENT_SAFETY_PII` | Enable AI PII detection |
| `CONTENT_SAFETY_ENDPOINT` | Content Safety URL |

### Key Resource IDs

| Resource | ID/Value |
|----------|----------|
| Subscription | a20d761d-cb36-4f83-b827-58ccdb166f39 |
| Resource Group | CSAT_Guardian_Dev |
| App MSI Object ID | 7b0f0d42-0f23-48cd-b982-41abad5f1927 |
| VNet Address Space | 10.100.0.0/16 |

---

*Document Version: 2.0*  
*Last Updated: January 28, 2026*  
*Author: Kyle Monteagudo with GitHub Copilot*
