# CSAT Guardian - Getting Started Guide

> **For Newcomers:** This is your starting point. Read this first, then follow the links to dive deeper.

---

## 🎯 What is CSAT Guardian?

CSAT Guardian is an AI-powered assistant that helps Microsoft Support Engineers maintain high customer satisfaction (CSAT) scores by:

1. **Monitoring** all their open cases continuously
2. **Detecting** early signs of customer frustration using AI sentiment analysis
3. **Alerting** when cases are at risk (approaching deadlines, declining sentiment)
4. **Coaching** with specific, actionable recommendations

### Who is this for?

| Role | How CSAT Guardian Helps |
|------|------------------------|
| **Support Engineers** | Get notified before cases become problems |
| **Team Leads** | See dashboard of team CSAT health |
| **Security Team** | All PII scrubbed before AI processing |
| **DevOps** | Infrastructure-as-code, MSI auth, no secrets in code |

---

## 📚 Documentation Map

| Document | Audience | What You'll Learn |
|----------|----------|-------------------|
| [FILE_REFERENCE.md](FILE_REFERENCE.md) | **Everyone** | Complete file-by-file explanation of entire codebase |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Developers, Architects | Technical deep-dive with diagrams |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Developers | API endpoints, commands, environment variables |
| [DEPLOYMENT_GUIDE.md](../infrastructure/DEPLOYMENT_GUIDE.md) | DevOps | Step-by-step deployment instructions |
| [APPLICATION_SECURITY_REVIEW.md](APPLICATION_SECURITY_REVIEW.md) | Security | Security controls, PII handling, auth flows |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Project Managers | Roadmap, milestones, status |
| [CSAT_REQUIREMENTS.md](CSAT_REQUIREMENTS.md) | Product Owners | Business rules (2-day, 7-day, etc.) |

---

## 🚀 Quick Start (5 minutes)

### If you just want to understand the code:

1. **Read** [FILE_REFERENCE.md](FILE_REFERENCE.md) - it explains every file
2. **Browse** `/src/api.py` - the main application
3. **Check** `/src/models.py` - all data structures

### If you want to test the running application:

1. **Open** Azure Portal → CSAT_Guardian_Dev resource group
2. **Connect** to `vm-devbox-csatguardian` via Bastion
3. **Run** these PowerShell commands:

```powershell
# Health check
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"

# List cases
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/cases"

# Chat with the AI
$body = @{
    message = "How are my cases doing?"
    engineer_id = "eng-001"
} | ConvertTo-Json
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/chat" -Method Post -Body $body -ContentType "application/json"
```

### If you want to deploy changes:

1. **Clone** the repo in Azure Cloud Shell
2. **Make** your changes on the `develop` branch
3. **Run** the deployment:

```bash
cd ~/csat-guardian
git pull origin develop
zip -r deploy.zip src
az webapp deploy --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --src-path deploy.zip --type zip --clean
```

---

## 🧩 Understanding the Technology Stack

### Languages & Frameworks

| Technology | What It Does | Why We Chose It |
|------------|--------------|-----------------|
| **Python 3.11** | Main programming language | Team expertise, great AI libraries |
| **FastAPI** | Web framework | Fast, modern, auto-generates docs |
| **Semantic Kernel** | AI orchestration | Microsoft's official AI SDK |
| **Pydantic** | Data validation | Type safety, auto-documentation |
| **pyodbc** | Database driver | Best Azure SQL support |

### Azure Services

| Service | What It Does | Why It's Important |
|---------|--------------|-------------------|
| **App Service** | Hosts the application | PaaS - no servers to manage |
| **Azure SQL** | Stores case data | Enterprise database with MSI auth |
| **Azure OpenAI** | AI analysis | GPT-4o for sentiment and chat |
| **Content Safety** | PII detection | Catches names and addresses |
| **Key Vault** | Stores secrets | Centralized, audited secret management |
| **Virtual Network** | Private networking | All traffic stays in Azure |

### Authentication (No Passwords!)

```
┌─────────────────────────────────────────────────────────────────────┐
│   MANAGED IDENTITY (MSI) - HOW IT WORKS                            │
│                                                                     │
│   App Service                  Azure AD                  Azure SQL  │
│   ┌─────────┐                 ┌─────────┐              ┌─────────┐ │
│   │         │──1. Request────▶│         │              │         │ │
│   │   MSI   │     token       │ Token   │              │         │ │
│   │ enabled │◀──2. Return─────│ Service │              │         │ │
│   │         │     token       │         │              │         │ │
│   └────┬────┘                 └─────────┘              │ AD-only │ │
│        │                                               │  auth   │ │
│        └────────────3. Connect with token─────────────▶│         │ │
│                      (no password!)                    │         │ │
│                                                        └─────────┘ │
│                                                                     │
│   BENEFITS:                                                         │
│   • No passwords in code or config                                  │
│   • Tokens expire automatically                                     │
│   • Azure handles credential rotation                               │
│   • Full audit trail in Azure AD                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure Overview

```
csat-guardian/
├── 📄 README.md              # Project overview (you are here)
├── 📄 Dockerfile             # Container build instructions
│
├── 📁 src/                   # APPLICATION SOURCE CODE
│   ├── api.py                # Main FastAPI app (~800 lines)
│   ├── config.py             # Configuration loading (~700 lines)
│   ├── models.py             # Data structures (~680 lines)
│   ├── database.py           # Async database operations
│   ├── db_sync.py            # Sync database (production)
│   │
│   ├── 📁 agent/             # AI AGENT
│   │   ├── guardian_agent.py # Semantic Kernel agent
│   │   └── csat_rules_plugin.py # Business rules
│   │
│   ├── 📁 services/          # BUSINESS LOGIC
│   │   ├── sentiment_service.py # AI sentiment analysis
│   │   ├── privacy.py        # PII scrubbing (regex + AI)
│   │   └── alert_service.py  # Alert generation
│   │
│   └── 📁 clients/           # EXTERNAL INTEGRATIONS
│       ├── dfm_client.py     # DfM data abstraction
│       └── teams_client.py   # Teams notifications (mock)
│
├── 📁 docs/                  # DOCUMENTATION
│   ├── FILE_REFERENCE.md     # Complete file guide
│   ├── ARCHITECTURE.md       # Technical architecture
│   ├── QUICK_REFERENCE.md    # Developer cheat sheet
│   └── ...
│
└── 📁 infrastructure/        # DEPLOYMENT
    ├── bicep/                # Azure infrastructure-as-code
    ├── sql/                  # Database schemas
    └── DEPLOYMENT_GUIDE.md   # How to deploy
```

---

## ❓ Common Questions

### "Where is the main application code?"

→ [src/api.py](../src/api.py) - this is the FastAPI application that handles all HTTP requests.

### "How does the AI work?"

→ [src/agent/guardian_agent.py](../src/agent/guardian_agent.py) uses Microsoft's Semantic Kernel to orchestrate GPT-4o. It can call "plugins" to get data and apply business rules.

### "How is customer PII protected?"

→ [src/services/privacy.py](../src/services/privacy.py) scrubs PII using two layers:
1. **Fast regex** for obvious patterns (emails, phones, SSNs)
2. **Azure AI Content Safety** for names and contextual PII

### "What are the CSAT business rules?"

→ [CSAT_REQUIREMENTS.md](CSAT_REQUIREMENTS.md) has full details, but in brief:
- **2-Day Rule**: Contact customer at least every 2 days
- **7-Day Rule**: Update case notes at least every 7 days
- **5-Hour Rule**: Add notes within 5 hours of sending an email

### "Why can't I access the app from my laptop?"

→ The app is deployed with **private endpoints** - it's only accessible from within the Azure Virtual Network. Use the DevBox VM (via Bastion) to test.

### "How do I deploy changes?"

→ See [DEPLOYMENT_GUIDE.md](../infrastructure/DEPLOYMENT_GUIDE.md). In short:
1. Push to `develop` branch
2. In Cloud Shell: `zip -r deploy.zip src && az webapp deploy ...`

---

## 🔗 External Resources

| Resource | Link | Notes |
|----------|------|-------|
| FastAPI Docs | https://fastapi.tiangolo.com | Web framework we use |
| Semantic Kernel | https://github.com/microsoft/semantic-kernel | AI orchestration |
| Pydantic | https://docs.pydantic.dev | Data validation |
| Azure OpenAI | https://learn.microsoft.com/en-us/azure/ai-services/openai/ | AI service |
| Azure Content Safety | https://learn.microsoft.com/en-us/azure/ai-services/content-safety/ | PII detection |

---

## 📞 Getting Help

| Need | Contact |
|------|---------|
| Code questions | Kyle Monteagudo (project owner) |
| Azure access | Your IT admin for subscription permissions |
| Security review | See APPLICATION_SECURITY_REVIEW.md |

---

*Last Updated: January 28, 2026*
