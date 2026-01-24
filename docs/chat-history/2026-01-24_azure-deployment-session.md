# CSAT Guardian - Azure Deployment Session
**Date:** January 24, 2026

## Summary
Successfully deployed CSAT Guardian FastAPI application to Azure App Service with private networking.

## Key Accomplishments

### 1. App Service Deployment
- Created App Service `app-csatguardian-dev` manually via CLI (wasn't in Bicep)
- Scaled to S1 tier for faster startup (B1 was too slow, causing timeout loops)
- Set startup timeout: `WEBSITES_CONTAINER_START_TIME_LIMIT=600`
- Startup command: `python -m uvicorn api:app --host 0.0.0.0 --port 8000`

### 2. Environment Variables Configured
Set via Azure Portal (CLI had issues with special characters):
- `DATABASE_CONNECTION_STRING`: ADO.NET format (Server=...;Initial Catalog=...;User ID=...;Password=...)
- `AZURE_KEYVAULT_URL`: https://kv-csatguard-dev.vault.azure.net/
- `AZURE_OPENAI_ENDPOINT`: https://ais-csatguardian-dev.cognitiveservices.azure.com/
- `AZURE_OPENAI_DEPLOYMENT_NAME`: gpt-4o
- `USE_AZURE_CREDENTIAL`: true
- `WEBSITES_CONTAINER_START_TIME_LIMIT`: 600

### 3. Database Schema Fixes
Fixed `db_sync.py` to match actual Azure SQL schema:

**Actual column names (lowercase):**
- Engineers: `id, name, email, team` (not TeamsId)
- Customers: `id, name, company, tier`
- Cases: `id, title, customer_id, engineer_id, status, severity, created_at`
- TimelineEntries: `id, case_id, entry_type, content, sentiment_score, created_at`

**Code changes:**
- Updated all SQL queries to use lowercase column names
- Fixed `_map_status()` and `_map_priority()` to handle integer values (convert to string first)

### 4. Connection String Format
The code expects **ADO.NET format**, not ODBC:
```
Server=tcp:sql-csatguardian-dev.database.windows.net,1433;Initial Catalog=sqldb-csatguardian-dev;User ID=sqladmin;Password=YourSecureP@ssword123!;Encrypt=yes;TrustServerCertificate=no;
```

NOT this (ODBC format):
```
Driver={ODBC Driver 18 for SQL Server};Server=...;Database=...;Uid=...;Pwd=...
```

### 5. Deployment Workflow Established
```bash
# In Cloud Shell (with PAT for private repo)
cd ~/csat-guardian
git pull
cd src
az webapp up --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev --runtime "PYTHON:3.11"
```

### 6. requirements.txt Location
Must be in `src/` folder for deployment since we deploy from src directory.
Committed to repo: `src/requirements.txt`

## Issues Encountered & Solutions

| Issue | Solution |
|-------|----------|
| `az webapp deploy` token audience error in Cloud Shell | Use `az webapp up` instead |
| App timing out on B1 tier | Scale to S1 |
| Startup timeout (4 min default) | Set `WEBSITES_CONTAINER_START_TIME_LIMIT=600` |
| "No module named uvicorn" | Copy requirements.txt to src folder |
| "Invalid column name 'TeamsId'" | Update SQL queries to use actual column names (lowercase) |
| "'int' object has no attribute 'lower'" | Convert status/severity to string before calling .lower() |
| SQL login failed for user '' | Use ADO.NET format connection string, not ODBC |
| Private repo access from Cloud Shell | Create GitHub PAT and clone with it |

## Resource Reference
| Resource | Name |
|----------|------|
| Resource Group | CSAT_Guardian_Dev |
| App Service | app-csatguardian-dev |
| App Service Plan | asp-csatguardian-dev (S1) |
| SQL Server | sql-csatguardian-dev |
| SQL Database | sqldb-csatguardian-dev |
| Key Vault | kv-csatguard-dev |
| AI Services | ais-csatguardian-dev |
| Dev-box VM | vm-devbox-csatguardian |
| Bastion | bas-csatguardian-dev |

## Commits Made
1. `f83c922` - Fix db_sync.py to match actual Azure SQL schema
2. `1248885` - Fix _map_status and _map_priority to handle integer values  
3. `0298a56` - Add requirements.txt to src folder for deployment

## Testing
- App accessible via dev-box through Bastion
- `/health` endpoint works
- `/api/engineers` works (after schema fix)
- `/api/cases?engineer_id=eng-001` - pending test after latest deployment

## Next Steps
1. Complete API testing from dev-box
2. Test AI analysis endpoints
3. Close SQL public access firewall rule (TempAccess)
4. Revoke exposed GitHub PAT and create new one
5. Consider scaling back to B1 if startup time is acceptable
