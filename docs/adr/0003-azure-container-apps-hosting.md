# ADR 0003: Azure Container Apps for Application Hosting

## Status

**Superseded by [ADR 0004](0004-app-service-private-networking.md)** - January 24, 2026

> **Note**: This ADR documents the initial Container Apps decision. We subsequently moved to App Service with VNet integration for simpler private networking. See ADR 0004 for current architecture.

## Context

CSAT Guardian needs a hosting platform for its web API and background processing services. We needed to select a platform that balances simplicity, cost, and scalability.

### Options Considered

1. **Azure App Service** - Traditional PaaS web hosting
2. **Azure Container Apps** - Serverless container platform
3. **Azure Kubernetes Service (AKS)** - Full Kubernetes cluster
4. **Azure Functions** - Serverless functions

## Decision

We will use **Azure Container Apps** for hosting CSAT Guardian services.

## Rationale

1. **Serverless Containers**: Container Apps provides the flexibility of containers without managing infrastructure
2. **Cost Efficiency**: Scale-to-zero capability means we only pay when the app is used
3. **Simplicity**: Much simpler than AKS while still supporting containers
4. **Dapr Integration**: Built-in support for microservices patterns if needed later
5. **Managed Identity**: Native support for Azure Managed Identity

## Consequences

### Positive

- No infrastructure management overhead
- Automatic scaling based on HTTP traffic or KEDA scalers
- Built-in ingress with HTTPS
- Easy integration with Container Registry
- Supports revision management for blue-green deployments

### Negative

- Less control compared to AKS
- Azure Government requires `Consumption` workload profile (not default)
- Some advanced networking scenarios require additional configuration
- Cold start latency when scaling from zero

### Azure Government Considerations

In Azure Government, Container Apps requires explicit workload profile configuration:

```bicep
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-csatguardian-dev'
  location: 'usgovvirginia'
  properties: {
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  properties: {
    workloadProfileName: 'Consumption'  // Required in Azure Gov
    // ...
  }
}
```

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Container Apps Environment               │
│                   (cae-csatguardian-dev)               │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Container App (ca-csatguardian-dev)    │  │
│  │  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │  CSAT Guardian │  │   Managed Identity     │  │  │
│  │  │    API         │  │   (System-Assigned)    │  │  │
│  │  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
          │                        │
          ▼                        ▼
   ┌──────────────┐        ┌──────────────┐
   │  Key Vault   │        │  Azure SQL   │
   └──────────────┘        └──────────────┘
```

## Related

- ADR 0001: Azure Government Cloud Selection
- ADR 0002: Key Vault Secrets Management
- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
