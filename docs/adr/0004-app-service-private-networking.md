# ADR 0004: App Service with Private Networking

## Status

**Accepted** - January 24, 2026

## Context

After initial deployment with Azure Container Apps (see [ADR 0003](0003-azure-container-apps-hosting.md)), we needed to implement private networking for all Azure-to-Azure communication. The requirement was:

> "Private endpoints for all communication even between Azure services because we want no public access."

This required a re-evaluation of hosting options to find the best approach for VNet integration with Private Endpoints.

### Options Re-Evaluated

1. **Azure Container Apps** - Originally selected, but VNet integration requires additional configuration
2. **Azure App Service** - Native VNet integration, simpler for single-app scenarios
3. **Azure Kubernetes Service (AKS)** - Overkill for POC

## Decision

We will use **Azure App Service** with **VNet integration** for hosting the CSAT Guardian Streamlit POC application.

## Rationale

1. **Native VNet Integration**: App Service has built-in support for VNet integration via subnet delegation
2. **Simpler Architecture**: No need for Container Registry or container builds for Python apps
3. **Private Endpoints**: Can easily reach SQL, Key Vault, and OpenAI via Private Endpoints
4. **Azure Government Support**: Well-supported in Azure Government with all features
5. **Python Support**: Native Python 3.12 runtime, no containerization needed
6. **Managed Identity**: System-assigned identity for Key Vault and SQL access

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRIVATE NETWORKING ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                 VNet: vnet-csatguardian-dev (10.100.0.0/16)         │
│                                                                      │
│  ┌─────────────────────────┐    ┌────────────────────────────────┐ │
│  │  snet-appservice        │    │  snet-privateendpoints         │ │
│  │  10.100.1.0/24          │    │  10.100.2.0/24                 │ │
│  │                         │    │                                │ │
│  │  ┌───────────────────┐  │    │  ┌──────────────────────────┐ │ │
│  │  │   App Service     │──┼────┼──│  pep-sql     (10.100.2.4)│ │ │
│  │  │   (Streamlit)     │  │    │  │  pep-kv      (10.100.2.5)│ │ │
│  │  │   VNet Integrated │  │    │  │  pep-openai  (10.100.2.6)│ │ │
│  │  └───────────────────┘  │    │  └──────────────────────────┘ │ │
│  └─────────────────────────┘    └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │                                    │
         │                                    ▼
         │              ┌─────────────────────────────────────────┐
         │              │         PRIVATE DNS ZONES               │
         │              │  privatelink.database.usgovcloudapi.net │
         │              │  privatelink.vaultcore.usgovcloudapi.net│
         │              │  privatelink.openai.azure.us            │
         │              └─────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Azure SQL     │  │   Key Vault     │  │  Azure OpenAI   │
│   (Private)     │  │   (Private)     │  │   (Private)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Deployed Resources

| Resource | Name | Configuration |
|----------|------|---------------|
| App Service Plan | `asp-csatguardian-dev` | Linux B1, Python 3.12 |
| App Service | `app-csatguardian-dev` | VNet integrated, route all enabled |
| VNet | `vnet-csatguardian-dev` | 10.100.0.0/16 |
| App Service Subnet | `snet-appservice` | 10.100.1.0/24, delegated to Web/serverFarms |
| PE Subnet | `snet-privateendpoints` | 10.100.2.0/24 |
| SQL Private Endpoint | `pep-csatguardian-dev-sql` | 10.100.2.4 |
| Key Vault Private Endpoint | `pep-csatguardian-dev-kv` | 10.100.2.5 |
| OpenAI Private Endpoint | `pep-csatguardian-dev-oai` | 10.100.2.6 |

## Consequences

### Positive

- **Complete Network Isolation**: All backend services only accessible via private endpoints
- **No Public Exposure**: SQL, Key Vault, and OpenAI have no public access
- **Simpler Deployment**: ZIP deploy or `az webapp up` without containerization
- **Native Python**: Direct Python 3.12 runtime without Docker
- **Lower Latency**: VNet integration provides faster, more reliable connectivity
- **Compliance**: Meets federal requirements for private networking

### Negative

- **Higher Cost**: Private endpoints add ~$7.30/month each (~$22/month total)
- **No Scale-to-Zero**: App Service runs continuously (unlike Container Apps consumption)
- **Fixed Pricing**: B1 tier is fixed cost vs. consumption-based
- **Limited Auto-Scale**: Need Premium tier for advanced auto-scaling rules

### Trade-offs Accepted

| Aspect | Container Apps | App Service | Decision |
|--------|---------------|-------------|----------|
| Cost | Lower (scale-to-zero) | Higher (always on) | Accept for simplicity |
| VNet Integration | Requires additional config | Native | Prefer native |
| Deployment | Container builds required | ZIP deploy | Prefer simpler |
| Scaling | Auto-scale included | Manual (B1) | OK for POC |

## Implementation

### Bicep Modules Created

- `modules/networking.bicep` - VNet and subnets
- `modules/private-dns.bicep` - Private DNS zones with VNet links
- `modules/openai.bicep` - Azure OpenAI with gpt-4o deployment
- `modules/private-endpoints.bicep` - All private endpoints
- `modules/appservice.bicep` - App Service Plan and Web App

### Key Configuration

```bicep
// App Service with VNet Integration
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  properties: {
    virtualNetworkSubnetId: appServiceSubnet.id
    vnetRouteAllEnabled: true  // Route all outbound through VNet
    httpsOnly: true
  }
}

// Subnet delegation for App Service
resource appServiceSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' = {
  properties: {
    delegations: [
      {
        name: 'appServiceDelegation'
        properties: {
          serviceName: 'Microsoft.Web/serverFarms'
        }
      }
    ]
  }
}
```

## Future Considerations

1. **Production Scaling**: Upgrade to P1v3 or P2v3 for auto-scaling
2. **Teams Integration**: Will eventually replace Streamlit POC with Teams Bot
3. **Public Access Lockdown**: Disable public access on SQL, Key Vault, OpenAI after testing
4. **WAF**: Consider Azure Front Door with WAF for production

## References

- [Azure App Service VNet Integration](https://learn.microsoft.com/en-us/azure/app-service/overview-vnet-integration)
- [Private Endpoints for Azure Services](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview)
- [ADR 0003: Container Apps (superseded)](0003-azure-container-apps-hosting.md)
