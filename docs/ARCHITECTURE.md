# CSAT Guardian - Architecture Overview

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Kyle Monteagudo | Initial architecture document |
| 1.1 | 2026-01-23 | Kyle Monteagudo | Updated for Azure Government |
| 1.2 | 2026-01-23 | Kyle Monteagudo | Added actual deployed resource names and endpoints |
| 2.0 | 2026-01-23 | Kyle Monteagudo | **Major update**: Private networking architecture with VNet, Private Endpoints, App Service |

---

## 1. Executive Summary

CSAT Guardian is a cloud-native, AI-powered support case monitoring system designed to improve customer satisfaction by:
- Detecting negative customer sentiment before it escalates
- Ensuring timely case updates (7-day compliance)
- Providing engineers with actionable coaching recommendations

> **⚠️ IMPORTANT: Azure Government Cloud with Private Networking**
> 
> This application is deployed in **Azure Government** cloud with **private endpoints**.
> All Azure-to-Azure communication is private (no public internet).
> See [AZURE_GOVERNMENT.md](AZURE_GOVERNMENT.md) for details.

**Key Architectural Principles:**
1. **Cloud-First**: All components run in Azure Government, no local hosting
2. **Private by Default**: All backend services use Private Endpoints
3. **No Secrets in Code**: All credentials stored in Azure Key Vault
4. **API-Based Access**: Even sample data accessed via API patterns
5. **VNet Integration**: App Service routes all traffic through VNet
6. **FedRAMP Compliant**: Azure Government meets federal compliance requirements

---

## 2. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│             CSAT GUARDIAN ARCHITECTURE (AZURE GOVERNMENT - PRIVATE NETWORKING)      │
└────────────────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────────────────┐
                            │        GitHub Actions       │
                            │       (CI/CD Pipeline)      │
                            └─────────────┬───────────────┘
                                          │ Deploy
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       AZURE GOVERNMENT CLOUD (USGov Virginia)                       │
│                           Resource Group: rg-csatguardian-dev                       │
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
│  │  │  │    (Streamlit POC)    │──┼───┼──│  ├─ pep-sql (10.100.2.4) │    │   │    │
│  │  │  │    VNet Integration   │  │   │  │  ├─ pep-kv  (10.100.2.5) │    │   │    │
│  │  │  └───────────────────────┘  │   │  │  └─ pep-oai (10.100.2.6) │    │   │    │
│  │  │                             │   │  └─────────────────────────┘    │   │    │
│  │  └─────────────────────────────┘   └──────────────────────────────────┘   │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                          │
│         ┌────────────────────────────────┼────────────────────────────────┐        │
│         │                                │                                │        │
│         ▼                                ▼                                ▼        │
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
│  │  privatelink.database.usgovcloudapi.net  ← SQL Server                         │ │
│  │  privatelink.vaultcore.usgovcloudapi.net ← Key Vault                          │ │
│  │  privatelink.openai.azure.us             ← Azure OpenAI                       │ │
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

### Resource Group: `rg-csatguardian-dev`

| Resource | Name | Type | Notes |
|----------|------|------|-------|
| **VNet** | `vnet-csatguardian-dev` | Virtual Network | 10.100.0.0/16 |
| **App Service Plan** | `asp-csatguardian-dev` | Linux B1 | Python 3.12 |
| **App Service** | `app-csatguardian-dev` | Web App | Streamlit POC with VNet integration |
| **Azure OpenAI** | `oai-csatguardian-dev` | Cognitive Services | GPT-4o deployment |
| **SQL Server** | `sql-csatguardian-dev` | Azure SQL | Logical server |
| **SQL Database** | `sqldb-csatguardian-dev` | Azure SQL DB | Basic tier |
| **Key Vault** | `kv-csatguardian-dev` | Key Vault | RBAC-enabled |
| **App Insights** | `appi-csatguardian-dev` | Application Insights | Logging/monitoring |
| **Log Analytics** | `log-csatguardian-dev` | Log Analytics | Central logs |
| **Container Registry** | `acrcsatguardiandev` | ACR | For future containers |

### Private Endpoints

| Endpoint | Target | Private IP | DNS Zone |
|----------|--------|-----------|----------|
| `pep-csatguardian-dev-sql` | SQL Server | 10.100.2.4 | privatelink.database.usgovcloudapi.net |
| `pep-csatguardian-dev-kv` | Key Vault | 10.100.2.5 | privatelink.vaultcore.usgovcloudapi.net |
| `pep-csatguardian-dev-oai` | Azure OpenAI | 10.100.2.6 | privatelink.openai.azure.us |

### Subnets

| Subnet | Address Range | Purpose |
|--------|--------------|---------|
| `snet-appservice` | 10.100.1.0/24 | App Service VNet integration |
| `snet-privateendpoints` | 10.100.2.0/24 | Private Endpoints |

---

## 4. Component Details

### 4.1 App Service (POC Frontend)

**Purpose**: Hosts the Streamlit web UI for POC demonstration

**Why App Service (not Container Apps)?**
- Simpler deployment for Python apps
- Native VNet integration support
- Easier for single-app scenarios
- Well-supported in Azure Government

**Configuration:**
```
Plan: asp-csatguardian-dev (Linux B1)
Runtime: Python 3.12
VNet Integration: snet-appservice
Route All: Enabled (all outbound through VNet)
URL: https://app-csatguardian-dev.azurewebsites.us
```

**Note**: This is a temporary POC frontend. Production will use Teams Bot integration.

### 4.2 Azure Key Vault

**Purpose**: Securely stores all secrets and credentials

**Deployed Instance:** `kv-csatguardian-dev.vault.usgovcloudapi.net`
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
- Server: `sql-csatguardian-dev.database.usgovcloudapi.net`
- Database: `sqldb-csatguardian-dev`
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
- Resource: `oai-csatguardian-dev`
- Endpoint: `https://oai-csatguardian-dev.openai.azure.us/`
- Deployment: `gpt-4o` (version 2024-11-20)
- Private Endpoint IP: 10.100.2.6
- Region: USGov Virginia

**Use Cases:**
1. **Sentiment Analysis**: Classify customer communications as positive/neutral/negative
2. **Recommendations**: Generate coaching tips for engineers
3. **Conversational AI**: Interactive case Q&A (via Semantic Kernel)

---

## 4. Data Flow

### 4.1 Case Monitoring Flow

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

### 4.2 Conversational Flow

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

## 5. Security Architecture

### 5.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

App Service
    │
    │ System Managed Identity
    ▼
Azure AD
    │
    │ Token
    ▼
Target Service (Key Vault, SQL, OpenAI)
```

**No credentials in code or config** - all authentication via Managed Identity

### 5.2 Network Security (Production)

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

### 5.3 Secrets Management

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

## 6. Deployment Architecture

### 6.1 Environment Strategy

| Environment | Purpose | Data | API |
|-------------|---------|------|-----|
| **Dev** | Development & testing | Sample data | Mock |
| **Test** | Integration testing | Sample data | Mock |
| **Prod** | Production | Real DfM | Real |

### 6.2 Infrastructure as Code

All Azure resources defined in Bicep (private networking):

```
infrastructure/
├── bicep/
│   ├── main-private.bicep       # Main orchestrator
│   ├── main-private.bicepparam  # Parameters
│   ├── modules/
│   │   ├── networking.bicep     # VNet and subnets
│   │   ├── private-dns.bicep    # Private DNS zones
│   │   ├── keyvault.bicep       # Key Vault
│   │   ├── sql.bicep            # Azure SQL
│   │   ├── openai.bicep         # Azure OpenAI
│   │   ├── appservice.bicep     # App Service + Plan
│   │   ├── private-endpoints.bicep # SQL, KV, OpenAI endpoints
│   │   └── monitoring.bicep     # App Insights
│   └── parameters/
│       └── dev.json
└── scripts/
    └── deploy-private-infra.ps1  # Deployment script
```

### 6.3 CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         CI/CD PIPELINE                          │
└─────────────────────────────────────────────────────────────────┘

Push to Feature Branch
    │
    ▼
┌─────────────┐
│ CI: Build   │──▶ Run tests, linting, security scan
│    & Test   │
└──────┬──────┘
       │ PR to develop
       ▼
┌─────────────┐
│ Review &    │──▶ Code review, approval
│   Merge     │
└──────┬──────┘
       │ Merge
       ▼
┌─────────────┐
│ CD: Deploy  │──▶ Run Bicep, deploy to App Service
│   to Dev    │
└──────┬──────┘
       │ PR to main
       ▼
┌─────────────┐
│ CD: Deploy  │──▶ Deploy to Production (with approval)
│   to Prod   │
└─────────────┘
```

---

## 7. Scalability

### 7.1 App Service Scaling

```
Plan: asp-csatguardian-dev
Tier: B1 (Basic)
Scale: Manual (1 instance for POC)
Future: Can scale to P1v3 or Premium for auto-scale
```

**Production Scale Options:**
- Scale Up: P1v3, P2v3 (more CPU/RAM)
- Scale Out: Multiple instances with load balancing
- Auto-scale: Based on CPU, memory, or HTTP requests

### 7.2 Database Scaling

| Load | Tier | DTUs | Est. Cost |
|------|------|------|-----------|
| POC | Basic | 5 | $5/month |
| Low | Standard S0 | 10 | $15/month |
| Medium | Standard S2 | 50 | $75/month |
| High | Premium P1 | 125 | $465/month |

### 7.3 OpenAI Rate Limits

Managed via Azure OpenAI deployment capacity:
- POC: 10K tokens/min
- Production: Based on usage patterns

---

## 8. Monitoring & Observability

### 8.1 Logging Strategy

| Log Level | Usage |
|-----------|-------|
| DEBUG | Detailed troubleshooting (dev only) |
| INFO | Normal operations, case analysis |
| WARNING | Degraded service, approaching limits |
| ERROR | Failed operations, exceptions |
| CRITICAL | System failures |

### 8.2 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `scan_duration_ms` | Time to scan all cases | > 60,000 ms |
| `sentiment_api_latency_ms` | OpenAI API response time | > 5,000 ms |
| `alerts_sent_count` | Alerts sent per scan | N/A (informational) |
| `error_count` | Errors per hour | > 10/hour |

### 8.3 Dashboards

Azure Monitor workbook displaying:
- Scan execution history
- Sentiment distribution
- Alert volume trends
- Error rates

---

## 9. Disaster Recovery

| Aspect | Strategy |
|--------|----------|
| **RTO** | 4 hours (non-critical advisory service) |
| **RPO** | N/A (no critical data; can regenerate from DfM) |
| **Backup** | Azure SQL automatic backups |
| **Failover** | Redeploy from GitHub + Bicep |

---

## 10. Cost Estimate (POC)

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

*Document Version: 1.0*  
*Last Updated: January 23, 2026*
