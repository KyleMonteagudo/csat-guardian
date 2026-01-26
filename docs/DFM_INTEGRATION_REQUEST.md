# DfM Integration Request - CSAT Guardian

**From:** Kyle Monteagudo  
**Date:** January 26, 2026  
**Subject:** API Access Request for CSAT Guardian Application

---

## Summary

We're building **CSAT Guardian**, an AI-powered tool to help CSS support engineers proactively manage customer satisfaction by:
- Monitoring case sentiment via AI analysis
- Alerting engineers to communication gaps (7-day rule compliance)
- Providing coaching recommendations to improve CSAT outcomes

We need **read-only API access** to DfM case data.

---

## Data Requirements

### 1. Cases (Incidents)

We need the following fields from the **Incident** entity:

| Field | Dynamics Field (expected) | Description |
|-------|---------------------------|-------------|
| Case ID | `incidentid` | Unique identifier |
| Title | `title` | Case subject |
| Description | `description` | Initial case description |
| Status | `statecode` / `statuscode` | Active, Resolved, etc. |
| Severity | `severitycode` | Sev A, B, C, D |
| Created Date | `createdon` | Case creation timestamp |
| Modified Date | `modifiedon` | Last update timestamp |
| Owner | `ownerid` | Assigned engineer (link to systemuser) |
| Customer | `customerid` | Customer reference |

### 2. Timeline Activities

We need activities associated with each case to analyze communication patterns:

| Activity Type | Dynamics Entity | Fields Needed |
|---------------|-----------------|---------------|
| Notes | `annotation` | `subject`, `notetext`, `createdon`, `createdby` |
| Emails | `email` | `subject`, `description`, `directioncode`, `createdon`, `from`, `to` |
| Phone Calls | `phonecall` | `subject`, `description`, `directioncode`, `createdon` |

**Key question:** How do we query activities by case? (via `regardingobjectid`?)

### 3. Engineers (System Users)

| Field | Dynamics Field | Description |
|-------|----------------|-------------|
| User ID | `systemuserid` | Unique identifier |
| Name | `fullname` | Display name |
| Email | `internalemailaddress` | Email address |

---

## Access Pattern

| Requirement | Details |
|-------------|---------|
| **Read/Write** | Read-only |
| **Frequency** | Polling every 5-15 minutes (configurable) |
| **Scope** | Cases for specific engineers or teams (filterable) |
| **Volume** | ~50-100 active cases per poll (estimated) |

---

## Technical Questions

1. **API Endpoint**: What's the base URL and API version?
   - Is it standard Dynamics Web API (OData)?
   - Or a custom CSS-specific API?

2. **Authentication**: What method should we use?
   - OAuth2 with App Registration?
   - Managed Identity?
   - Certificate-based?

3. **Filtering**: Can we filter queries by:
   - Engineer/owner?
   - Date range (modified in last X hours)?
   - Status (active only)?

4. **Related Data**: Can we use `$expand` to get timeline activities in a single call?
   - Or do we need separate queries per case?

5. **Rate Limits**: Are there throttling limits we should be aware of?

6. **Existing Patterns**: Is there an existing integration pattern or SDK we should follow?

---

## Our Environment

| Item | Details |
|------|---------|
| **Hosting** | Azure App Service (Commercial, Central US) |
| **Auth** | Managed Identity (MSI) |
| **Network** | Can use Private Endpoints if required |
| **Security** | No data stored locally - all queries on-demand |

---

## Contact

**Kyle Monteagudo**  
CSS Support Engineering  
kmonteagudo@microsoft.com

---

## Appendix: Sample Query (Expected)

If using standard Dynamics Web API:

```http
GET /api/data/v9.2/incidents?$filter=statecode eq 0 and _ownerid_value eq '{engineer-guid}'
&$select=incidentid,title,description,statecode,severitycode,createdon,modifiedon
&$expand=incident_activity_parties($select=subject,createdon,activitytypecode)
&$top=100
```

We're flexible on the implementation - just need guidance on the correct approach for your environment.
