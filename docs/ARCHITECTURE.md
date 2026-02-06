# CSAT Guardian - Architecture Overview

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Kyle Monteagudo | Initial architecture document |
| 2.0 | 2026-01-24 | Kyle Monteagudo | **Major update**: Private networking architecture with VNet, Private Endpoints, App Service |
| 3.0 | 2026-01-24 | Kyle Monteagudo | Updated for Commercial Azure (Central US), AI Foundry (AI Services + AI Hub) |
| 4.0 | 2026-01-25 | Kyle Monteagudo | Fixed database concurrency, all analysis features working, Kudu deployment method |
| 5.0 | 2026-01-26 | Kyle Monteagudo | **MSI Authentication**: Full managed identity implementation for SQL and OpenAI |
| 6.0 | 2026-01-27 | Kyle Monteagudo | **DfM via Kusto**: DfM data is in Azure Data Explorer (ADX), not D365 OData. Teams Bot requires Azure Function gateway |
| 7.0 | 2026-02-03 | Kyle Monteagudo | **Static Frontend**: Microsoft Learn-style UI with HTML/CSS/JS served by FastAPI at `/ui` |
| 8.0 | 2026-02-04 | Kyle Monteagudo | **Security Hardening**: Local auth DISABLED on all services (SQL, OpenAI, Content Safety). All auth via Managed Identity only |
| 9.0 | 2026-02-05 | Kyle Monteagudo | **UI Enhancement**: Glassmorphism design, animated sentiment rings, skeleton loading, micro-interactions, gradient accents, page transitions |
| 10.0 | 2026-02-05 | Kyle Monteagudo | **ULTRA PREMIUM UI**: Mobile-first responsive design, case filtering/search, export system (CSV/PDF/JSON), particle effects, aurora backgrounds, 3D transforms |

---

## Quick Links

> **📊 For visual diagrams (security reviews, stakeholder presentations):**  
> See [Infrastructure Diagrams](diagrams/infrastructure.md) - includes data flow, auth flow, and network security diagrams in Mermaid format.

---

## 1. Executive Summary

CSAT Guardian is a cloud-native, AI-powered support case monitoring system designed to improve customer satisfaction by:
- Detecting negative customer sentiment before it escalates
- Ensuring timely case updates (7-day compliance)
- Providing engineers with actionable coaching recommendations

> **⚠️ IMPORTANT: Commercial Azure with Private Networking**
> 
> This application is deployed in **Commercial Azure** (Central US) with **private endpoints**.
> All Azure-to-Azure communication is private (no public internet).

**Key Architectural Principles:**
1. **Cloud-First**: All components run in Azure Commercial, no local hosting
2. **Private by Default**: All backend services use Private Endpoints
3. **No Secrets in Code**: All credentials stored in Azure Key Vault
4. **API-Based Access**: Even sample data accessed via API patterns
5. **AI Foundry**: Uses AI Hub + AI Services instead of standalone Azure OpenAI

---

## 2. High-Level Architecture

### Frontend (New - February 2026)

The application now includes a **Microsoft Learn-style static frontend** served directly by FastAPI:

- **Access URL**: `https://app-csatguardian-dev.azurewebsites.net/ui`
- **Technology**: Pure HTML/CSS/JavaScript (no build step required)
- **Design**: Fluent Design System with dark theme
- **Features**: Engineer Dashboard, Manager Dashboard, Sentiment Analysis, AI Chat

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│             CSAT GUARDIAN ARCHITECTURE (AZURE COMMERCIAL - PRIVATE NETWORKING)      │
└────────────────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────────────────┐
                            │       User Browser          │
                            │   https://.../ui            │
                            └─────────────┬───────────────┘
                                          │ HTTPS
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       AZURE COMMERCIAL CLOUD (Central US)                           │
│                        Resource Group: CSAT_Guardian_Dev                            │
│                                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                    VIRTUAL NETWORK (vnet-csatguardian-dev)                  │    │
│  │                           Address Space: 10.100.0.0/16                      │    │
│  │                                                                             │    │
│  │  ┌─────────────────────────────┐   ┌──────────────────────────────────┐   │    │
│  │  │   snet-appservice           │   │   snet-privateendpoints          │   │    │
│  │  │   10.100.1.0/24             │   │   10.100.2.0/24                  │   │    │
│  │  │                             │   │                                  │   │    │
│  │  │  ┌───────────────────────┐  │   │  ┌─────────────────────────┐    │   │    │
│  │  │  │    App Service        │  │   │  │  Private Endpoints      │    │   │    │
│  │  │  │    (FastAPI POC)      │──┼───┼──│  ├─ pep-sql              │    │   │    │
│  │  │  │    Python 3.11        │  │   │  │  ├─ pep-kv               │    │   │    │
│  │  │  └───────────────────────┘  │   │  │  └─ pep-ais              │    │   │    │
│  │  │                             │   │  └─────────────────────────┘    │   │    │
│  │  └─────────────────────────────┘   └──────────────────────────────────┘   │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                          │
│         ┌────────────────────────────────┼────────────────────────────────────┐    │
│         │                                │                                    │    │
│         ▼                                ▼                                    ▼    │
│  ┌───────────────┐               ┌───────────────┐               ┌───────────────┐ │
│  │   Azure SQL   │               │   Key Vault   │               │  AI Services  │ │
│  │   (Private)   │               │   (Private)   │               │   (Private)   │ │
│  │               │               │               │               │               │ │
│  │ sql-csat...   │               │ kv-csatguard  │               │ ais-csat...   │ │
│  └───────────────┘               └───────────────┘               └───────────────┘ │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                         PRIVATE DNS ZONES                                      │ │
│  │  privatelink.database.windows.net        ← SQL Server                         │ │
│  │  privatelink.vaultcore.azure.net         ← Key Vault                          │ │
│  │  privatelink.cognitiveservices.azure.com ← AI Services                        │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘

                                          │
                                          │ Future: Teams Bot
                                          ▼
                              ┌───────────────────────┐
                              │   Microsoft Teams     │
                              │   (via Bot Service)   │
                              └───────────────────────┘
```

---

## 3. Deployed Resources

### Resource Group: `CSAT_Guardian_Dev`

| Resource | Name | Type | Notes |
|----------|------|------|-------|
| **VNet** | `vnet-csatguardian-dev` | Virtual Network | 10.100.0.0/16 |
| **App Service Plan** | `asp-csatguardian-dev` | Linux P1v3 | Python 3.11 |
| **App Service** | `app-csatguardian-dev` | Web App | FastAPI + Semantic Kernel with VNet integration |
| **AI Services** | `ais-csatguardian-dev` | AI Services | GPT-4o deployment |
| **SQL Server** | `sql-csatguardian-dev` | Azure SQL | Logical server (private endpoint only) |
| **SQL Database** | `sqldb-csatguardian-dev` | Azure SQL DB | 12 tables, 8 test cases |
| **Key Vault** | `kv-csatguard-dev` | Key Vault | RBAC-enabled, managed identity access |
| **Bastion** | `bas-csatguardian-dev` | Azure Bastion | Secure VM access |
| **Dev VM** | `vm-devbox-csatguardian` | Windows 11 VM | Testing from VNet |

### Private Endpoints

| Endpoint | Target | Private IP | DNS Zone |
|----------|--------|-----------|----------|
| `pep-csatguardian-sql` | SQL Server | 10.100.2.x | privatelink.database.windows.net |
| `pep-csatguardian-kv` | Key Vault | 10.100.2.x | privatelink.vaultcore.azure.net |
| `pep-csatguardian-ais` | AI Services | 10.100.2.x | privatelink.cognitiveservices.azure.com |

### Subnets

| Subnet | Address Range | Purpose |
|--------|--------------|---------|
| `snet-appservice` | 10.100.1.0/24 | App Service VNet integration |
| `snet-private-endpoints` | 10.100.2.0/24 | Private Endpoints |
| `snet-devbox` | 10.100.3.0/24 | Development VM |
| `AzureBastionSubnet` | 10.100.4.0/26 | Azure Bastion |

---

## 4. Component Details

### 4.1 App Service (FastAPI + Static Frontend + Semantic Kernel)

**Purpose**: Hosts the FastAPI backend with AI-powered CSAT coaching agent AND the Microsoft Learn-style frontend UI

**Why App Service?**
- Simpler deployment for Python apps
- Native VNet integration support
- Managed identity for Key Vault access
- Static file serving for frontend (no separate web server needed)

**Configuration:**
```
Plan: asp-csatguardian-dev (Linux P1v3)
Runtime: Python 3.11
VNet Integration: snet-appservice
Route All: Enabled (all outbound through VNet)
URL: https://app-csatguardian-dev.azurewebsites.net
UI URL: https://app-csatguardian-dev.azurewebsites.net/ui
Startup Command: cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Frontend Stack:**
| Component | Technology | Location | Lines |
|-----------|------------|----------|-------|
| HTML | Static HTML5 | `src/static/index.html` | ~180 |
| Styling | CSS3 (Fluent Design + Glassmorphism + Aurora) | `src/static/css/styles.css` | ~4,500 |
| Logic | Vanilla JavaScript (ES6+) | `src/static/js/app.js` | ~3,600 |
| Icons | Fluent UI Icons + Emoji | Embedded in JS | - |

**UI Features v10.0 (ULTRA PREMIUM):**
| Feature | Description |
|---------|-------------|
| **Mobile-First Design** | Full responsive layout with hamburger menu for mobile |
| **Slide-Out Mobile Menu** | Touch-friendly navigation with swipe-to-close |
| **Case Filtering/Search** | Filter by severity, sentiment status, days inactive, text search |
| **Quick Filter Pills** | One-click filters for Critical/At-Risk/Healthy cases |
| **Export System** | Export to CSV, PDF report, or JSON formats |
| **Particle Canvas** | Animated interconnected particle network background |
| **Aurora Background** | Morphing gradient blob animations |
| **Glassmorphism** | Enhanced frosted glass effect with deeper blur |
| **Animated Sentiment Rings** | SVG-based circular progress with gradient fills |
| **Animated Counters** | Numbers that count up with easing animations |
| **Skeleton Loading** | Shimmer placeholders while data loads |
| **Micro-interactions** | Button ripples, card hover lifts, focus states |
| **Gradient Text Animation** | Animated color-shifting text effects |
| **Neon Border Effects** | Glowing borders on hover |
| **3D Card Transforms** | Perspective-based card tilt effects |
| **Page Transitions** | Smooth fade-in-up animations with staggered delays |
| **Confetti Celebration** | Success animation on exports |
| **Theme Support** | Dark/Light mode with CSS variables |
| **Touch Optimized** | 44px min-touch targets, no zoom on input focus |
| **Safe Area Support** | Notch-friendly layout for modern phones |
| **Print Styles** | Clean print layout for PDF export |

**Deployed Endpoints:**
| Endpoint | Status | Description |
|----------|--------|-------------|
| `/ui` | ✅ Working | **Static frontend UI** |
| `/api/health` | ✅ Working | Health check |
| `/api/cases` | ✅ Working | List cases from Azure SQL |
| `/api/analyze/{id}` | ✅ Working | AI sentiment analysis |
| `/api/chat` | ✅ Working | Semantic Kernel agent chat |

### 4.2 Azure Key Vault

**Purpose**: Securely stores all secrets and credentials

**Deployed Instance:** `kv-csatguard-dev.vault.azure.net`

**Secrets Stored:**
| Secret Name | Description | Status |
|-------------|-------------|--------|
| `azure-openai-key` | Azure OpenAI API key | ✅ Stored |

**Access Pattern:**
```
App Service (Managed Identity)
    │
    │ VNet Integration → Private Endpoint
    ▼
Key Vault (via @Microsoft.KeyVault reference)
    │
    │ RBAC: Key Vault Secrets User
    ▼
Application Settings (auto-resolved)
```

### 4.3 Azure SQL Database

**Purpose**: Stores case data, alert history, and analytics

**Deployed Instances:**
- Server: `sql-csatguardian-dev.database.windows.net`
- Database: `sqldb-csatguardian-dev`
- Admin: `sqladmin`
- Access: Private endpoint only (no public access)

**Database Schema (12 Tables):**
```sql
-- Core entities
engineers           -- Support engineer profiles
customers           -- Customer information
cases               -- Support cases (8 test records)
timeline_entries    -- Case notes, emails, calls
surveys             -- CSAT survey data

-- Configuration
csat_rules          -- Compliance rules
alerts              -- Alert history
escalations         -- Escalation tracking

-- Authentication
roles, permissions, role_permissions
engineer_roles
```

### 4.4 Azure AI Services (GPT-4o)

**Purpose**: Provides AI capabilities for sentiment analysis and conversational coaching

**Deployed Instance:**
- Resource: `ais-csatguardian-dev`
- Endpoint: `https://ais-csatguardian-dev.cognitiveservices.azure.com/`
- Deployment: `gpt-4o`
- Region: Central US

**Use Cases:**
1. **Sentiment Analysis**: Classify customer communications as positive/neutral/negative
2. **CSAT Coaching**: Proactive guidance via Semantic Kernel agent with function calling
3. **Timeline Analysis**: Detect response gaps and communication patterns

---

## 5. Data Flow

### 5.1 Case Monitoring Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Timer     │────▶│   Monitor   │────▶│  Sentiment  │────▶│   Alert     │
│   Trigger   │     │   Service   │     │   Service   │     │   Service   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │   Azure     │     │   Azure     │     │   Teams     │
                    │   SQL DB    │     │   OpenAI    │     │   (Mock)    │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

**Steps:**
1. Timer triggers monitoring scan (every N minutes)
2. Monitor Service fetches active cases from Azure SQL
3. Sentiment Service analyzes each case using Azure OpenAI
4. Alert Service checks thresholds and sends alerts via Teams
5. Metrics recorded to database

### 5.2 Conversational Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Engineer  │────▶│   Teams     │────▶│   Guardian  │
│   (Chat)    │     │   Bot       │     │    Agent    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                           ┌───────────────────┼───────────────────┐
                           ▼                   ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │   Case      │     │  Sentiment  │     │    Azure    │
                    │   Plugin    │     │   Plugin    │     │   OpenAI    │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

**Steps:**
1. Engineer sends message via Teams
2. Teams Bot forwards to Guardian Agent
3. Agent uses Semantic Kernel to understand intent
4. Plugins fetch case data or run analysis
5. Response sent back to engineer

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

> **Updated January 26, 2026**: Full MSI authentication implemented and verified working.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

App Service (Managed Identity)
    │
    │ DefaultAzureCredential / ManagedIdentityCredential
    ▼
Entra ID (Microsoft Corporate Tenant)
    │
    │ OAuth2 Token (resource-specific)
    ▼
Target Services:
    ├── Azure SQL: Token with database.windows.net audience
    ├── Azure OpenAI: Token via get_bearer_token_provider()
    └── Key Vault: @Microsoft.KeyVault references auto-resolved
```

**MSI Implementation Details:**

| Service | Auth Method | Code |
|---------|-------------|------|
| Azure SQL | `DefaultAzureCredential` → `struct.pack` token | `db_sync.py:_get_msi_access_token()` |
| Azure OpenAI | `get_bearer_token_provider()` | `sentiment_service.py` |
| Semantic Kernel | `ad_token_provider` parameter | `guardian_agent.py` |

**Environment Variables:**
```
USE_SQL_MANAGED_IDENTITY=true      # Use MSI for SQL (default)
USE_OPENAI_MANAGED_IDENTITY=true   # Use MSI for OpenAI (default)
```

**Azure RBAC Configuration:**

| Resource | Principal | Role | Notes |
|----------|-----------|------|-------|
| SQL Server | App Service MSI | **SQL Admin** | Workaround - Directory Readers unavailable |
| AI Services | App Service MSI | Cognitive Services User | Standard RBAC |
| Key Vault | App Service MSI | Key Vault Secrets User | Standard RBAC |

> **⚠️ Production Note**: The App Service is currently SQL Admin because the SQL Server MSI lacks Directory Readers role in Azure AD. For production, request AAD admin to grant Directory Readers to SQL Server MSI (`04199892-389c-4531-97a7-42eda6734c28`), then demote App Service to `db_datareader`/`db_datawriter`.

**No credentials in code or config** - all authentication via Managed Identity

### 6.2 Network Security (Production)

```
                    Internet
                        │
                        ▼
                ┌───────────────┐
                │  Azure Front  │
                │    Door       │
                └───────┬───────┘
                        │ WAF Protected
                        ▼
            ┌───────────────────────┐
            │    VNet Integration   │
            │                       │
            │   ┌───────────────┐   │
            │   │  App Service  │   │
            │   └───────┬───────┘   │
            │           │           │
            │   ┌───────┴───────┐   │
            │   │    Private    │   │
            │   │   Endpoints   │   │
            │   └───────────────┘   │
            │   │   │   │   │       │
            │   ▼   ▼   ▼   ▼       │
            │  SQL KV  OAI Logs     │
            └───────────────────────┘
```

### 6.3 Secrets Management

| Environment | Secret Source | How Accessed |
|-------------|---------------|--------------|
| Local Dev | `.env.local` file (gitignored) | python-dotenv |
| CI/CD | GitHub Secrets | Injected as env vars |
| Azure | Key Vault | Managed Identity |

**Key Vault Access Control:**
- RBAC enabled (not access policies)
- App Service has "Key Vault Secrets User" role
- Developers have "Key Vault Secrets Officer" for management

---

## 7. Deployment Architecture

### 7.1 Environment Strategy

| Environment | Purpose | Data | API |
|-------------|---------|------|-----|
| **Dev** | Development & testing | Sample data | Mock |
| **Test** | Integration testing | Sample data | Mock |
| **Prod** | Production | Real DfM | Real |

### 7.2 Infrastructure as Code

All Azure resources defined in Bicep:

```
infrastructure/
├── bicep/
│   ├── main-commercial.bicep       # Complete Bicep template
│   └── main-commercial.bicepparam  # Parameters
├── deploy-all.ps1                  # All-in-one deployment script
└── DEPLOYMENT_GUIDE.md             # Step-by-step guide
```

### 7.3 Deployment Process

Deployment is manual via PowerShell script:

```powershell
# Deploy everything
.\infrastructure\deploy-all.ps1 `
    -SubscriptionId "<your-subscription-id>" `
    -ResourceGroup "CSAT_Guardian_Dev" `
    -Location "centralus"
```

---

## 8. Scalability

### 8.1 App Service Scaling

```
Plan: asp-csatguardian
Tier: B1 (Basic)
Scale: Manual (1 instance for POC)
Future: Can scale to P1v3 or Premium for auto-scale
```

**Production Scale Options:**
- Scale Up: P1v3, P2v3 (more CPU/RAM)
- Scale Out: Multiple instances with load balancing
- Auto-scale: Based on CPU, memory, or HTTP requests

### 8.2 Database Scaling

| Load | Tier | DTUs | Est. Cost |
|------|------|------|-----------|
| POC | Basic | 5 | $5/month |
| Low | Standard S0 | 10 | $15/month |
| Medium | Standard S2 | 50 | $75/month |
| High | Premium P1 | 125 | $465/month |

### 8.3 OpenAI Rate Limits

Managed via Azure OpenAI deployment capacity:
- POC: 10K tokens/min
- Production: Based on usage patterns

---

## 9. Monitoring & Observability

### 9.1 Logging Strategy

| Log Level | Usage |
|-----------|-------|
| DEBUG | Detailed troubleshooting (dev only) |
| INFO | Normal operations, case analysis |
| WARNING | Degraded service, approaching limits |
| ERROR | Failed operations, exceptions |
| CRITICAL | System failures |

### 9.2 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `scan_duration_ms` | Time to scan all cases | > 60,000 ms |
| `sentiment_api_latency_ms` | OpenAI API response time | > 5,000 ms |
| `alerts_sent_count` | Alerts sent per scan | N/A (informational) |
| `error_count` | Errors per hour | > 10/hour |

### 9.3 Dashboards

Azure Monitor workbook displaying:
- Scan execution history
- Sentiment distribution
- Alert volume trends
- Error rates

---

## 10. Disaster Recovery

| Aspect | Strategy |
|--------|----------|
| **RTO** | 4 hours (non-critical advisory service) |
| **RPO** | N/A (no critical data; can regenerate from DfM) |
| **Backup** | Azure SQL automatic backups |
| **Failover** | Redeploy from GitHub + Bicep |

---

## 11. Cost Estimate (POC)

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| App Service Plan | Linux B1 | ~$13 |
| Azure SQL | Basic (5 DTU) | ~$5 |
| Key Vault | Standard | ~$1 |
| App Insights | Free tier | $0 |
| Private Endpoints | 3 endpoints | ~$22 |
| Private DNS Zones | 3 zones | ~$1.50 |
| Azure OpenAI | Pay-per-use | ~$5-20 |
| VNet | (no cost) | $0 |
| **Total** | | **~$50-70/month** |

> **Note**: Private endpoint costs are the main addition (~$7.30/endpoint/month).
> For production, consider Premium App Service Plan for auto-scaling capabilities.

---

*Document Version: 3.0*  
*Last Updated: January 25, 2026*
