# CSAT Guardian - Azure Deployment Session
**Date:** January 24, 2026
**Duration:** Extended session (multiple hours)

---

## Executive Summary

This document captures the complete deployment session for CSAT Guardian to Commercial Azure. The session involved infrastructure deployment, troubleshooting, and identifying areas for improvement in the agent's capabilities.

**Final Status:**
- ✅ App Service deployed and running on Premium V3
- ✅ VNet integration configured
- ✅ AI Services connectivity working (via private endpoint)
- ✅ Database connectivity working
- ✅ Core API endpoints functional
- ⚠️ Test data seeding incomplete (schema mismatch)
- ⚠️ Chat functionality is placeholder (not AI-powered)
- ⏳ Agent prompts need improvement for production quality

---

## Session Constraints (User Guardrails)

**IMPORTANT - These constraints must be remembered:**

1. **No passwords/secrets in repo** - Never commit credentials to git
2. **Cloud Shell limitations** - MSI token audience errors with some `az webapp` commands
3. **Dev-box limitations** - No Python installed, no Azure CLI auth, no git auth
4. **SQL access** - Only via private endpoint (no Query Editor access)
5. **All Azure changes should be in Bicep** - For repeatability

---

## Infrastructure Deployed

### Azure Resources (CSAT_Guardian_Dev)

| Resource | Name | Configuration |
|----------|------|---------------|
| Resource Group | `CSAT_Guardian_Dev` | Central US |
| App Service | `app-csatguardian-dev` | Premium V3, Python 3.11, Linux |
| App Service Plan | `asp-csatguardian-dev` | P1v3 tier |
| SQL Server | `sql-csatguardian-dev` | Private endpoint only |
| SQL Database | `sqldb-csatguardian-dev` | Basic tier |
| AI Services | `ais-csatguardian-dev` | gpt-4o deployment, private endpoint only |
| Key Vault | `kv-csatguard-dev` | Stores API keys and connection strings |
| VNet | `vnet-csatguardian-dev` | 10.100.0.0/16 |
| Dev-box VM | `vm-devbox-csatguardian` | Windows 11, access via Bastion |
| Bastion | `bas-csatguardian-dev` | Secure RDP access |

### VNet Subnets

| Subnet | CIDR | Purpose |
|--------|------|---------|
| snet-appservice | 10.100.1.0/24 | App Service VNet integration |
| snet-privateendpoints | 10.100.2.0/24 | SQL, AI Services, Key Vault endpoints |
| snet-devbox | 10.100.3.0/24 | Dev-box VM |
| AzureBastionSubnet | 10.100.4.0/26 | Azure Bastion |

---

## Key Technical Discoveries

### 1. Database Schema Mismatch

**Problem:** The `seed-database.sql` and original `db_sync.py` used different column names than the actual Azure SQL schema.

**Actual Azure SQL Schema (lowercase columns):**
```
Engineers: id, name, email, team
Customers: id, name, company, tier  
Cases: id, title, customer_id, engineer_id, status, severity, created_at
TimelineEntries: id, case_id, entry_type, content, sentiment_score, created_at
```

**What was expected (seed-database.sql):**
```
Engineers: Id, Name, Email, TeamsId
Cases: Id, Title, OwnerId, CustomerId, CreatedOn, ModifiedOn
TimelineEntries: Id, CaseId, EntryType, CreatedOn, CreatedBy
```

**Resolution:** Fixed `db_sync.py` to use actual schema. Added `/api/admin/seed` endpoint with correct schema. Seed files still need updating.

### 2. Connection String Format

**Problem:** Code expected ADO.NET format but received ODBC format.

**Correct format (ADO.NET):**
```
Server=tcp:sql-csatguardian-dev.database.windows.net,1433;Initial Catalog=sqldb-csatguardian-dev;User ID=sqladmin;Password=xxx;Encrypt=yes;TrustServerCertificate=no;
```

### 3. App Service Tier for VNet Integration

**Problem:** B1 tier doesn't support VNet integration (config was ignored).

**Solution:** Scaled to Premium V3 (P1v3) which supports VNet integration.

### 4. Azure OpenAI Authentication

**Problem:** 403 Forbidden when App Service called AI Services.

**Cause:** AI Services has public access disabled, requires private endpoint access.

**Solution:** 
1. App Service VNet integration to snet-appservice
2. VNet can reach AI Services via private endpoint
3. API key stored in Key Vault with Key Vault reference

### 5. Cloud Shell Deployment Issues

**Problem:** `az webapp up` and `az webapp deploy` fail with MSI token audience error.

**Workaround Options:**
- Use `az webapp deployment source config` with GitHub
- Use Kudu zip deploy with publishing credentials
- Use `az logout && az login --scope "https://management.azure.com/.default"`

---

## Code Changes Made

### Commits (develop branch)

1. `f83c922` - Fix db_sync.py to match actual Azure SQL schema
2. `1248885` - Fix _map_status and _map_priority to handle integer values
3. `0298a56` - Add requirements.txt to src folder for deployment
4. `c867548` - Update Bicep: P1v3 SKU, API key setting, startup timeout
5. `9d96859` - Add Python script to run seed SQL from dev-box
6. `6cbf226` - Add /api/admin/seed endpoint to populate test data
7. `0b0a8cf` - Fix seed endpoint to use actual DB schema (lowercase columns)

### Bicep Updates (main-commercial.bicep)

- App Service Plan: B1 → P1v3
- Added `AZURE_OPENAI_API_KEY` with Key Vault reference
- Added `AZURE_OPENAI_DEPLOYMENT_NAME` setting
- Added `WEBSITES_CONTAINER_START_TIME_LIMIT=600`

---

## Testing Status

### Working Endpoints
- ✅ `/` - Root health check
- ✅ `/api/health` - Detailed health status
- ✅ `/api/engineers` - List engineers
- ✅ `/api/cases` - List cases with filters
- ✅ `/api/cases/{id}` - Get case details
- ✅ `/api/analyze/{id}` - Sentiment analysis (AI works)

### Pending/Issues
- ⚠️ `/api/admin/seed` - Not deployed (deployment sync issues)
- ⚠️ `/api/chat` - Uses hardcoded responses, not AI
- ⚠️ `/api/alerts` - Returns 0 alerts (test data missing)

---

## Outstanding Issues

### 1. Seed Data Not Loaded
- Only 2 test cases (case-001, case-002) exist
- Full seed script has wrong schema
- `/api/admin/seed` endpoint written but not deployed

### 2. Chat is Not AI-Powered
The `/api/chat` endpoint uses keyword matching:
```python
if any(word in message for word in ["risk", "csat", "concern"]):
    response = "Based on the case analysis, I recommend..."
```

This needs to be replaced with Semantic Kernel agent that can:
- Understand natural language questions
- Access case data via plugins
- Provide specific, contextual answers

### 3. Agent Quality Concerns
User feedback: Analysis is "too generic" and "doesn't feel close to meeting expected impact."

**Problems identified:**
- Prompts focus only on sentiment scoring
- No CSAT domain knowledge in prompts
- No case context in conversations
- Cannot answer questions like "how long since my last note"

---

## Questions Pending (For Next Session)

The following questions need answers to improve the agent:

**1. User Interaction Model**
- Teams chat only, or also proactive notifications?
- Should the agent initiate conversations?

**2. Data Access**
- What DfM data will agent access?
- Own cases only or team-wide?
- Customer tier, contract details, previous CSAT scores?

**3. CSAT Domain Knowledge**
- What are the actual SLA rules?
- What factors drive CSAT scores?
- Escalation paths?

**4. Guardrails**
- What should the agent NOT do/say?
- Sensitive recommendations to avoid?

**5. Expected Interactions**
- 3-5 example questions engineers would ask
- What does a "great" answer look like?

**6. Success Metrics**
- How to measure agent value?
- What's "good enough for POC"?

---

## Files That Need Cleanup

| File | Issue | Action Needed |
|------|-------|---------------|
| `infrastructure/seed-database.sql` | Wrong schema | Update to match actual DB |
| `infrastructure/run-seed.py` | Wrong schema | Update or remove |
| `src/api.py` | Chat is hardcoded | Replace with SK agent |
| `docs/FILE_REFERENCE.md` | Shows B1 tier | Update to P1v3 |

---

## Deployment Commands Reference

### From Cloud Shell (working methods)

**Option 1: GitHub deployment source**
```bash
az webapp deployment source config \
  --name app-csatguardian-dev \
  --resource-group CSAT_Guardian_Dev \
  --repo-url https://github.com/kmonteagudo_microsoft/csat-guardian \
  --branch develop \
  --manual-integration

az webapp deployment source sync \
  --name app-csatguardian-dev \
  --resource-group CSAT_Guardian_Dev
```

**Option 2: Kudu zip deploy**
```bash
cd ~/csat-guardian/src
zip -r ../deploy.zip .
CREDS=$(az webapp deployment list-publishing-credentials --name app-csatguardian-dev --resource-group CSAT_Guardian_Dev --query "{user:publishingUserName,pass:publishingPassword}" -o tsv)
curl -X POST -u "$USER:$PASS" --data-binary @../deploy.zip \
  "https://app-csatguardian-dev.scm.azurewebsites.net/api/zipdeploy"
```

### App Service Configuration
```bash
# Update startup command
az webapp config set \
  --name app-csatguardian-dev \
  --resource-group CSAT_Guardian_Dev \
  --startup-file "python -m uvicorn api:app --host 0.0.0.0 --port 8000"

# Restart
az webapp restart --name app-csatguardian-dev --resource-group CSAT_Guardian_Dev

# Add VNet integration
az webapp vnet-integration add \
  --name app-csatguardian-dev \
  --resource-group CSAT_Guardian_Dev \
  --vnet vnet-csatguardian-dev \
  --subnet snet-appservice
```

---

## Next Session Priorities

1. **Answer agent design questions** (see Questions Pending section)
2. **Improve agent prompts** with CSAT domain knowledge
3. **Replace hardcoded chat** with Semantic Kernel agent
4. **Clean up seed files** to match actual schema
5. **Consider DfM integration** vs Azure SQL test data
3. Close SQL public access firewall rule (TempAccess)
4. Revoke exposed GitHub PAT and create new one
5. Consider scaling back to B1 if startup time is acceptable
