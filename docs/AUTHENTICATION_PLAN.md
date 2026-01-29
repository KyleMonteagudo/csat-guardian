# CSAT Guardian - Authentication & Authorization Plan

> **Document Purpose:** Explains the planned authentication architecture for production, current POC limitations, and security considerations.
>
> **Status:** PLANNED (Not Yet Implemented)
>
> **Last Updated:** January 29, 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State (POC)](#2-current-state-poc)
3. [Production Architecture](#3-production-architecture)
4. [Security Controls](#4-security-controls)
5. [Role-Based Access](#5-role-based-access)
6. [Open Questions for DfM Team](#6-open-questions-for-dfm-team)
7. [Limitations & Mitigations](#7-limitations--mitigations)

---

## 1. Executive Summary

### The Challenge

CSAT Guardian needs to ensure that:
1. **Engineers can only see their own cases**
2. **Managers can see their team's cases (but not other teams)**
3. **No one can impersonate another user**
4. **All access is auditable**

### Our Approach

We leverage **Microsoft Teams as the identity provider**. When an engineer messages the bot, Teams automatically provides their verified Azure AD identity. This identity cannot be forged or modified by the user.

| Component | Authentication Method |
|-----------|----------------------|
| User Identity | Teams provides AAD Object ID (verified by Microsoft) |
| Bot-to-App Communication | Azure Bot Service with JWT validation |
| App-to-Azure Services | Managed Service Identity (MSI) |
| App-to-DfM | TBD - depends on DfM capabilities |

---

## 2. Current State (POC)

### ⚠️ NOT PRODUCTION READY

The current POC implementation is **intentionally simplified** for demonstration purposes:

| Aspect | Current POC | Production Plan |
|--------|-------------|-----------------|
| User Identity | Passed as parameter (trusted) | Extracted from Teams token (verified) |
| Authentication | None | Azure AD via Teams |
| Authorization | None | Role-based (engineer vs manager) |
| Data Source | Mock data in SQL | Real DfM/Kusto data |
| Teams Bot | Not built | Azure Bot Service + Function gateway |

### Current API Behavior

```http
POST /api/chat
Content-Type: application/json

{
  "message": "How are my cases?",
  "engineer_id": "eng-001"    ← Currently trusted without verification
}
```

**Why this is insecure:** Anyone calling the API can pass any `engineer_id` and see that engineer's cases. This is acceptable for POC with mock data, but must be fixed for production.

---

## 3. Production Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION AUTHENTICATION ARCHITECTURE                            │
│                                                                                      │
│                                                                                      │
│    ┌──────────────┐                                                                 │
│    │   Engineer   │                                                                 │
│    │ (Sarah Chen) │                                                                 │
│    │              │                                                                 │
│    │ Already      │                                                                 │
│    │ signed into  │                                                                 │
│    │ Teams via    │                                                                 │
│    │ Azure AD     │                                                                 │
│    └──────┬───────┘                                                                 │
│           │                                                                          │
│           │ ① "How are my cases doing?"                                             │
│           ▼                                                                          │
│    ┌──────────────┐                                                                 │
│    │              │                                                                 │
│    │   Microsoft  │  Teams automatically attaches verified identity:                │
│    │    Teams     │  • AAD Object ID: 7b0f0d42-0f23-...                            │
│    │              │  • Email: schen@microsoft.com                                   │
│    │              │  • Name: Sarah Chen                                             │
│    │              │  • Tenant: 72f988bf-... (Microsoft)                             │
│    └──────┬───────┘                                                                 │
│           │                                                                          │
│           │ ② Message + User Identity (signed by Microsoft)                         │
│           ▼                                                                          │
│    ┌──────────────┐                                                                 │
│    │              │                                                                 │
│    │  Azure Bot   │  Validates the message is really from Teams                     │
│    │   Service    │  Forwards to our registered endpoint                            │
│    │              │                                                                 │
│    └──────┬───────┘                                                                 │
│           │                                                                          │
│           │ ③ Bot Framework message + JWT token                                     │
│           ▼                                                                          │
│    ┌──────────────┐     ┌─────────────────────────────────────────────────────┐    │
│    │              │     │                                                      │    │
│    │   Azure      │     │  Token Validation:                                   │    │
│    │  Function    │────▶│  • Verify JWT signature (is this really from Bot Svc?)│    │
│    │  (Gateway)   │     │  • Check audience (is this meant for our bot?)       │    │
│    │              │     │  • Validate issuer (is this from Microsoft?)         │    │
│    │  PUBLIC      │     │                                                      │    │
│    │  ENDPOINT    │     └─────────────────────────────────────────────────────┘    │
│    └──────┬───────┘                                                                 │
│           │                                                                          │
│           │ ④ Validated request (via VNet)                                          │
│           ▼                                                                          │
│    ┌──────────────┐                                                                 │
│    │              │                                                                 │
│    │ CSAT Guardian│  Extracts user identity from validated token:                   │
│    │  App Service │  user_aad_id = activity.from.aad_object_id                      │
│    │              │                                                                 │
│    │  PRIVATE     │  User CANNOT modify this - it came from Teams                   │
│    │  (VNet only) │                                                                 │
│    └──────┬───────┘                                                                 │
│           │                                                                          │
│           │ ⑤ Query cases WHERE owner = {verified_user_id}                          │
│           ▼                                                                          │
│    ┌──────────────┐                                                                 │
│    │              │                                                                 │
│    │  DfM/Kusto   │  Returns ONLY cases owned by Sarah Chen                         │
│    │              │                                                                 │
│    └──────────────┘                                                                 │
│                                                                                      │
│                                                                                      │
│    KEY SECURITY POINTS:                                                             │
│    ─────────────────────                                                            │
│    • User identity comes FROM TEAMS, not from user input                            │
│    • User cannot forge or modify their AAD Object ID                                │
│    • Bot Framework validates all messages are really from Teams                     │
│    • Azure Function validates JWT before forwarding                                 │
│    • Main application never exposed to public internet                              │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Decision | Rationale |
|----------|-----------|
| **Teams as identity provider** | Engineers already signed in via Azure AD. No additional login required. |
| **Azure Function gateway** | Teams/Bot Service requires a public callback URL. Function is minimal attack surface. |
| **App Service stays private** | Core application logic and data access never exposed publicly. |
| **MSI for Azure services** | No credentials stored. Tokens are short-lived and auto-rotated. |

---

## 4. Security Controls

### 4.1 Identity Verification

```
┌─────────────────────────────────────────────────────────────────┐
│                  IDENTITY CANNOT BE FORGED                       │
│                                                                  │
│   What user types:     "Show me cases for John Smith"            │
│                                                                  │
│   What we use:         activity.from.aad_object_id               │
│                        (provided by Teams, not by user)          │
│                                                                  │
│   Result:              User sees THEIR cases, not John's         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Tenant Restriction

The bot will **only respond to users in the Microsoft tenant**:

```python
ALLOWED_TENANT = "72f988bf-86f1-41af-91ab-2d7cd011db47"  # Microsoft

async def on_message(activity):
    tenant_id = activity.channel_data.tenant.id
    
    if tenant_id != ALLOWED_TENANT:
        return "This bot is only available to Microsoft employees."
    
    # Continue processing...
```

### 4.3 Bot Framework Token Validation

The Azure Function validates every incoming request:

```python
# Pseudocode for token validation
async def validate_bot_framework_token(request):
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "")
    
    # Validate JWT
    claims = jwt.decode(
        token,
        audience=BOT_APP_ID,          # Is this for our bot?
        issuer="https://api.botframework.com",  # From Microsoft?
        algorithms=["RS256"]
    )
    
    # Verify it's from Teams
    if claims.get("serviceUrl") not in ALLOWED_SERVICE_URLS:
        raise Unauthorized("Invalid service URL")
    
    return claims
```

### 4.4 Network Security

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK ISOLATION                             │
│                                                                  │
│   PUBLIC INTERNET                                                │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Azure Function  │ ◀── Only public endpoint                  │
│   │ (Gateway)       │     Validates tokens before forwarding    │
│   └────────┬────────┘                                           │
│            │ VNet Integration                                    │
│            ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              PRIVATE VNET (10.100.0.0/16)               │   │
│   │                                                          │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │   │
│   │   │ App Service │    │ Azure SQL   │    │ Azure      │  │   │
│   │   │             │───▶│ (Private EP)│    │ OpenAI     │  │   │
│   │   │             │───▶│             │    │(Private EP)│  │   │
│   │   └─────────────┘    └─────────────┘    └────────────┘  │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   NOTHING in the VNet is publicly accessible                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Role-Based Access

### 5.1 User Roles

| Role | Description | What They Can See |
|------|-------------|-------------------|
| **Engineer** | GSX engineer handling cases | Only their own cases |
| **Manager** | GSX manager overseeing team | Their direct reports' cases |

### 5.2 Determining Role and Scope

**Option A: DfM/Kusto Enforces Access**
- We pass the user's identity to DfM
- DfM returns only cases the user is authorized to see
- DfM already knows manager-engineer relationships

**Option B: We Query Microsoft Graph**
- Query Graph API for the user's direct reports
- If they have direct reports → Manager role
- Query cases for user + all direct reports

```
┌─────────────────────────────────────────────────────────────────┐
│                    MANAGER ACCESS FLOW                           │
│                                                                  │
│   Manager: "How is my team doing?"                              │
│                     │                                            │
│                     ▼                                            │
│   ┌─────────────────────────────────────────────────┐           │
│   │ 1. Get manager's AAD ID from Teams              │           │
│   │ 2. Query Graph: GET /users/{id}/directReports   │           │
│   │ 3. Get list of engineer AAD IDs                 │           │
│   │ 4. Query DfM for cases owned by those engineers │           │
│   │ 5. Return aggregated team view                  │           │
│   └─────────────────────────────────────────────────┘           │
│                                                                  │
│   ⚠️ OPEN QUESTION: Does DfM have its own manager mapping?     │
│      If so, we should use that instead of Graph.                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Access Matrix

| User | Requests | Sees |
|------|----------|------|
| Sarah Chen (Engineer) | "How are my cases?" | Only Sarah's cases |
| Sarah Chen (Engineer) | "Show me John's cases" | ❌ Denied - only her cases |
| Mike Johnson (Manager) | "How is my team doing?" | All direct reports' cases |
| Mike Johnson (Manager) | "Show me Sarah's cases" | ✅ If Sarah reports to Mike |
| Mike Johnson (Manager) | "Show me Bob's cases" | ❌ Denied if Bob doesn't report to Mike |

---

## 6. Open Questions for DfM Team

These questions need answers to finalize the authentication design:

### Identity Mapping

| # | Question | Why We Need This |
|---|----------|------------------|
| 1 | Does DfM have a field for engineer AAD Object ID or email? | To query cases by verified identity |
| 2 | Can we query cases by owner AAD ID directly? | Simplest approach if supported |
| 3 | Is there a mapping table from AAD ID → DfM engineer ID? | Fallback if direct query not supported |

### Access Control

| # | Question | Why We Need This |
|---|----------|------------------|
| 4 | Does DfM track manager-engineer relationships? | For manager role access |
| 5 | Can DfM enforce access control (we pass token, it filters)? | Defense in depth |
| 6 | Or do we need to filter results in our app? | Determines our responsibility |

### Authentication Method

| # | Question | Why We Need This |
|---|----------|------------------|
| 7 | Does DfM/Kusto support MSI-based access? | Our app uses MSI for all Azure services |
| 8 | Would DfM require On-Behalf-Of token flow? | If DfM needs to see the actual user's identity |
| 9 | What permissions/roles does our MSI need? | For access provisioning |

---

## 7. Limitations & Mitigations

### 7.1 Current Limitations

| Limitation | Risk | Mitigation Plan |
|------------|------|-----------------|
| **No auth in POC** | Anyone with API access could query any case | POC uses only mock data; production will require Teams identity |
| **Teams bot not built** | Can't demo actual auth flow | API-based demo with explanation of planned flow |
| **DfM access model unknown** | May need different implementation based on DfM capabilities | Multiple approaches ready; will finalize after DfM discussion |
| **Manager role logic TBD** | May need Graph API integration | Depends on DfM capabilities for manager mapping |

### 7.2 What We CAN Guarantee

Even with open questions, these are guaranteed:

| Guarantee | How |
|-----------|-----|
| **User identity is verified** | Teams provides AAD Object ID; cannot be forged |
| **Microsoft tenant only** | We validate tenant ID; reject external users |
| **Audit trail** | All Azure services have diagnostic logging |
| **No public API access** | App Service is VNet-only; only Azure Function is public |
| **No stored credentials** | MSI for all Azure service authentication |
| **PII protection** | Two-layer scrubbing before any AI processing |

### 7.3 Proactive Notifications

For the feature where the bot proactively alerts engineers:

| Aspect | Detail |
|--------|--------|
| **How it works** | When user first messages bot, we store their "conversation reference" |
| **Proactive message** | We use that reference to send alerts without waiting for user to ask |
| **Permission needed** | User must initiate first conversation (install/message the bot) |
| **Opt-out** | Good practice to provide opt-out command (e.g., "stop notifications") |
| **Security** | Proactive messages use same verified identity; we can only message users who've interacted with bot |

---

## Appendix: Implementation Checklist

When we move to production, these must be completed:

### Authentication
- [ ] Register Azure Bot Service
- [ ] Create Azure Function gateway with token validation
- [ ] Implement tenant restriction
- [ ] Extract user identity from Teams activity
- [ ] Remove `engineer_id` parameter from API (use verified identity)

### Authorization
- [ ] Implement engineer → own cases only
- [ ] Implement manager → direct reports' cases
- [ ] Determine manager-engineer mapping source (DfM or Graph)
- [ ] Add authorization checks to all case-related endpoints

### Audit & Monitoring
- [ ] Enable diagnostic logging on Bot Service
- [ ] Log all access requests with user identity
- [ ] Alert on unauthorized access attempts

### Testing
- [ ] Test with real Azure AD users
- [ ] Test tenant restriction (reject non-Microsoft users)
- [ ] Test engineer cannot see other engineers' cases
- [ ] Test manager can only see their reports' cases

---

*Document Version: 1.0*
*Author: Kyle Monteagudo / GitHub Copilot*
