# CSAT Guardian - Quick Reference Card

## 🔑 Credentials

| Resource | Username | Password/Key |
|----------|----------|--------------|
| SQL Server | `sqladmin` | Key Vault: `sql-admin-password` |
| Devbox VM | `testadmin` | Key Vault: `devbox-password` |
| Azure OpenAI | - | Key Vault: `azure-openai-key` |

---

## 🌐 URLs

| Service | URL |
|---------|-----|
| **Frontend UI** | https://app-csatguardian-dev.azurewebsites.net/ui |
| App Service (API) | https://app-csatguardian-dev.azurewebsites.net |
| Swagger Docs | https://app-csatguardian-dev.azurewebsites.net/docs |
| Kudu Console | https://app-csatguardian-dev.scm.azurewebsites.net/DebugConsole |
| Log Stream | https://app-csatguardian-dev.scm.azurewebsites.net/api/logstream |

---

## 🚀 Deployment Commands (Cloud Shell)

### Pull Latest Code
```bash
cd ~/csat-guardian && git pull origin develop
```

### Create Deployment Package
```bash
cd ~/csat-guardian
rm -f deploy.zip
zip -r deploy.zip src requirements.txt
download deploy.zip
```

### Deploy Database Schema
```bash
# Get password from Key Vault first
sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev \
  -U sqladmin -P '<password-from-keyvault>' -i infrastructure/sql/001-schema-complete.sql
```

### Restart App Service
```bash
az webapp restart --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev
```

---

## 🔧 Required App Settings

| Setting | Value |
|---------|-------|
| `AZURE_OPENAI_ENDPOINT` | `https://ais-csatguardian-dev.cognitiveservices.azure.com/` |
| `AZURE_OPENAI_API_KEY` | `@Microsoft.KeyVault(VaultName=kv-csatguard-dev;SecretName=azure-openai-key)` |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` |
| `DATABASE_CONNECTION_STRING` | `Server=tcp:sql-csatguardian-dev.database.windows.net,1433;...` |
| `WEBSITE_VNET_ROUTE_ALL` | `1` |
| `WEBSITES_PORT` | `8000` |

⚠️ **Important**: Use `AZURE_OPENAI_DEPLOYMENT`, NOT `AZURE_OPENAI_DEPLOYMENT_NAME`

---

## 📍 Startup Command (App Service)

```
cd /home/site/wwwroot/src && pip install -r requirements.txt && python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

---

## ✅ Verification Commands (Devbox VM PowerShell)

### Health Check
```powershell
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/health"
```

### List Cases
```powershell
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/cases"
```

### Chat with Agent
```powershell
$body = @{ message = "Check CSAT rules for case-001"; engineer_id = "eng-001" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://app-csatguardian-dev.azurewebsites.net/api/chat" -Method POST -ContentType "application/json" -Body $body
```

---

## 🛠️ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "No module named uvicorn" | Add `pip install -r requirements.txt` to startup command |
| SQL connection fails | Check `WEBSITE_VNET_ROUTE_ALL=1` and restart |
| Chat returns error | Verify `AZURE_OPENAI_DEPLOYMENT` (not DEPLOYMENT_NAME) |
| Kudu upload fails | Enable SCM Basic Auth in Portal |
| Old code running | Clear wwwroot, redeploy, restart |

---

## 📁 Key File Locations

| File | Purpose |
|------|---------|
| `src/api.py` | FastAPI endpoints + static file serving |
| `src/static/index.html` | **Frontend UI (Microsoft Learn-style)** |
| `src/static/css/styles.css` | **Frontend styles (Fluent Design)** |
| `src/static/js/app.js` | **Frontend JavaScript (~870 lines)** |
| `src/agent/guardian_agent.py` | Semantic Kernel agent |
| `src/db_sync.py` | Azure SQL database client |
| `src/models.py` | Pydantic data models |
| `infrastructure/sql/001-schema-complete.sql` | Database schema |
| `infrastructure/sql/002-seed-data.sql` | Test data (8 cases) |
