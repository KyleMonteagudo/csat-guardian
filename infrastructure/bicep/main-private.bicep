// =============================================================================
// CSAT Guardian - Main Infrastructure Template (Private Networking)
// =============================================================================
// This Bicep template deploys a fully private Azure infrastructure for
// CSAT Guardian in Azure Government.
//
// Architecture:
// - VNet with subnets for App Service VNet integration and Private Endpoints
// - Private DNS Zones for SQL, Key Vault, and Azure OpenAI
// - Private Endpoints for all backend services
// - App Service with VNet integration (outbound through VNet)
// - Azure OpenAI with GPT-4o deployment
//
// All Azure-to-Azure communication is private (no public internet).
// The only public endpoint is the App Service frontend (for POC).
//
// Usage:
//   az cloud set --name AzureUSGovernment
//   az deployment group create \
//     --resource-group rg-csatguardian-dev \
//     --template-file main-private.bicep \
//     --parameters main-private.bicepparam
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

@description('Enable public network access during initial deployment (set to false after testing)')
param enablePublicAccess bool = true

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

// Naming convention: {resourceType}-{baseName}-{environment}
var keyVaultName = 'kv-${baseName}-${environment}'
var sqlServerName = 'sql-${baseName}-${environment}'
var sqlDatabaseName = 'sqldb-${baseName}-${environment}'
var appInsightsName = 'appi-${baseName}-${environment}'

// Tags applied to all resources
var commonTags = {
  Application: 'CSAT Guardian'
  Environment: environment
  ManagedBy: 'Bicep'
  CostCenter: 'CSS-Escalations'
  Cloud: 'AzureUSGovernment'
  NetworkMode: 'Private'
}

// -----------------------------------------------------------------------------
// Existing Resources (deployed previously)
// -----------------------------------------------------------------------------

// Reference existing Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Reference existing SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' existing = {
  name: sqlServerName
}

// -----------------------------------------------------------------------------
// Module: Networking (VNet + Subnets)
// -----------------------------------------------------------------------------

module networking 'modules/networking.bicep' = {
  name: 'networking-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: commonTags
  }
}

// -----------------------------------------------------------------------------
// Module: Private DNS Zones
// -----------------------------------------------------------------------------

module privateDns 'modules/private-dns.bicep' = {
  name: 'private-dns-deployment'
  params: {
    tags: commonTags
    vnetId: networking.outputs.vnetId
    vnetName: networking.outputs.vnetName
  }
}

// -----------------------------------------------------------------------------
// Module: Azure OpenAI
// -----------------------------------------------------------------------------

module openAI 'modules/openai.bicep' = {
  name: 'openai-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: commonTags
    publicNetworkAccess: enablePublicAccess
  }
}

// -----------------------------------------------------------------------------
// Module: Private Endpoints
// -----------------------------------------------------------------------------

module privateEndpoints 'modules/private-endpoints.bicep' = {
  name: 'private-endpoints-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: commonTags
    privateEndpointsSubnetId: networking.outputs.privateEndpointsSubnetId
    sqlServerId: sqlServer.id
    keyVaultId: keyVault.id
    openAIId: openAI.outputs.openAIId
    sqlPrivateDnsZoneId: privateDns.outputs.sqlPrivateDnsZoneId
    keyVaultPrivateDnsZoneId: privateDns.outputs.keyVaultPrivateDnsZoneId
    openAIPrivateDnsZoneId: privateDns.outputs.openAIPrivateDnsZoneId
  }
}

// -----------------------------------------------------------------------------
// Module: App Service
// -----------------------------------------------------------------------------

module appService 'modules/appservice.bicep' = {
  name: 'appservice-deployment'
  params: {
    environment: environment
    location: location
    baseName: baseName
    tags: commonTags
    appServiceSubnetId: networking.outputs.appServiceSubnetId
    keyVaultUri: keyVault.properties.vaultUri
    appInsightsConnectionString: appInsights.properties.ConnectionString
    openAIEndpoint: openAI.outputs.openAIEndpoint
    openAIDeploymentName: openAI.outputs.gpt4oDeploymentName
    sqlServerFqdn: sqlServer.properties.fullyQualifiedDomainName
    sqlDatabaseName: sqlDatabaseName
  }
}

// -----------------------------------------------------------------------------
// RBAC: Grant App Service access to Key Vault
// -----------------------------------------------------------------------------

// Key Vault Secrets User role - use deterministic GUID based on resource names
resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, keyVaultName, 'app-${baseName}-${environment}', 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appService.outputs.appServicePrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// RBAC: Grant App Service access to Azure OpenAI
// -----------------------------------------------------------------------------

// Cognitive Services OpenAI User role
resource openAIUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'oai-${baseName}-${environment}', 'app-${baseName}-${environment}', 'Cognitive Services OpenAI User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: appService.outputs.appServicePrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// Store new secrets in Key Vault
// -----------------------------------------------------------------------------

// Azure OpenAI API Key
resource openAIKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AzureOpenAI--ApiKey'
  properties: {
    value: openAI.outputs.openAIKey
  }
}

// Azure OpenAI Endpoint
resource openAIEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AzureOpenAI--Endpoint'
  properties: {
    value: openAI.outputs.openAIEndpoint
  }
}

// Azure OpenAI Deployment Name
resource openAIDeploymentSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AzureOpenAI--DeploymentName'
  properties: {
    value: openAI.outputs.gpt4oDeploymentName
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('VNet resource ID')
output vnetId string = networking.outputs.vnetId

@description('Azure OpenAI endpoint')
output openAIEndpoint string = openAI.outputs.openAIEndpoint

@description('Azure OpenAI deployment name')
output openAIDeploymentName string = openAI.outputs.gpt4oDeploymentName

@description('App Service URL')
output appServiceUrl string = appService.outputs.appServiceUrl

@description('App Service hostname')
output appServiceHostname string = appService.outputs.appServiceHostname

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('SQL Server FQDN')
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName

@description('Private Endpoints deployed')
output privateEndpointsDeployed object = {
  sql: privateEndpoints.outputs.sqlPrivateEndpointIp
  keyVault: privateEndpoints.outputs.keyVaultPrivateEndpointIp
  openAI: privateEndpoints.outputs.openAIPrivateEndpointIp
}
