// =============================================================================
// CSAT Guardian - Azure Government Infrastructure
// =============================================================================
// This Bicep template deploys all Azure resources required for CSAT Guardian.
//
// IMPORTANT: This template is designed for AZURE GOVERNMENT cloud.
// - Use USGov Virginia or USGov Arizona regions
// - Some services have different availability than Commercial cloud
// - Endpoints use .us domains (e.g., .vault.usgovcloudapi.net)
//
// Resources deployed:
// - Key Vault (secrets management)
// - Azure SQL Database (sample data / analytics)
// - Container Registry (Docker images)
// - Container Apps Environment + App (application hosting)
// - Application Insights (monitoring)
// - Azure OpenAI (sentiment analysis) - optional, can use existing
//
// Usage:
//   az cloud set --name AzureUSGovernment
//   az deployment group create \
//     --resource-group rg-csat-guardian-dev \
//     --template-file main.bicep \
//     --parameters environment=dev
// =============================================================================

// -----------------------------------------------------------------------------
// Parameters
// -----------------------------------------------------------------------------

@description('Environment name (dev, test, prod)')
@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'

@description('Azure region for resources (Azure Government regions)')
@allowed(['usgovvirginia', 'usgovarizona', 'usgovtexas'])
param location string = 'usgovvirginia'

@description('Base name for resources')
param baseName string = 'csatguardian'

@description('SQL Administrator login')
param sqlAdminLogin string = 'sqladmin'

@description('SQL Administrator password')
@secure()
param sqlAdminPassword string

@description('Deploy Azure OpenAI? Set to false if using existing instance')
param deployOpenAI bool = false

@description('Existing Azure OpenAI endpoint (if not deploying new)')
param existingOpenAIEndpoint string = ''

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

// Naming convention: {resourceType}-{baseName}-{environment}
var keyVaultName = 'kv-${baseName}-${environment}'
var sqlServerName = 'sql-${baseName}-${environment}'
var sqlDatabaseName = 'sqldb-${baseName}-${environment}'
var containerRegistryName = 'acr${baseName}${environment}'  // No hyphens allowed
var containerAppsEnvName = 'cae-${baseName}-${environment}'
var containerAppName = 'ca-${baseName}-${environment}'
var appInsightsName = 'appi-${baseName}-${environment}'
var logAnalyticsName = 'log-${baseName}-${environment}'
var openAIName = 'oai-${baseName}-${environment}'

// Tags applied to all resources
var commonTags = {
  Application: 'CSAT Guardian'
  Environment: environment
  ManagedBy: 'Bicep'
  CostCenter: 'CSS-Escalations'
  Cloud: 'AzureUSGovernment'
}

// -----------------------------------------------------------------------------
// Log Analytics Workspace (required for Container Apps and App Insights)
// -----------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// -----------------------------------------------------------------------------
// Application Insights
// -----------------------------------------------------------------------------

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// -----------------------------------------------------------------------------
// Key Vault
// -----------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    // Enable RBAC for access control (recommended over access policies)
    enableRbacAuthorization: true
    // Soft delete for recovery
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    // Note: Not setting enablePurgeProtection - defaults to false for dev
    // For prod, uncomment: enablePurgeProtection: true
  }
}

// -----------------------------------------------------------------------------
// Azure SQL Server and Database
// -----------------------------------------------------------------------------

resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: sqlServerName
  location: location
  tags: commonTags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'  // For POC; disable in prod
  }
}

// Allow Azure services to access SQL (for Container Apps)
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// The actual database (child resource of SQL Server)
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  name: sqlDatabaseName
  location: location
  tags: commonTags
  parent: sqlServer
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648  // 2 GB
  }
}

// -----------------------------------------------------------------------------
// Container Registry
// -----------------------------------------------------------------------------

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true  // Enable for simplicity in POC; use managed identity in prod
  }
}

// -----------------------------------------------------------------------------
// Container Apps Environment (Workload Profile - required for Azure Government)
// -----------------------------------------------------------------------------

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppsEnvName
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Container App (CSAT Guardian API)
// -----------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'csat-guardian-api'
          // Placeholder image - will be updated by CI/CD
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'AZURE_CLOUD'
              value: 'AzureUSGovernment'
            }
            {
              name: 'AZURE_AUTHORITY_HOST'
              value: 'https://login.microsoftonline.us'
            }
            {
              name: 'AZURE_KEY_VAULT_URL'
              value: keyVault.properties.vaultUri
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 1 : 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// -----------------------------------------------------------------------------
// Azure OpenAI (Optional)
// -----------------------------------------------------------------------------

resource openAI 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = if (deployOpenAI) {
  name: openAIName
  location: location
  tags: commonTags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: 'Enabled'
  }
}

// GPT-4o deployment (only if deploying OpenAI)
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = if (deployOpenAI) {
  parent: openAI
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
  }
}

// -----------------------------------------------------------------------------
// RBAC Assignments
// -----------------------------------------------------------------------------

// Grant Container App's managed identity access to Key Vault
resource keyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')  // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// Store secrets in Key Vault
// -----------------------------------------------------------------------------

// SQL connection string
resource sqlConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'SqlServer--ConnectionString'
  properties: {
    value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Initial Catalog=${sqlDatabaseName};Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
  }
}

// App Insights connection string
resource appInsightsSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AppInsights--ConnectionString'
  properties: {
    value: appInsights.properties.ConnectionString
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('SQL Server fully qualified domain name')
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName

@description('SQL Database name')
output sqlDatabaseName string = sqlDatabaseName

@description('Container Registry login server')
output containerRegistryLoginServer string = containerRegistry.properties.loginServer

@description('Container App URL')
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString

@description('Azure OpenAI endpoint (if deployed)')
output openAIEndpoint string = deployOpenAI ? openAI!.properties.endpoint : existingOpenAIEndpoint
