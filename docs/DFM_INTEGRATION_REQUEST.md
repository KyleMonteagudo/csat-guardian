# DfM Integration Request - CSAT Guardian

**From:** Kyle Monteagudo  
**Date:** January 27, 2026 (Updated)  
**Subject:** Azure Data Explorer (Kusto) Access Request for CSAT Guardian Application

---

## Summary

We're building **CSAT Guardian**, an AI-powered tool to help **GSX (Government Support Engineers)** proactively manage customer satisfaction by:
- Monitoring case sentiment via AI analysis
- Alerting engineers to communication gaps (7-day rule compliance)
- Providing coaching recommendations to improve CSAT outcomes

We need **read-only access** to DfM case data via **Azure Data Explorer (Kusto)**.

---

## Update: Kusto Integration

We've confirmed that DfM case data for Azure Gov is stored in Azure Data Explorer (ADX), not via D365 OData APIs. We will query Kusto directly using the `azure-kusto-data` Python SDK with Managed Identity authentication.

---

## Data Requirements

### 1. Cases (Incidents)

| Field | Expected Column | Description |
|-------|-----------------|-------------|
| Case ID | `CaseId` or `IncidentId` | Unique identifier |
| Title | `Title` | Case subject |
| Description | `Description` | Initial case description |
| Status | `Status` or `StateCode` | Active, Resolved, etc. |
| Severity | `Severity` | Sev A, B, C, D |
| Created Date | `CreatedOn` | Case creation timestamp |
| Modified Date | `ModifiedOn` | Last update timestamp |
| Owner/Engineer | `OwnerAlias` or `EngineerAlias` | Assigned engineer |
| Customer | `CustomerId` or `CustomerName` | Customer reference |

### 2. Timeline Activities

| Data | Expected Table/Columns | Description |
|------|------------------------|-------------|
| Notes | `CaseNotes` or `Annotations` | Internal notes on case |
| Communications | `CaseActivities` or `Timeline` | Emails, calls, updates |
| Timestamps | `ActivityDate`, `CreatedOn` | When activity occurred |
| Direction | `DirectionCode` | Inbound vs outbound |

### 3. CSAT Scores (if available)

| Field | Expected Column | Description |
|-------|-----------------|-------------|
| Survey Score | `CSATScore` | 1-5 or 1-10 rating |
| Survey Date | `SurveyDate` | When survey was completed |
| Case Link | `CaseId` | Link to case |

---

## Access Request

| Requirement | Details |
|-------------|---------|
| **Access Type** | Read-only (Viewer role) |
| **Cluster URL** | *Need from DfM team* |
| **Database Name** | *Need from DfM team* |
| **Table Names** | *Need from DfM team* |
| **Identity** | `app-csatguardian-dev` (Enterprise Application) |
| **Object ID** | `7b0f0d42-0f23-48cd-b982-41abad5f1927` |

---

## Technical Questions

1. **Cluster URL**: What is the ADX cluster URL?
   - e.g., `https://dfmgov.kusto.windows.net` or `https://dfmgov.kusto.usgovcloudapi.net`

2. **Database & Tables**: What database and tables contain case data?
   - Cases, Timeline, CSAT scores

3. **Schema**: What are the column names and types?

4. **Authentication**: Can we use Managed Identity?
   - We have an Enterprise Application: `app-csatguardian-dev`
   - Object ID: `7b0f0d42-0f23-48cd-b982-41abad5f1927`

5. **Rate Limits**: Are there query limits we should be aware of?

6. **User-Assigned MSI**: Do we need to create a separate user-assigned managed identity specifically for ADX access?

---

## Our Environment

| Item | Details |
|------|---------|
| **Hosting** | Azure App Service (Commercial, Central US) |
| **Auth** | Managed Identity (MSI) |
| **SDK** | `azure-kusto-data` Python SDK |
| **Network** | Can use Private Endpoints if required |
| **Security** | No data stored locally - all queries on-demand |

---

## Sample Kusto Query (Expected)

```kusto
// Get active cases for a specific engineer
Cases
| where EngineerAlias == 'kmonteagudo'
| where Status == 'Active'
| project CaseId, Title, Severity, CreatedOn, ModifiedOn
| order by ModifiedOn desc
| take 100
```

---

## Business Justification

CSAT Guardian is an AI-powered coaching tool designed to help GSX (Government Support Engineers) improve their customer satisfaction scores. The application provides personalized, actionable feedback based on case handling patterns and CSAT survey results.

GSX engineer performance directly impacts customer satisfaction and retention for government customers. Currently, engineers lack timely, personalized feedback on their case handling behaviors that correlate with CSAT outcomes. CSAT Guardian addresses this gap by identifying patterns in case handling that correlate with positive or negative CSAT, providing proactive coaching before trends become problematic, enabling managers to support engineers with data-driven insights, and reducing time-to-insight from weeks of manual review to real-time.

Access is read-only with no modifications to source data. Authentication uses Managed Identity with no stored credentials. Access is scoped to the GSX organization. All data remains within the Microsoft tenant on Azure infrastructure.

---

## Contact

**Kyle Monteagudo**  
GSX Support Engineering  
kmonteagudo@microsoft.com
