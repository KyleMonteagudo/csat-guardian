# ADR 0001: Azure Government Cloud Selection

## Status

**Accepted** - January 23, 2026

## Context

CSAT Guardian is being developed as an internal Microsoft tool for support engineers. We needed to decide which Azure cloud environment to deploy to for development and eventually production.

### Options Considered

1. **Azure Commercial (Public)** - Standard Azure cloud
2. **Azure Government** - FedRAMP-compliant government cloud
3. **Azure China** - China-specific cloud

## Decision

We will deploy CSAT Guardian to **Azure Government** (usgovvirginia region).

## Rationale

1. **Microsoft Internal Tool**: As an internal Microsoft application, deploying to Azure Government aligns with internal compliance requirements
2. **FedRAMP Compliance**: Azure Government provides built-in compliance with FedRAMP High, which may be required for handling certain support case data
3. **Data Residency**: Azure Government ensures data stays within US boundaries
4. **Future-Proofing**: If CSAT Guardian handles any government customer support cases, the infrastructure is already compliant

## Consequences

### Positive

- Built-in compliance with government security standards
- Simplified compliance audits
- Data sovereignty guarantees
- Isolated from public cloud attack surfaces

### Negative

- Slightly different API endpoints (`.usgovcloudapi.net` vs `.azure.com`)
- Some Azure services may have delayed feature availability
- Need to use `--cloud AzureUSGovernment` flag with Azure CLI
- Container Apps requires `Consumption` workload profile in Azure Gov

### Technical Implications

| Resource | Endpoint Pattern |
|----------|-----------------|
| Key Vault | `*.vault.usgovcloudapi.net` |
| SQL Server | `*.database.usgovcloudapi.net` |
| Container Registry | `*.azurecr.us` |
| Container Apps | `*.azurecontainerapps.us` |

## Related

- [Azure Government Documentation](https://docs.microsoft.com/azure/azure-government/)
- [Azure Government vs Commercial Comparison](https://docs.microsoft.com/azure/azure-government/compare-azure-government-global-azure)
