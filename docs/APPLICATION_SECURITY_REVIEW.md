# CSAT Guardian - Application Security Review Documentation

## Executive Summary

**Application Name:** CSAT Guardian  
**Purpose:** Proactive customer support experience optimization through AI-powered sentiment analysis and engineer coaching  
**Requestor:** Kyle Monteagudo  
**Date:** January 22, 2026  
**Last Updated:** February 4, 2026  
**Classification:** Internal Enterprise Tool  

### Security Highlights (Updated Feb 2026)

| Security Control | Status |
|-----------------|--------|
| Local Auth (API Keys) | ❌ **DISABLED** on all Azure services |
| Authentication | ✅ Managed Identity only |
| Network Access | ✅ Private Endpoints (no public access) |
| PII Protection | ✅ Two-layer scrubbing (regex + Azure AI Content Safety) |

---

## 1. Application Overview

### 1.1 Business Justification

Customer Satisfaction (CSAT) scores directly impact customer retention, team performance metrics, and overall service quality. Currently, negative CSAT feedback is **reactive** - we learn about poor experiences only after the customer completes a post-closure survey.

CSAT Guardian shifts this paradigm to **proactive intervention** by:
- Detecting negative customer sentiment in real-time during case handling
- Providing engineers with actionable guidance before situations escalate
- Ensuring timely and substantive communications
- Identifying at-risk cases for early intervention

**Expected Outcomes:**
- Improved CSAT scores across support organization
- Reduced escalations and customer churn
- Enhanced engineer effectiveness through AI-assisted coaching
- Data-driven insights into support experience patterns

### 1.2 Application Description

CSAT Guardian is an AI-powered monitoring and coaching service that:

1. **Monitors** incoming support cases for initial customer sentiment
2. **Analyzes** case timelines (notes, emails, calls) for sentiment shifts
3. **Alerts** engineers when negative signals are detected
4. **Recommends** troubleshooting steps and communication improvements
5. **Tracks** communication timeliness and quality metrics
6. **Enforces** 7-day case note update compliance with proactive warnings
7. **Converses** with engineers in Teams for interactive guidance and follow-up questions

The application does NOT:
- Modify case data in any way
- Respond to customers directly
- Make automated decisions about case handling
- Store customer PII beyond transient processing

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CSAT GUARDIAN ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Azure OpenAI  │
                              │  (Sentiment &   │
                              │   Analysis)     │
                              └────────┬────────┘
                                       │
┌──────────────┐              ┌────────▼────────┐              ┌──────────────┐
│              │   Webhook/   │                 │   Alerts     │              │
│     DfM      │───Polling───▶│  CSAT Guardian  │─────────────▶│  Microsoft   │
│  (Dynamics)  │              │     Service     │              │    Teams     │
│              │◀─────────────│                 │              │              │
└──────────────┘  Read-Only   └────────┬────────┘              └──────────────┘
                   Queries             │
                              ┌────────▼────────┐
                              │  Azure SQL /    │
                              │  Cosmos DB      │
                              │  (Analytics &   │
                              │   Config Only)  │
                              └─────────────────┘
```

### 2.2 Component Description

| Component | Purpose | Technology |
|-----------|---------|------------|
| **CSAT Guardian Service** | Core orchestration, sentiment analysis coordination | Azure Functions / Azure Container Apps |
| **Azure OpenAI** | Sentiment analysis, recommendation generation | GPT-4o (Azure Gov/Commercial as applicable) |
| **DfM Integration** | Read case data via API | Dynamics 365 Web API |
| **Notification Service** | Alert engineers via Teams | Microsoft Graph API / Teams Webhooks |
| **Analytics Store** | Store aggregated metrics (no PII) | Azure SQL / Cosmos DB |
| **Configuration Store** | Manage thresholds, rules, preferences | Azure App Configuration |

### 2.3 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

CASE CREATION FLOW:
───────────────────
DfM Event (Case Created)
    │
    ▼
Webhook triggers CSAT Guardian
    │
    ▼
Service queries case details (READ-ONLY)
    │
    ├──▶ Case Description
    ├──▶ Customer Context
    └──▶ Initial Metadata
    │
    ▼
Azure OpenAI analyzes sentiment
    │
    ▼
Results cached transiently (no PII stored)
    │
    ▼
If negative sentiment OR case assigned:
    │
    ▼
Teams notification sent to engineer
    │
    ▼
Aggregate metrics logged (anonymized)


TIMELINE MONITORING FLOW:
─────────────────────────
Scheduled scan (every N minutes)
    │
    ▼
Query active cases with recent updates
    │
    ▼
For each case:
    ├──▶ Fetch timeline entries (notes, emails)
    ├──▶ Analyze sentiment delta
    └──▶ Check communication timing
    │
    ▼
If alert threshold met:
    │
    ▼
Generate coaching recommendation
    │
    ▼
Send Teams alert to assigned engineer
```

---

## 3. Data Access Requirements

### 3.1 DfM (Dynamics for Microsoft) Access

| Data Entity | Fields Required | Access Level | Justification |
|-------------|-----------------|--------------|---------------|
| **Incident (Case)** | incidentid, title, description, createdon, statecode, prioritycode | Read | Core case identification and initial analysis |
| **Incident Owner** | ownerid, fullname, internalemailaddress | Read | Route notifications to assigned engineer |
| **Case Notes** | annotationid, subject, notetext, createdon, createdby | Read | Timeline sentiment analysis |
| **Emails** | activityid, subject, description, createdon, directioncode | Read | Communication quality analysis |
| **Phone Call Notes** | activityid, subject, description, createdon | Read | Capture engineer notes about customer calls (note: no voice/audio data - just written notes about the call) |
| **Activities** | activityid, activitytypecode, createdon, statecode | Read | Track response timing and frequency |

**Access Pattern:** READ-ONLY via Dynamics 365 Web API  
**No Write/Update/Delete operations required**

### 3.2 Azure OpenAI Access

| Capability | Model | Purpose |
|------------|-------|---------|
| Sentiment Analysis | GPT-4o | Analyze text for customer sentiment indicators |
| Recommendation Generation | GPT-4o | Generate troubleshooting suggestions and coaching tips |
| Text Summarization | GPT-4o | Summarize case context for engineer briefings |

**Data Sent to Azure OpenAI:**
- Case descriptions (text only)
- Communication excerpts (text only)
- No customer PII is sent - content is processed for sentiment, not identity

**Azure OpenAI Data Handling:**
- Using Azure OpenAI (not public OpenAI)
- Data is NOT used to train models
- Data is processed transiently and not retained by the service
- Compliant with Microsoft enterprise data handling policies

### 3.3 Microsoft Graph / Teams Access

| Permission | Scope | Purpose |
|------------|-------|---------|
| Chat.Create | Application | Send proactive alerts to engineers |
| Chat.ReadWrite | Application | Read engineer replies for conversational interaction |
| User.Read.All | Application | Resolve engineer IDs for notification routing |
| ChannelMessage.Send | Application | Post to support team channels (optional) |

### 3.4 Teams Bot Framework Access

| Component | Purpose |
|-----------|----------|
| **Azure Bot Service** | Host conversational bot for Teams integration |
| **Bot Framework SDK** | Handle message routing and conversation state |
| **Teams App Manifest** | Register bot as Teams app for engineer interaction |

**Conversational Capabilities:**
- Engineers can reply to alerts to ask follow-up questions
- Engineers can ask for more details on troubleshooting suggestions
- Engineers can request case summaries or sentiment analysis on demand
- Conversation context is maintained within session (not persisted long-term)

**Alternative for Notifications Only:** Teams Incoming Webhooks (no Graph permissions required, but no conversation)

---

## 4. Identity & Authentication

### 4.1 Managed Identity

| Identity Type | Purpose | Scope |
|---------------|---------|-------|
| **System-Assigned Managed Identity** | Authenticate to Azure services (Key Vault, SQL, OpenAI) | Service principal with least-privilege |
| **Application Registration** | Authenticate to DfM and Microsoft Graph | Service-to-service OAuth 2.0 |

### 4.2 Service Principal Permissions

```
DfM Application Registration:
├── Dynamics CRM
│   └── user_impersonation (Delegated) OR
│   └── Application permission with S2S authentication
│
Microsoft Graph Application Registration:
├── Chat.Create (Application)
├── User.Read.All (Application)
└── ChannelMessage.Send (Application) [if using channels]
```

### 4.3 User Access

| Role | Access Level | Capabilities |
|------|--------------|--------------|
| **Support Engineers** | Conversational | Receive alerts via Teams; can converse with agent for guidance |
| **Team Leads** | Dashboard Viewer | View aggregated team metrics (no individual case data) |
| **Administrators** | Configuration | Manage alert thresholds, enable/disable monitoring |

**Note:** Support engineers interact with the agent conversationally through Teams. They can ask follow-up questions, request clarification on recommendations, and get on-demand case analysis.

---

## 5. Data Storage & Retention

### 5.1 What IS Stored

| Data | Storage Location | Retention | Purpose |
|------|------------------|-----------|---------|
| Aggregate Metrics | Azure SQL / Cosmos DB | 90 days | Dashboard analytics (e.g., "Cases with negative sentiment this week: 15") |
| Alert History | Azure SQL | 30 days | Track which alerts were sent (case ID + timestamp only) |
| Configuration | Azure App Configuration | Indefinite | Alert thresholds, enabled features |
| Application Logs | Azure Monitor / App Insights | 30 days | Debugging, performance monitoring |

### 5.2 What IS NOT Stored

| Data | Reason |
|------|--------|
| Customer Names | Not required for sentiment analysis |
| Customer Email Addresses | Not required - we analyze content, not identity |
| Full Case Descriptions | Processed transiently, not persisted |
| Email/Note Content | Processed transiently, not persisted |
| Phone Numbers | Not accessed |
| Any Customer PII | By design - sentiment analysis doesn't require identity |

### 5.3 Data Minimization Approach

```
RAW DATA (from DfM)          PROCESSED DATA              STORED DATA
─────────────────────        ──────────────────          ────────────────
Case Description      ──▶    Sentiment Score      ──▶   Metric: +1 negative case
Customer Email        ──▶    Communication Gap    ──▶   Metric: avg response time
Engineer Notes        ──▶    Quality Assessment   ──▶   Alert: case ID + timestamp
                             │
                             ▼
                      [DISCARDED - NOT STORED]
```

---

## 6. Security Controls

### 6.1 Network Security

| Control | Implementation |
|---------|----------------|
| **Private Endpoints** | DfM, Azure OpenAI, and Storage accessed via private endpoints (no public internet) |
| **VNet Integration** | Service runs in isolated VNet with NSG rules |
| **TLS 1.2+** | All data in transit encrypted |
| **No Inbound Internet** | Service only makes outbound calls to authorized endpoints |

### 6.2 Data Security

| Control | Implementation |
|---------|----------------|
| **Encryption at Rest** | Azure SQL TDE, Storage Service Encryption |
| **Encryption in Transit** | TLS 1.2+ for all API calls |
| **No PII Storage** | By design - sentiment analysis is content-based, not identity-based |
| **Key Vault** | All secrets (API keys, connection strings) stored in Azure Key Vault |
| **Managed Identity** | No credentials in code or configuration |

### 6.3 Access Controls

| Control | Implementation |
|---------|----------------|
| **RBAC** | Azure RBAC for all Azure resources |
| **Least Privilege** | Service principal has minimum required permissions |
| **No Interactive Login** | Service uses managed identity, no user credentials |
| **Audit Logging** | All API calls logged to Azure Monitor |

### 6.4 Compliance Considerations

| Requirement | How Addressed |
|-------------|---------------|
| **Data Residency** | All processing and storage in approved Azure region |
| **GDPR/Privacy** | No PII stored; transient processing only |
| **SOC 2** | Azure services are SOC 2 compliant |
| **Audit Trail** | All actions logged with timestamps |

---

## 7. Notification System Requirements

### 7.1 Communication Channels

| Channel | Use Case | Technology |
|---------|----------|------------|
| **Teams Bot (1:1 Chat)** | Interactive alerts and conversation with engineers | Azure Bot Service + Teams |
| **Teams Channel Post** | Team-wide awareness (optional) | Teams Incoming Webhook |
| **Email (Backup)** | If Teams unavailable | Microsoft Graph Mail API |

### 7.2 Conversational Interaction

Engineers can interact with CSAT Guardian through natural conversation in Teams:

**Example Interactions:**
```
👤 Engineer: "Tell me more about why this customer seems frustrated"
🤖 Guardian: "Based on the case timeline, the customer has expressed frustration
             in 3 messages over the past 48 hours. Key concerns:
             1. Waiting 2 days for initial response
             2. Solution provided didn't resolve the issue
             3. Had to repeat information multiple times
             
             Would you like suggestions for how to address these concerns?"

👤 Engineer: "Yes, what should I say?"
🤖 Guardian: "Here's a suggested response approach:
             1. Start with empathy: Acknowledge the delays and frustration
             2. Show progress: Summarize what's been tried and why
             3. Clear next step: 'I'm escalating to [team] and will update you by EOD'
             
             Would you like me to draft a sample response?"

👤 Engineer: "Can you summarize case 12345678?"
🤖 Guardian: "📋 Case #12345678 Summary:
             • Created: Jan 15, 2026 (7 days ago)
             • Issue: Unable to access shared mailbox after migration
             • Sentiment: Negative (customer frustrated with timeline)
             • Last update: Jan 20 (2 days ago)
             • ⚠️ Approaching 7-day update requirement
             
             Shall I suggest next steps?"
```

**Conversation Boundaries:**
- Agent only discusses cases assigned to the engineer
- Agent cannot modify case data or send messages to customers
- Agent provides suggestions - engineer makes all decisions
- Conversation history is session-based, not permanently stored

### 7.3 Notification Types

| Alert Type | Trigger | Urgency | Content |
|------------|---------|---------|---------|
| **Case Briefing** | Case assigned to engineer | Normal | Summary, sentiment flag, suggested actions |
| **Sentiment Alert** | Negative sentiment detected | High | Specific concern, recommended response |
| **Communication Gap** | No response in X hours | Medium | Reminder with suggested follow-up |
| **7-Day Warning** | Case notes not updated in 5-6 days | Medium | Warning: approaching 7-day update requirement |
| **7-Day Breach** | Case notes not updated in 7+ days | High | Alert: 7-day update requirement breached |
| **Recovery Suggestion** | After negative interaction | High | Specific recovery actions to take |

### 7.4 Notification Content (Example)

```
┌─────────────────────────────────────────────────────────────────┐
│ 🚨 CSAT Guardian Alert - Case #12345678                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ⚠️ Negative Sentiment Detected                                  │
│                                                                 │
│ Customer appears frustrated. Key signals:                       │
│ • "I've been waiting for 3 days with no update"                │
│ • "This is unacceptable"                                       │
│                                                                 │
│ 💡 Suggested Actions:                                           │
│ 1. Acknowledge the delay and apologize                         │
│ 2. Provide a concrete update on progress                       │
│ 3. Set clear expectations for next steps                       │
│                                                                 │
│ [View Case in DfM]                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Operational Requirements

### 8.1 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.5% (non-critical advisory service) |
| RTO | 4 hours |
| RPO | N/A (no critical data stored) |

### 8.2 Scalability

| Scenario | Approach |
|----------|----------|
| Increased case volume | Azure Functions consumption plan auto-scales |
| Multiple teams | Configuration-driven team isolation |
| Global deployment | Multi-region deployment if needed |

### 8.3 Monitoring

| Metric | Tool |
|--------|------|
| Application health | Azure Monitor / App Insights |
| API latency | App Insights distributed tracing |
| Alert delivery success | Custom metrics in App Insights |
| Error rates | App Insights exceptions |

---

## 9. Risk Assessment

### 9.1 Identified Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| False positive sentiment detection | Medium | Low | Tunable thresholds; human review of recommendations |
| DfM API rate limiting | Low | Medium | Implement exponential backoff; cache where appropriate |
| Azure OpenAI unavailability | Low | Medium | Graceful degradation; queue and retry |
| Over-notification fatigue | Medium | Medium | Configurable quiet hours; severity-based throttling |
| Data breach | Low | High | No PII stored; encryption everywhere; private endpoints |

### 9.2 Abuse Prevention

| Concern | Control |
|---------|---------|
| Mass data extraction | Read-only access; API calls logged and monitored |
| Unauthorized access | Managed identity; no user credentials; RBAC |
| Data exfiltration | No bulk export capability; private endpoints |

---

## 10. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Security review approval
- [ ] Azure resource provisioning
- [ ] DfM API access granted
- [ ] Managed identity configuration

### Phase 2: Core Development (Weeks 3-6)
- [ ] DfM integration (read case data)
- [ ] Sentiment analysis pipeline
- [ ] Teams Bot registration and setup
- [ ] Basic alerting logic
- [ ] Conversational interaction framework

### Phase 3: Intelligence (Weeks 7-8)
- [ ] Troubleshooting recommendation engine
- [ ] Communication timing analysis
- [ ] Engineer coaching suggestions

### Phase 4: Pilot (Weeks 9-10)
- [ ] Deploy to pilot team
- [ ] Gather feedback
- [ ] Tune thresholds and prompts

### Phase 5: Rollout (Weeks 11-12)
- [ ] Broader deployment
- [ ] Dashboard for team leads
- [ ] Documentation and training

---

## 11. Appendices

### Appendix A: API Endpoints Required

**DfM (Dynamics 365):**
```
GET /api/data/v9.2/incidents                    # List/query cases
GET /api/data/v9.2/incidents({id})              # Get case details
GET /api/data/v9.2/annotations                  # Get case notes
GET /api/data/v9.2/emails                       # Get email activities
GET /api/data/v9.2/phonecalls                   # Get phone call notes (engineer notes about calls)
GET /api/data/v9.2/activitypointers             # Get all activities
```

**Microsoft Graph:**
```
POST /v1.0/chats                                # Create chat with user
POST /v1.0/chats/{id}/messages                  # Send message
GET  /v1.0/chats/{id}/messages                  # Read engineer replies (for conversation)
GET  /v1.0/users/{id}                           # Resolve user details
```

**Azure Bot Service:**
```
POST /api/messages                              # Receive messages from Teams
     (Bot Framework webhook endpoint)
```

**Azure OpenAI:**
```
POST /openai/deployments/{deployment}/chat/completions
```

### Appendix B: Sample Configuration

```json
{
  "monitoring": {
    "enabled": true,
    "scanIntervalMinutes": 15,
    "activeStatusCodes": ["Active", "In Progress"]
  },
  "sentimentThresholds": {
    "alertOnNegative": true,
    "negativeScoreThreshold": 0.3,
    "escalationKeywords": ["manager", "escalate", "supervisor"]
  },
  "communicationAlerts": {
    "noResponseAlertHours": 24,
    "reminderIntervalHours": 8
  },
  "complianceAlerts": {
    "caseUpdateRequiredDays": 7,
    "warningThresholdDays": 5,
    "breachAlertEnabled": true,
    "warningAlertEnabled": true
  },
  "notifications": {
    "teamsEnabled": true,
    "emailFallbackEnabled": false,
    "quietHoursStart": "22:00",
    "quietHoursEnd": "07:00"
  }
}
```

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| **CSAT** | Customer Satisfaction - a score from 1-5 provided by customers post-case closure |
| **DfM** | Dynamics for Microsoft - the case management system |
| **Sentiment** | The emotional tone detected in customer communications |
| **Timeline** | The chronological record of all case activities (notes, emails, calls) |
| **Transient Processing** | Data is processed in memory and immediately discarded, not persisted |

---

## 12. Approval Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Application Owner | | | |
| Security Reviewer | | | |
| Data Privacy Officer | | | |
| Infrastructure Lead | | | |

---

*Document Version: 1.0*  
*Last Updated: January 22, 2026*
