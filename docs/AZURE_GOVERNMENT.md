# CSAT Guardian - Azure Government Considerations

## Overview

CSAT Guardian is deployed in **Azure Government** cloud, which has:
- Different service endpoints (`.us` instead of `.com`)
- Different regional availability
- Some feature parity gaps with Azure Commercial
- Compliance requirements (FedRAMP, DoD IL2-IL5)

---

## Deployed Resources

CSAT Guardian is deployed to **rg-csatguardian-dev** in **USGov Virginia** with private networking:

| Resource | Name | Private Endpoint IP |
|----------|------|---------------------|
| **Virtual Network** | vnet-csatguardian-dev | 10.100.0.0/16 |
| **Azure OpenAI** | oai-csatguardian-dev | 10.100.2.6 |
| **Azure SQL** | sql-csatguardian-dev | 10.100.2.4 |
| **Key Vault** | kv-csatguardian-dev | 10.100.2.5 |
| **App Service** | app-csatguardian-dev | VNet Integrated |
| **App Service Plan** | asp-csatguardian-dev | Linux B1 |

### Private DNS Zones

| Zone | VNet Linked |
|------|-------------|
| privatelink.database.usgovcloudapi.net | ✅ |
| privatelink.vaultcore.usgovcloudapi.net | ✅ |
| privatelink.openai.azure.us | ✅ |

---

## 1. Azure Government Endpoints

| Service | Commercial Endpoint | Government Endpoint |
|---------|--------------------|--------------------|
| **Azure OpenAI** | `https://{resource}.openai.azure.com/` | `https://{resource}.openai.azure.us/` |
| **Key Vault** | `https://{vault}.vault.azure.net/` | `https://{vault}.vault.usgovcloudapi.net/` |
| **Azure SQL** | `{server}.database.windows.net` | `{server}.database.usgovcloudapi.net` |
| **Microsoft Graph** | `https://graph.microsoft.com/` | `https://graph.microsoft.us/` |
| **Azure AD** | `https://login.microsoftonline.com/` | `https://login.microsoftonline.us/` |
| **Container Registry** | `{registry}.azurecr.io` | `{registry}.azurecr.us` |
| **Storage** | `{account}.blob.core.windows.net` | `{account}.blob.core.usgovcloudapi.net` |
| **App Insights** | `https://dc.services.visualstudio.com/` | `https://dc.applicationinsights.us/` |

---

## 2. Service Availability in Azure Government

### ✅ Available Services (Used by CSAT Guardian)

| Service | Gov Availability | Regions | Notes |
|---------|-----------------|---------|-------|
| **Azure OpenAI** | ✅ GA | USGov Virginia, USGov Arizona | GPT-4o (2024-11-20) deployed |
| **Azure Key Vault** | ✅ GA | All Gov regions | Full feature parity |
| **Azure SQL Database** | ✅ GA | All Gov regions | Full feature parity |
| **Azure App Service** | ✅ GA | All Gov regions | Python 3.12, Linux |
| **Virtual Network** | ✅ GA | All Gov regions | Private Endpoints |
| **Private DNS Zones** | ✅ GA | All Gov regions | Gov-specific zone names |
| **Application Insights** | ✅ GA | All Gov regions | Full feature parity |
| **Azure Monitor** | ✅ GA | All Gov regions | Full feature parity |
| **Azure AD** | ✅ GA | All Gov regions | Full feature parity |

### ⚠️ Feature Parity Considerations

| Feature | Status | Workaround |
|---------|--------|------------|
| Container Apps Jobs | May have limited availability | Use Azure Functions if needed |
| Dapr integration | Check current status | Standard HTTP if unavailable |
| Azure OpenAI Assistants API | Limited | Use Chat Completions API |
| Some GPT models | Check availability | Use available models |

---

## 3. Recommended Azure Government Regions

| Priority | Region | Services Available |
|----------|--------|-------------------|
| 1 | **USGov Virginia** | All services including Azure OpenAI |
| 2 | **USGov Arizona** | All services including Azure OpenAI |
| 3 | USGov Texas | Most services (verify OpenAI) |

**Recommendation:** Deploy to **USGov Virginia** for best service availability.

---

## 4. Azure OpenAI in Government

### Available Models (as of Jan 2026)

| Model | Availability | Use Case |
|-------|--------------|----------|
| GPT-4o | ✅ Available | Sentiment analysis, recommendations |
| GPT-4 | ✅ Available | Alternative to GPT-4o |
| GPT-3.5-Turbo | ✅ Available | Lower cost option |
| text-embedding-ada-002 | ✅ Available | If embeddings needed |

### API Differences

```python
# Commercial
endpoint = "https://myresource.openai.azure.com/"

# Government
endpoint = "https://myresource.openai.azure.us/"
```

### Compliance

Azure OpenAI in Government is:
- FedRAMP High authorized
- DoD IL2 authorized
- Suitable for government workloads

---

## 5. Microsoft Graph for Government

### Endpoint Change

```python
# Commercial
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

# Government
GRAPH_BASE_URL = "https://graph.microsoft.us/v1.0"
```

### Teams in Government

Teams for Government (GCC, GCC High) has some limitations:
- Bot Framework may require GCC-specific configuration
- Webhooks work similarly but with `.us` endpoints
- Some Teams apps may not be available

### Authentication Endpoint

```python
# Commercial
AUTH_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

# Government
AUTH_ENDPOINT = "https://login.microsoftonline.us/{tenant}/oauth2/v2.0/token"
```

---

## 6. Configuration for Government

### Deployed Endpoints (CSAT Guardian)

```bash
# Azure OpenAI (deployed via private endpoint)
AZURE_OPENAI_ENDPOINT=https://oai-csatguardian-dev.openai.azure.us/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Key Vault (deployed via private endpoint)
AZURE_KEY_VAULT_URL=https://kv-csatguardian-dev.vault.usgovcloudapi.net/

# Azure SQL (deployed via private endpoint)
SQL_SERVER=sql-csatguardian-dev.database.usgovcloudapi.net
SQL_DATABASE=csatdb

# App Service (VNet integrated)
APP_SERVICE_URL=https://app-csatguardian-dev.azurewebsites.us

# Microsoft Graph (Gov endpoint)
GRAPH_BASE_URL=https://graph.microsoft.us/v1.0

# Azure AD (Gov endpoint)
AZURE_AD_ENDPOINT=https://login.microsoftonline.us/
```

### Azure SDK Configuration

```python
from azure.identity import DefaultAzureCredential

# For Azure Government, set the authority host
credential = DefaultAzureCredential(
    authority="https://login.microsoftonline.us"
)

# Or use environment variable
# AZURE_AUTHORITY_HOST=https://login.microsoftonline.us
```

---

## 7. Deployment Considerations

### Azure CLI for Government

```powershell
# Set Azure CLI to use Government cloud
az cloud set --name AzureUSGovernment

# Login to Government
az login

# Verify cloud setting
az cloud show
```

### Bicep/ARM Considerations

- Use Government-specific resource providers
- Verify SKU availability in Gov regions
- Some ARM API versions may differ

### GitHub Actions for Government

```yaml
- name: Azure Login (Government)
  uses: azure/login@v2
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
    environment: AzureUSGovernment  # Critical!
```

---

## 8. Compliance Requirements

### Data Residency

- All data stored in US Government regions
- No data leaves US sovereign boundaries
- Azure OpenAI processes data in US Gov datacenters

### Certifications

CSAT Guardian deployment should meet:
- FedRAMP High (inherited from Azure Gov)
- DoD IL2 minimum
- ITAR (if applicable)

### Audit Requirements

- All access logged to Azure Monitor
- Key Vault access audited
- No PII stored (by design)

---

## 9. Testing in Government

### Verify Endpoints

```python
# Test script to verify Gov endpoints
import httpx

endpoints = {
    "Key Vault": "https://kv-csatguardian-dev.vault.usgovcloudapi.net/",
    "Azure OpenAI": "https://your-resource.openai.azure.us/",
    "Graph": "https://graph.microsoft.us/v1.0/$metadata",
}

for name, url in endpoints.items():
    try:
        response = httpx.head(url, timeout=5)
        print(f"✅ {name}: {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

---

## 10. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Resource not found" | Using commercial endpoint | Update to `.us` endpoints |
| Authentication failed | Wrong authority | Use `login.microsoftonline.us` |
| Service unavailable | Region doesn't have service | Deploy to USGov Virginia |
| API version not supported | Version not in Gov | Use older API version |

### Helpful Commands

```powershell
# Check which cloud you're connected to
az cloud show --query name

# List available regions in Gov
az account list-locations --query "[?metadata.regionType=='Physical']"

# Check service availability
az provider show --namespace Microsoft.CognitiveServices --query "resourceTypes[?resourceType=='accounts'].locations"
```

---

*Document Version: 1.0*  
*Last Updated: January 23, 2026*  
*Cloud: Azure Government*
