# ADR 0002: Azure Key Vault for Secrets Management

## Status

**Accepted** - January 23, 2026

## Context

CSAT Guardian requires secure storage for sensitive configuration values including:
- Azure OpenAI API keys and endpoints
- SQL Server connection strings and passwords
- Application Insights connection strings

We needed to decide how to manage these secrets securely across development and production environments.

### Options Considered

1. **Environment Variables** - Store secrets in `.env` files or system environment variables
2. **Azure Key Vault** - Centralized secrets management with RBAC
3. **Azure App Configuration** - Configuration management with optional Key Vault references
4. **GitHub Secrets** - For CI/CD pipelines only

## Decision

We will use **Azure Key Vault** as the primary secrets store, with **Managed Identity** for authentication from Azure services.

## Rationale

1. **Security**: Key Vault provides hardware-backed encryption and audit logging
2. **Zero Trust**: Managed Identity eliminates the need to store credentials for accessing secrets
3. **Centralization**: Single source of truth for all secrets across environments
4. **Compliance**: Key Vault meets FedRAMP High requirements
5. **Rotation**: Supports automatic secret rotation policies

## Consequences

### Positive

- No secrets in source code or configuration files
- Complete audit trail of secret access
- Easy secret rotation without redeployment
- RBAC controls for who can read/write secrets
- Works seamlessly with Container Apps via Managed Identity

### Negative

- Requires Azure CLI authentication for local development
- Adds latency for secret retrieval (mitigated by caching)
- Additional Azure resource cost (minimal)
- Local development requires Key Vault Secrets User role

### Implementation

**Secret Naming Convention:**
```
{Category}--{SecretName}

Examples:
- AzureOpenAI--ApiKey
- AzureOpenAI--Endpoint
- SqlServer--ConnectionString
- AppInsights--ConnectionString
```

**Local Development Access:**
```bash
# Authenticate to Azure Government
az cloud set --name AzureUSGovernment
az login

# Retrieve secret
az keyvault secret show --vault-name kv-csatguardian-dev --name AzureOpenAI--ApiKey --query value -o tsv
```

**Production Access (Container Apps):**
- System-assigned Managed Identity enabled
- Key Vault Secrets User role assigned
- Secrets referenced via Key Vault SecretUri in app settings

## Secrets Inventory

| Secret Name | Purpose | Rotatable |
|-------------|---------|-----------|
| AzureOpenAI--ApiKey | OpenAI API authentication | Yes |
| AzureOpenAI--Endpoint | OpenAI service URL | No |
| AzureOpenAI--DeploymentName | Model deployment name | No |
| AzureOpenAI--ApiVersion | API version string | No |
| SqlServer--ConnectionString | Full SQL connection string | Yes |
| SqlServer--AdminPassword | SQL admin password | Yes |
| AppInsights--ConnectionString | Telemetry endpoint | No |

## Related

- ADR 0001: Azure Government Cloud Selection
- [Azure Key Vault Documentation](https://docs.microsoft.com/azure/key-vault/)
