# CSAT Guardian - Session State

> **Last Updated**: January 23, 2026, 11:00 AM EST
> **Sprint**: Sprint 0 (Infrastructure) → Sprint 1 (UI) 
> **Status**: ✅ Infrastructure & Docs Complete, Ready for Streamlit UI

---

## Quick Context for AI Assistant

When starting a new session, say:

```
Read the SESSION_STATE.md file in the csat-guardian project to understand where we left off and what to do next.
```

---

## Current State Summary

### ✅ Completed (Sprint 0)

1. **Private Networking Infrastructure** - All deployed and tested
   - VNet: `vnet-csatguardian-dev` (10.100.0.0/16)
   - App Service: `app-csatguardian-dev.azurewebsites.us` (VNet integrated)
   - Private Endpoints: SQL (10.100.2.4), Key Vault (10.100.2.5), OpenAI (10.100.2.6)
   - Private DNS Zones: 3 zones configured with VNet links

2. **Azure OpenAI** - Deployed in project resource group
   - Resource: `oai-csatguardian-dev.openai.azure.us`
   - Model: gpt-4o (version 2024-11-20)
   - Deployment: `gpt-4o`

3. **Core Application** - Working end-to-end
   - Sentiment analysis with Azure OpenAI ✅
   - Azure SQL connectivity ✅
   - Key Vault secret retrieval ✅
   - Alert generation and deduplication ✅
   - Batch scan mode (`python main.py scan`) ✅

4. **Documentation** - Fully updated with diagrams
   - ARCHITECTURE.md - Updated with VNet diagrams, linked to infrastructure diagrams
   - README.md - Updated with Mermaid diagrams, feature status table, accurate project structure
   - AZURE_GOVERNMENT.md - Updated with deployed resources
   - PROJECT_PLAN.md - Updated Sprint 0 checklist
   - FILE_REFERENCE.md - Updated with Bicep modules and diagrams folder
   - ADR 0004 - Created for App Service decision
   - **NEW**: `docs/diagrams/infrastructure.md` - Comprehensive Mermaid diagrams for security reviews

### ⏳ In Progress / Next Steps

1. **Create Streamlit POC UI** (HIGH PRIORITY)
   - Dashboard showing case overview
   - Real-time chat with Guardian agent
   - Alert visualization
   - File: `src/app.py` (to be created)

2. **Deploy to App Service**
   - Use `az webapp up` or ZIP deploy
   - Configure app settings for Key Vault
   - Test private endpoint connectivity from App Service

3. **Disable Public Access** (after app deployed)
   - SQL Server: `publicNetworkAccess: 'Disabled'`
   - Key Vault: `publicNetworkAccess: 'Disabled'`
   - OpenAI: `publicNetworkAccess: 'Disabled'`

4. **Reduce Log Verbosity**
   - Change default LOG_LEVEL from DEBUG to INFO
   - Less noisy console output

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/main.py` | CLI entry point (scan, chat, monitor commands) |
| `src/config.py` | Configuration management |
| `src/agent/guardian_agent.py` | Conversational AI agent |
| `src/services/sentiment_service.py` | Azure OpenAI sentiment analysis |
| `infrastructure/bicep/main-private.bicep` | Main IaC template |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/PROJECT_PLAN.md` | Sprint planning and progress |
| **`docs/diagrams/infrastructure.md`** | **Mermaid diagrams for security reviews** |

---

## Azure Resources (rg-csatguardian-dev)

| Resource | Name | Endpoint |
|----------|------|----------|
| Resource Group | rg-csatguardian-dev | USGov Virginia |
| VNet | vnet-csatguardian-dev | 10.100.0.0/16 |
| App Service | app-csatguardian-dev | https://app-csatguardian-dev.azurewebsites.us |
| Azure OpenAI | oai-csatguardian-dev | https://oai-csatguardian-dev.openai.azure.us |
| SQL Server | sql-csatguardian-dev | sql-csatguardian-dev.database.usgovcloudapi.net |
| SQL Database | sqldb-csatguardian-dev | (on above server) |
| Key Vault | kv-csatguardian-dev | https://kv-csatguardian-dev.vault.usgovcloudapi.net |

---

## Important Notes

1. **Azure Government Cloud** - All endpoints use `.us` domains
2. **Public access still enabled** - For local development; disable after deploying app
3. **Streamlit is POC only** - Production will use Teams Bot
4. **Mock clients** - DfM and Teams are mocked; real integration pending approval

---

## Test Command

To verify everything works:
```powershell
cd csat-guardian/src
..\env\Scripts\Activate.ps1
python main.py scan
```

Expected: 6 cases analyzed, 0 errors

---

## ⚠️ CRITICAL GUARDRAILS

**Resource Group Boundaries - DO NOT VIOLATE:**
- ✅ Only work within: `rg-csatguardian-dev`
- ❌ **NEVER** modify resources in `kmonteagudo` RG or any other resource group
- ❌ **NEVER** reference or depend on resources outside `rg-csatguardian-dev`
- All new Azure resources MUST be created in `rg-csatguardian-dev`
- Azure OpenAI is already in project RG (decoupled from kmonteagudo RG)

**Other Restrictions:**
- ❌ Don't delete existing resources in `rg-csatguardian-dev` without explicit approval
- ❌ Don't change the VNet address space (10.100.0.0/16)
- ❌ Don't disable public access until app is deployed to App Service
- ❌ Don't commit `.env.local`, secrets, or connection strings
- ❌ Don't create resources in other subscriptions

---

*Update this file at the end of each session to maintain continuity.*
