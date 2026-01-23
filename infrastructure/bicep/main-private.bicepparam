// =============================================================================
// CSAT Guardian - Deployment Parameters (Private Networking)
// =============================================================================
// Parameter values for deploying the private networking infrastructure.
//
// Usage:
//   az cloud set --name AzureUSGovernment
//   az deployment group create \
//     --resource-group rg-csatguardian-dev \
//     --template-file main-private.bicep \
//     --parameters main-private.bicepparam
// =============================================================================

using 'main-private.bicep'

// Environment settings
param environment = 'dev'
param location = 'usgovvirginia'
param baseName = 'csatguardian'

// Initial deployment allows public access for testing
// Set to false after verifying private connectivity works
param enablePublicAccess = true
