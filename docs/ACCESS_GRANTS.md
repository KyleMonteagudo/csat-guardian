# CSAT Guardian - Access Grants & Security Status

> **Purpose:** Track security configuration and access grants for Azure resources.
> 
> **Last Updated:** February 4, 2026

---

## 🔐 Security Status

> ✅ **Local authentication is DISABLED** on all services. All access uses Managed Identity.

### Current Security Configuration

| Resource | Local Auth | Public Network | Auth Method |
|----------|------------|----------------|-------------|
| Azure SQL Server | ❌ Disabled | ❌ Disabled (Private Endpoint only) | Managed Identity |
| Azure OpenAI (AI Services) | ❌ Disabled | ❌ Disabled (Private Endpoint only) | Managed Identity |
| Azure AI Content Safety | ❌ Disabled | Via VNet | Managed Identity |
| Key Vault | ❌ Disabled | ❌ Disabled (Private Endpoint only) | Managed Identity (RBAC) |

---

## 📋 Managed Identity Role Assignments

### App Service Managed Identity

| Resource | Role | Purpose |
|----------|------|---------|
| Azure SQL Database | `db_datareader`, `db_datawriter` | Read/write case data |
| Azure OpenAI (AI Services) | `Cognitive Services User` | GPT-4o sentiment analysis |
| Azure AI Content Safety | `Cognitive Services User` | PII detection |
| Key Vault | `Key Vault Secrets User` | Read secrets (if needed) |

### SQL Server Entra Admin

| Principal | Role | Notes |
|-----------|------|-------|
| Kyle Monteagudo | SQL Admin | Entra ID authentication |

---

## 🚀 Transition Checklist - COMPLETED ✅

The following security hardening was completed in February 2026:

### Phase 1: Private Networking ✅
- [x] Create VNet for CSAT Guardian (`vnet-csatguardian-dev`)
- [x] Configure Private Endpoints for:
  - [x] Azure SQL Database (`pep-csatguardian-sql`)
  - [x] Azure Key Vault (`pep-csatguardian-kv`)
  - [x] Azure OpenAI / AI Services (`pep-csatguardian-ais`)
- [x] Set up Devbox VM in the VNet (`vm-devbox-csatguardian`)
- [x] Configure NSG rules

### Phase 2: Disable Local Auth ✅
- [x] Disable local auth on Azure SQL Server
- [x] Disable local auth on Azure OpenAI (AI Services)
- [x] Disable local auth on Azure AI Content Safety
- [x] Disable public network access on Key Vault
- [x] Configure App Service MSI with required RBAC roles

### Phase 3: Verified ✅
- [x] App works via private endpoints with managed identity
- [x] No public access remains on backend services
- [x] Documentation updated

---

## 📝 Commands to Verify Security Configuration

### Check SQL Server Auth Settings
```powershell
az sql server show --resource-group CSAT_Guardian_Dev --name sql-csatguardian-dev --query "administrators"
```

### List Cognitive Services (AI Services) Settings
```powershell
az cognitiveservices account show --resource-group CSAT_Guardian_Dev --name ais-csatguardian-dev --query "properties.disableLocalAuth"
```

### List Key Vault Network Rules
```powershell
az keyvault show --name kv-csatguard-dev --query "properties.networkAcls"
```

### List App Service Identity
```powershell
az webapp identity show --resource-group CSAT_Guardian_Dev --name app-csatguardian-dev
```

---

*This document was updated February 4, 2026 to reflect security hardening completion.*

*This document should be updated whenever access is granted or revoked.*
