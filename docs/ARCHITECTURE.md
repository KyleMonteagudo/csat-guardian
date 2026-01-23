# CSAT Guardian - Architecture Overview

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Kyle Monteagudo | Initial architecture document |
| 2.0 | 2026-01-24 | Kyle Monteagudo | **Major update**: Private networking architecture with VNet, Private Endpoints, App Service |
| 3.0 | 2026-01-25 | Kyle Monteagudo | Updated for Commercial Azure (East US) |

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
> This application is deployed in **Commercial Azure** (East US) with **private endpoints**.
> All Azure-to-Azure communication is private (no public internet).

**Key Architectural Principles:**
1. **Cloud-First**: All components run in Azure Commercial, no local hosting
2. **Private by Default**: All backend services use Private Endpoints
3. **No Secrets in Code**: All credentials stored in Azure Key Vault
4. **API-Based Access**: Even sample data accessed via API patterns
5. **VNet Integration**: App Service routes all traffic through VNet

---

## 2. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│             CSAT GUARDIAN ARCHITECTURE (AZURE COMMERCIAL - PRIVATE NETWORKING)      │
└────────────────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────────────────┐
                            │         Manual Deploy       │
                            │     (deploy-all.ps1)        │
                            └─────────────┬───────────────┘
                                          │ Deploy
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       AZURE COMMERCIAL CLOUD (East US)                              │
│                        Resource Group: KMonteagudo_CSAT_Guardian                    │
│                                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                    VIRTUAL NETWORK (vnet-csatguardian)                      │    │
│  │                           Address Space: 10.100.0.0/16                      │    │
│  │                                                                             │    │
│  │  ┌─────────────────────────────┐   ┌──────────────────────────────────┐   │    │
│  │  │   snet-appservice           │   │   snet-privateendpoints          │   │    │
│  │  │   10.100.1.0/24             │   │   10.100.2.0/24                  │   │    │
│  │  │                             │   │                                  │   │    │
│  │  │  ┌───────────────────────┐  │   │  ┌─────────────────────────┐    │   │    │
│  │  │  │    App Service        │  │   │  │  Private Endpoints      │    │   │    │
│  │  │  │    (FastAPI POC)      │──┼───┼──│  ├─ pep-sql (10.100.2.4) │    │   │    │
│  │  │  │    VNet Integration   │  │   │  │  ├─ pep-kv  (10.100.2.5) │    │   │    │
│  │  │  └───────────────────────┘  │   │  │  └─ pep-oai (10.100.2.6) │    │   │    │
│  │  │                             │   │  └─────────────────────────┘    │   │    │
│  │  └─────────────────────────────┘   └──────────────────────────────────┘   │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                          │
│         ┌────────────────────────────────┼────────────────────────────────────┐    │
│         │                                │                                    │    │
│         ▼                                ▼                                    ▼    │
│  ┌───────────────┐               ┌───────────────┐               ┌───────────────┐ │
│  │   Azure SQL   │               │   Key Vault   │               │  Azure OpenAI │ │
│  │   (Private)   │               │   (Private)   │               │   (Private)   │ │
│  │               │               │               │               │               │ │
│  │ sql-csat...   │               │ kv-csat...    │               │ oai-csat...   │ │
│  │ 10.100.2.4    │               │ 10.100.2.5    │               │ 10.100.2.6    │ │
│  └───────────────┘               └───────────────┘               └───────────────┘ │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                         PRIVATE DNS ZONES                                      │ │
│  │  privatelink.database.windows.net        ← SQL Server                         │ │
│  │  privatelink.vaultcore.azure.net         ← Key Vault                          │ │
│  │  privatelink.openai.azure.com            ← Azure OpenAI                       │ │
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

### Resource Group: `KMonteagudo_CSAT_Guardian`

| Resource | Name | Type | Notes |
|----------|------|------|-------|
| **VNet** | `vnet-csatguardian` | Virtual Network | 10.100.0.0/16 |
| **App Service Plan** | `asp-csatguardian` | Linux B1 | Python 3.12 |
| **App Service** | `app-csatguardian` | Web App | FastAPI POC with VNet integration |
| **Azure OpenAI** | `oai-csatguardian` | Cognitive Services | GPT-4o deployment |
| **SQL Server** | `sql-csatguardian` | Azure SQL | Logical server |
| **SQL Database** | `sqldb-csatguardian` | Azure SQL DB | Basic tier |
| **Key Vault** | `kv-csatguardian` | Key Vault | RBAC-enabled |
| **App Insights** | `appi-csatguardian` | Application Insights | Logging/monitoring |
| **Log Analytics** | `log-csatguardian` | Log Analytics | Central logs |

### Private Endpoints

| Endpoint | Target | Private IP | DNS Zone |
|----------|--------|-----------|----------|
| `pep-csatguardian-sql` | SQL Server | 10.100.2.4 | privatelink.database.windows.net |
| `pep-csatguardian-kv` | Key Vault | 10.100.2.5 | privatelink.vaultcore.azure.net |
| `pep-csatguardian-oai` | Azure OpenAI | 10.100.2.6 | privatelink.openai.azure.com |

### Subnets

| Subnet | Address Range | Purpose |
|--------|--------------|---------|
| `snet-appservice` | 10.100.1.0/24 | App Service VNet integration |
| `snet-privateendpoints` | 10.100.2.0/24 | Private Endpoints |

---

## 4. Component Details

### 4.1 App Service (POC Frontend)

**Purpose**: Hosts the FastAPI backend for POC demonstration

**Why App Service?**
- Simpler deployment for Python apps
- Native VNet integration support
- Easier for single-app scenarios

**Configuration:**
```
Plan: asp-csatguardian (Linux B1)
Runtime: Python 3.12
VNet Integration: snet-appservice
Route All: Enabled (all outbound through VNet)
URL: https://app-csatguardian.azurewebsites.net
```

**Note**: This is a temporary POC frontend. Production will use Teams Bot integration.

### 4.2 Azure Key Vault

**Purpose**: Securely stores all secrets and credentials

**Deployed Instance:** `kv-csatguardian.vault.azure.net`
**Private Endpoint IP:** 10.100.2.5

**Secrets Stored:**
| Secret Name | Description | Status |
|-------------|-------------|--------|
| `AzureOpenAI--Endpoint` | Azure OpenAI endpoint URL | ✅ Stored |
| `AzureOpenAI--ApiKey` | Azure OpenAI API key | ✅ Stored |
| `AzureOpenAI--DeploymentName` | GPT-4o deployment name | ✅ Stored |
| `SqlServer--ConnectionString` | Azure SQL connection string | ✅ Auto-generated |
| `AppInsights--ConnectionString` | App Insights connection | ✅ Auto-generated |
| `Teams--WebhookUrl` | Teams incoming webhook | ⏳ Pending |

**Access Pattern:**
```
App Service (Managed Identity)
    │
    │ VNet Integration → Private Endpoint
    ▼
Key Vault (10.100.2.5)
    │
    │ RBAC: Key Vault Secrets User
    ▼
Application Config
```

### 4.3 Azure SQL Database

**Purpose**: Stores case data, alert history, and analytics

**Deployed Instances:**
- Server: `sql-csatguardian.database.windows.net`
- Database: `sqldb-csatguardian`
- Private Endpoint IP: 10.100.2.4
- Admin: `sqladmin`

**Tables:**
```sql
-- Core data (sample data for POC)
Engineers     -- Support engineer profiles
Customers     -- Customer information
Cases         -- Support cases
TimelineEntries -- Case notes, emails, calls

-- Analytics (persisted)
Alerts        -- Sent alert history (for deduplication)
```

### 4.4 Azure OpenAI

**Purpose**: Provides AI capabilities for sentiment analysis and recommendations

**Deployed Instance:**
- Resource: `oai-csatguardian`
- Endpoint: `https://oai-csatguardian.openai.azure.com/`
- Deployment: `gpt-4o` (version 2024-11-20)
- Private Endpoint IP: 10.100.2.6
- Region: East US

**Use Cases:**
1. **Sentiment Analysis**: Classify customer communications as positive/neutral/negative
2. **Recommendations**: Generate coaching tips for engineers
3. **Conversational AI**: Interactive case Q&A (via Semantic Kernel)

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

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

App Service
    │
    │ System Managed Identity
    ▼
Entra ID
    │
    │ Token
    ▼
Target Service (Key Vault, SQL, OpenAI)
```

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
    -SubscriptionId "a20d761d-cb36-4f83-b827-58ccdb166f39" `
    -ResourceGroup "KMonteagudo_CSAT_Guardian" `
    -Location "eastus"
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
