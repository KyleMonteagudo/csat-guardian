// =============================================================================
// CSAT Guardian - App Service Module
// =============================================================================
// Creates Azure App Service with:
// - Linux Python runtime for Streamlit
// - VNet integration for private connectivity
// - System-assigned Managed Identity
//
// This is the POC web frontend until Teams bot integration is complete.
// =============================================================================

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Base name for resources')
param baseName string

@description('Common tags for all resources')
param tags object

@description('Subnet ID for VNet integration')
param appServiceSubnetId string

@description('Key Vault URI for secrets')
param keyVaultUri string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('Azure OpenAI endpoint')
param openAIEndpoint string

@description('Azure OpenAI deployment name')
param openAIDeploymentName string

@description('SQL Server FQDN')
param sqlServerFqdn string

@description('SQL Database name')
param sqlDatabaseName string

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

var appServicePlanName = 'asp-${baseName}-${environment}'
var appServiceName = 'app-${baseName}-${environment}'

// -----------------------------------------------------------------------------
// App Service Plan (Linux)
// -----------------------------------------------------------------------------

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: 'B1'  // Basic tier - supports VNet integration
    tier: 'Basic'
    capacity: 1
  }
  properties: {
    reserved: true  // Required for Linux
  }
}

// -----------------------------------------------------------------------------
// App Service (Web App)
// -----------------------------------------------------------------------------

resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: appServiceName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    virtualNetworkSubnetId: appServiceSubnetId
    vnetRouteAllEnabled: true  // Route all outbound traffic through VNet
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: false  // Set to true in production
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      // Streamlit startup command
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true'
      appSettings: [
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
          value: keyVaultUri
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAIEndpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: openAIDeploymentName
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-08-01-preview'
        }
        {
          name: 'SQL_SERVER'
          value: sqlServerFqdn
        }
        {
          name: 'SQL_DATABASE'
          value: sqlDatabaseName
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        // SCM (deployment) settings
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
      ]
    }
  }
}

// -----------------------------------------------------------------------------
// VNet Integration
// -----------------------------------------------------------------------------

resource vnetIntegration 'Microsoft.Web/sites/virtualNetworkConnections@2023-12-01' = {
  parent: appService
  name: 'vnet-integration'
  properties: {
    vnetResourceId: appServiceSubnetId
    isSwift: true
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('App Service resource ID')
output appServiceId string = appService.id

@description('App Service name')
output appServiceName string = appService.name

@description('App Service default hostname')
output appServiceHostname string = appService.properties.defaultHostName

@description('App Service URL')
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'

@description('App Service Managed Identity Principal ID')
output appServicePrincipalId string = appService.identity.principalId

@description('App Service Plan ID')
output appServicePlanId string = appServicePlan.id
