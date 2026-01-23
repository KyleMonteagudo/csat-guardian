# CSAT Guardian - Architecture Overview

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Kyle Monteagudo | Initial architecture document |
| 1.1 | 2026-01-23 | Kyle Monteagudo | Updated for Azure Government |

---

## 1. Executive Summary

CSAT Guardian is a cloud-native, AI-powered support case monitoring system designed to improve customer satisfaction by:
- Detecting negative customer sentiment before it escalates
- Ensuring timely case updates (7-day compliance)
- Providing engineers with actionable coaching recommendations

> **⚠️ IMPORTANT: Azure Government Cloud**
> 
> This application is deployed in **Azure Government** cloud, not Azure Commercial.
> All Azure endpoints use `.us` domains. See [AZURE_GOVERNMENT.md](AZURE_GOVERNMENT.md) for details.

**Key Architectural Principles:**
1. **Cloud-First**: All components run in Azure Government, no local hosting
2. **No Secrets in Code**: All credentials stored in Azure Key Vault
3. **API-Based Access**: Even sample data accessed via API patterns
4. **Mock-Ready**: Interfaces allow swapping between mock and real implementations
5. **FedRAMP Compliant**: Azure Government meets federal compliance requirements

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      CSAT GUARDIAN ARCHITECTURE (AZURE GOVERNMENT)                │
└──────────────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────────────────┐
                            │        GitHub Actions       │
                            │       (CI/CD Pipeline)      │
                            │   environment: AzureGov     │
                            └─────────────┬───────────────┘
                                          │
                                          │ Deploy
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         AZURE GOVERNMENT CLOUD (USGov Virginia)                   │
│                                                                                   │
│   ┌───────────────┐                              ┌───────────────┐               │
│   │   Azure       │                              │   Azure       │               │
│   │   OpenAI      │◀─────────────────────────────│   Key Vault   │               │
│   │   (GPT-4o)    │      Sentiment Analysis      │   (Secrets)   │               │
│   │  .azure.us    │                              │.usgovcloudapi │               │
│   └───────┬───────┘                              └───────┬───────┘               │
│           │                                              │                        │
│           │ Analyze                                      │ Credentials            │
│           ▼                                              ▼                        │
│   ┌─────────────────────────────────────────────────────────────────────┐        │
│   │                      AZURE CONTAINER APPS                            │        │
│   │                                                                      │        │
│   │   ┌────────────────────────────────────────────────────────────┐    │        │
│   │   │                   CSAT GUARDIAN SERVICE                     │    │        │
│   │   │                                                             │    │        │
│   │   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │    │        │
│   │   │   │   Monitor    │  │  Sentiment   │  │    Alert     │    │    │        │
│   │   │   │   Service    │──│   Service    │──│   Service    │    │    │        │
│   │   │   └──────┬───────┘  └──────────────┘  └──────┬───────┘    │    │        │
│   │   │          │                                    │            │    │        │
│   │   │   ┌──────┴───────┐  ┌──────────────┐  ┌──────┴───────┐    │    │        │
│   │   │   │     DfM      │  │  Guardian    │  │    Teams     │    │    │        │
│   │   │   │    Client    │  │    Agent     │  │    Client    │    │    │        │
│   │   │   └──────────────┘  └──────────────┘  └──────────────┘    │    │        │
│   │   │                                                             │    │        │
│   │   └─────────────────────────────────────────────────────────────┘    │        │
│   │                                  │                                   │        │
│   └──────────────────────────────────┼───────────────────────────────────┘        │
│                                      │                                            │
│           ┌──────────────────────────┼──────────────────────────┐                │
│           │                          │                          │                │
│           ▼                          ▼                          ▼                │
│   ┌───────────────┐          ┌───────────────┐          ┌───────────────┐       │
│   │   Azure SQL   │          │   Microsoft   │          │     App       │       │
│   │   Database    │          │    Teams      │          │   Insights    │       │
│   │   (Data)      │          │   (Alerts)    │          │   (Logs)      │       │
│   │.usgovcloudapi │          │  graph.us     │          │               │       │
│   └───────────────┘          └───────────────┘          └───────────────┘       │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘

                                          │
                                          │ API Calls (Future)
                                          ▼
                              ┌───────────────────────┐
                              │         DfM           │
                              │  (Dynamics for MSFT)  │
                              │  [External Service]   │
                              └───────────────────────┘
```

---

## 3. Component Details

### 3.1 Azure Container Apps

**Purpose**: Hosts the main CSAT Guardian application

**Why Container Apps?**
- Serverless pricing (scale to zero when not in use)
- Automatic scaling based on load
- No infrastructure management
- Built-in support for Managed Identity

**Configuration:**
```
SKU: Consumption (0.5 vCPU, 1GB RAM)
Min Replicas: 0 (dev), 1 (prod)
Max Replicas: 3
Ingress: External HTTPS
```

### 3.2 Azure Key Vault

**Purpose**: Securely stores all secrets and credentials

**Secrets Stored:**
| Secret Name | Description |
|-------------|-------------|
| `AzureOpenAI--Endpoint` | Azure OpenAI endpoint URL |
| `AzureOpenAI--ApiKey` | Azure OpenAI API key |
| `SqlServer--ConnectionString` | Azure SQL connection string |
| `Teams--WebhookUrl` | Teams incoming webhook |
| `DfM--ClientSecret` | DfM API client secret (future) |

**Access Pattern:**
```
Container App (Managed Identity)
    │
    │ RBAC: Key Vault Secrets User
    ▼
Key Vault
    │
    │ Get Secret
    ▼
Application Config
```

### 3.3 Azure SQL Database

**Purpose**: Stores case data, alert history, and analytics

**Why Azure SQL?**
- Simulates production DfM data access pattern
- Supports API-based queries (no local file access)
- Managed service with automatic backups
- Easy integration with Managed Identity

**Tables:**
```sql
-- Core data (sample data for POC)
Engineers     -- Support engineer profiles
Customers     -- Customer information
Cases         -- Support cases
TimelineEntries -- Case notes, emails, calls

-- Analytics (persisted)
Alerts        -- Sent alert history (for deduplication)
Metrics       -- Aggregated metrics (no PII)
```

**Tier:**
- Dev: Basic (5 DTU, ~$5/month)
- Prod: Standard S0 (10 DTU)

### 3.4 Azure OpenAI

**Purpose**: Provides AI capabilities for sentiment analysis and recommendations

**Model**: GPT-4o (2024-05-13)

**Use Cases:**
1. **Sentiment Analysis**: Classify customer communications as positive/neutral/negative
2. **Recommendations**: Generate coaching tips for engineers
3. **Summarization**: Create case briefings

**Data Handling:**
- No PII sent to model (content analyzed, not identity)
- Data processed transiently, not stored
- Azure OpenAI (not public OpenAI) - enterprise compliance

### 3.5 Application Insights

**Purpose**: Monitoring, logging, and alerting

**Captures:**
- Application logs (structured JSON)
- Performance metrics
- Exception traces
- Custom events (case analyzed, alert sent)

**Retention**: 30 days (dev), 90 days (prod)

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

Container App
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
            │   │ Container App │   │
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
- Container App has "Key Vault Secrets User" role
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

All Azure resources defined in Bicep:

```
infrastructure/
├── bicep/
│   ├── main.bicep           # Orchestrator
│   ├── modules/
│   │   ├── keyvault.bicep   # Key Vault
│   │   ├── sql.bicep        # Azure SQL
│   │   ├── container.bicep  # Container Apps
│   │   └── monitoring.bicep # App Insights
│   └── parameters/
│       ├── dev.json
│       └── prod.json
└── scripts/
    └── deploy.ps1           # Deployment script
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
│ CD: Deploy  │──▶ Build image, push to ACR, deploy to Dev
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

### 7.1 Container Apps Scaling

```yaml
scale:
  minReplicas: 0  # Scale to zero when idle
  maxReplicas: 10
  rules:
    - name: http-requests
      http:
        metadata:
          concurrentRequests: "100"
```

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
| Container Apps | Consumption | ~$10 |
| Azure SQL | Basic (5 DTU) | ~$5 |
| Key Vault | Standard | ~$1 |
| Container Registry | Basic | ~$5 |
| App Insights | Free tier | $0 |
| Azure OpenAI | Pay-per-use | ~$5-20 |
| **Total** | | **~$25-45/month** |

---

*Document Version: 1.0*  
*Last Updated: January 23, 2026*
