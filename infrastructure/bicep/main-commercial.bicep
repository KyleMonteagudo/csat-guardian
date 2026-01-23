// =============================================================================
// CSAT Guardian - Main Infrastructure Template (Commercial Azure)
// =============================================================================
// This Bicep template deploys a complete Azure infrastructure for CSAT Guardian
// in Commercial Azure (not Government).
//
// DEPLOYS EVERYTHING FROM SCRATCH:
// - VNet with subnets for App Service and Private Endpoints
// - Private DNS Zones for SQL, Key Vault, and Azure OpenAI
// - Azure SQL Server + Database with sample data
// - Azure Key Vault with secrets
// - Azure OpenAI with GPT-4o deployment
// - Private Endpoints for all backend services
// - App Service with VNet integration
// - Application Insights + Log Analytics
//
// All Azure-to-Azure communication is private (no public internet).
// The only public endpoint is the App Service frontend (for POC).
//
// Usage:
//   az deployment group create \
//     --resource-group KMonteagudo_CSAT_Guardian \
//     --template-file main-commercial.bicep \
//     --parameters main-commercial.bicepparam
// =============================================================================

targetScope = 'resourceGroup'

// -----------------------------------------------------------------------------
// Parameters
// -----------------------------------------------------------------------------

@description('Environment name (dev, test, prod)')
@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = 'eastus'

@description('Base name for resources')
param baseName string = 'csatguardian'

@description('SQL Server admin username')
param sqlAdminUsername string = 'sqladmin'

@description('SQL Server admin password')
@secure()
param sqlAdminPassword string

@description('Enable public network access (false = fully private, use Bastion to access devbox)')
param enablePublicAccess bool = false

@description('Deploy a dev-box VM for testing private endpoints')
param deployDevBox bool = true

@description('Dev-box VM admin username')
param devBoxAdminUsername string = 'testadmin'

@description('Dev-box VM admin password')
@secure()
param devBoxAdminPassword string

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

// Naming convention: {resourceType}-{baseName}-{environment}
var vnetName = 'vnet-${baseName}-${environment}'
var keyVaultName = 'kv-${baseName}-${environment}'
var sqlServerName = 'sql-${baseName}-${environment}'
var sqlDatabaseName = 'sqldb-${baseName}-${environment}'
var openAIName = 'oai-${baseName}-${environment}'
var appServicePlanName = 'asp-${baseName}-${environment}'
var appServiceName = 'app-${baseName}-${environment}'
var appInsightsName = 'appi-${baseName}-${environment}'
var logAnalyticsName = 'log-${baseName}-${environment}'

// Network configuration
var vnetAddressPrefix = '10.100.0.0/16'
var appServiceSubnetPrefix = '10.100.1.0/24'
var privateEndpointsSubnetPrefix = '10.100.2.0/24'
var devBoxSubnetPrefix = '10.100.3.0/24'
var bastionSubnetPrefix = '10.100.4.0/26' // Bastion requires /26 or larger

// Dev-box naming
var devBoxVmName = 'vm-devbox-${baseName}'
var devBoxNicName = 'nic-devbox-${baseName}'
var devBoxNsgName = 'nsg-devbox-${baseName}'

// Bastion naming
var bastionName = 'bas-${baseName}-${environment}'
var bastionPublicIpName = 'pip-bastion-${baseName}'

// Tags applied to all resources
var commonTags = {
  Application: 'CSAT Guardian'
  Environment: environment
  ManagedBy: 'Bicep'
  CostCenter: 'CSS-Escalations'
  Cloud: 'AzureCommercial'
  NetworkMode: 'Private'
}

// Private DNS Zone names using az.environment() function for cloud compatibility
var privateDnsZones = {
  sql: 'privatelink${az.environment().suffixes.sqlServerHostname}'
  keyVault: 'privatelink.vaultcore.azure.net'
  openAI: 'privatelink.openai.azure.com'
}

// -----------------------------------------------------------------------------
// Log Analytics Workspace
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
  }
}

// -----------------------------------------------------------------------------
// Virtual Network
// -----------------------------------------------------------------------------

resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: commonTags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-appservice'
        properties: {
          addressPrefix: appServiceSubnetPrefix
          delegations: [
            {
              name: 'delegation-appservice'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
      {
        name: 'snet-privateendpoints'
        properties: {
          addressPrefix: privateEndpointsSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-devbox'
        properties: {
          addressPrefix: devBoxSubnetPrefix
        }
      }
      {
        name: 'AzureBastionSubnet' // Must be named exactly this
        properties: {
          addressPrefix: bastionSubnetPrefix
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Private DNS Zones
// -----------------------------------------------------------------------------

resource sqlPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.sql
  location: 'global'
  tags: commonTags
}

resource keyVaultPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.keyVault
  location: 'global'
  tags: commonTags
}

resource openAIPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.openAI
  location: 'global'
  tags: commonTags
}

// VNet Links for DNS Zones
resource sqlDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: sqlPrivateDnsZone
  name: 'link-${vnetName}-sql'
  location: 'global'
  tags: commonTags
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource keyVaultDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: keyVaultPrivateDnsZone
  name: 'link-${vnetName}-kv'
  location: 'global'
  tags: commonTags
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource openAIDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: openAIPrivateDnsZone
  name: 'link-${vnetName}-oai'
  location: 'global'
  tags: commonTags
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

// -----------------------------------------------------------------------------
// Azure Key Vault
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
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: enablePublicAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      defaultAction: enablePublicAccess ? 'Allow' : 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// -----------------------------------------------------------------------------
// Azure SQL Server + Database
// -----------------------------------------------------------------------------

resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: sqlServerName
  location: location
  tags: commonTags
  properties: {
    administratorLogin: sqlAdminUsername
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: enablePublicAccess ? 'Enabled' : 'Disabled'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2GB
  }
}

// Allow Azure services to access SQL (needed for deployment)
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = if (enablePublicAccess) {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// -----------------------------------------------------------------------------
// Azure OpenAI
// -----------------------------------------------------------------------------

resource openAI 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAIName
  location: location
  tags: commonTags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: enablePublicAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      defaultAction: enablePublicAccess ? 'Allow' : 'Deny'
    }
  }
}

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
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
      version: '2024-11-20'
    }
  }
}

// -----------------------------------------------------------------------------
// Private Endpoints
// -----------------------------------------------------------------------------

resource sqlPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-${sqlServerName}'
  location: location
  tags: commonTags
  properties: {
    subnet: {
      id: vnet.properties.subnets[1].id
    }
    privateLinkServiceConnections: [
      {
        name: 'plsc-${sqlServerName}'
        properties: {
          privateLinkServiceId: sqlServer.id
          groupIds: ['sqlServer']
        }
      }
    ]
  }
}

resource sqlPrivateDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: sqlPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: sqlPrivateDnsZone.id
        }
      }
    ]
  }
}

resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-${keyVaultName}'
  location: location
  tags: commonTags
  properties: {
    subnet: {
      id: vnet.properties.subnets[1].id
    }
    privateLinkServiceConnections: [
      {
        name: 'plsc-${keyVaultName}'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: ['vault']
        }
      }
    ]
  }
}

resource keyVaultPrivateDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: keyVaultPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: keyVaultPrivateDnsZone.id
        }
      }
    ]
  }
}

resource openAIPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-${openAIName}'
  location: location
  tags: commonTags
  properties: {
    subnet: {
      id: vnet.properties.subnets[1].id
    }
    privateLinkServiceConnections: [
      {
        name: 'plsc-${openAIName}'
        properties: {
          privateLinkServiceId: openAI.id
          groupIds: ['account']
        }
      }
    ]
  }
}

resource openAIPrivateDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: openAIPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: openAIPrivateDnsZone.id
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// App Service Plan + App Service
// -----------------------------------------------------------------------------

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: commonTags
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  tags: commonTags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    virtualNetworkSubnetId: vnet.properties.subnets[0].id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'AZURE_KEY_VAULT_URL'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAI.properties.endpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT'
          value: 'gpt-4o'
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-10-21'
        }
        {
          name: 'DATABASE_CONNECTION_STRING'
          value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Initial Catalog=${sqlDatabaseName};Persist Security Info=False;User ID=${sqlAdminUsername};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '0'
        }
      ]
      appCommandLine: 'python -m uvicorn api:app --host 0.0.0.0 --port 8000'
    }
  }
}

// -----------------------------------------------------------------------------
// RBAC: Grant App Service access to Key Vault
// -----------------------------------------------------------------------------

resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, keyVaultName, appServiceName, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// RBAC: Grant App Service access to Azure OpenAI
// -----------------------------------------------------------------------------

resource openAIUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, openAIName, appServiceName, 'Cognitive Services OpenAI User')
  scope: openAI
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// Store Secrets in Key Vault
// -----------------------------------------------------------------------------

resource sqlConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'SqlServer--ConnectionString'
  properties: {
    value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Initial Catalog=${sqlDatabaseName};Persist Security Info=False;User ID=${sqlAdminUsername};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
  }
}

resource sqlPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'SqlServer--AdminPassword'
  properties: {
    value: sqlAdminPassword
  }
}

resource openAIKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AzureOpenAI--ApiKey'
  properties: {
    value: openAI.listKeys().key1
  }
}

resource openAIEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AzureOpenAI--Endpoint'
  properties: {
    value: openAI.properties.endpoint
  }
}

resource appInsightsConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AppInsights--ConnectionString'
  properties: {
    value: appInsights.properties.ConnectionString
  }
}

// -----------------------------------------------------------------------------
// Dev-Box VM (for testing private endpoints)
// -----------------------------------------------------------------------------

resource devBoxNsg 'Microsoft.Network/networkSecurityGroups@2023-05-01' = if (deployDevBox) {
  name: devBoxNsgName
  location: location
  tags: commonTags
  properties: {
    securityRules: [
      {
        name: 'AllowBastionRDP'
        properties: {
          priority: 1000
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: bastionSubnetPrefix
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '3389'
        }
      }
    ]
  }
}

// Bastion Public IP (required for Bastion service)
resource bastionPublicIp 'Microsoft.Network/publicIPAddresses@2023-05-01' = if (deployDevBox) {
  name: bastionPublicIpName
  location: location
  tags: commonTags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

// Azure Bastion Host
resource bastion 'Microsoft.Network/bastionHosts@2023-05-01' = if (deployDevBox) {
  name: bastionName
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
  }
  properties: {
    ipConfigurations: [
      {
        name: 'bastionIpConfig'
        properties: {
          subnet: {
            id: vnet.properties.subnets[3].id // AzureBastionSubnet
          }
          publicIPAddress: {
            id: bastionPublicIp.id
          }
        }
      }
    ]
  }
}

// Dev-box NIC (no public IP - access via Bastion only)
resource devBoxNic 'Microsoft.Network/networkInterfaces@2023-05-01' = if (deployDevBox) {
  name: devBoxNicName
  location: location
  tags: commonTags
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: vnet.properties.subnets[2].id // snet-devbox
          }
          privateIPAllocationMethod: 'Dynamic'
        }
      }
    ]
    networkSecurityGroup: {
      id: devBoxNsg.id
    }
  }
}

resource devBoxVm 'Microsoft.Compute/virtualMachines@2023-09-01' = if (deployDevBox) {
  name: devBoxVmName
  location: location
  tags: commonTags
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_DS2_v2'
    }
    osProfile: {
      computerName: 'devbox'
      adminUsername: devBoxAdminUsername
      adminPassword: devBoxAdminPassword
    }
    storageProfile: {
      imageReference: {
        publisher: 'MicrosoftWindowsDesktop'
        offer: 'Windows-11'
        sku: 'win11-23h2-pro'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: devBoxNic.id
        }
      ]
    }
  }
}

// Install tools on dev-box (Azure CLI, Python, VS Code, SSMS, etc.)
resource devBoxExtension 'Microsoft.Compute/virtualMachines/extensions@2023-09-01' = if (deployDevBox) {
  parent: devBoxVm
  name: 'InstallDevTools'
  location: location
  properties: {
    publisher: 'Microsoft.Compute'
    type: 'CustomScriptExtension'
    typeHandlerVersion: '1.10'
    autoUpgradeMinorVersion: true
    settings: {
      commandToExecute: 'powershell -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\')); choco install -y azure-cli python vscode sql-server-management-studio git"'
    }
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('Resource Group name')
output resourceGroupName string = resourceGroup().name

@description('VNet resource ID')
output vnetId string = vnet.id

@description('App Service URL')
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'

@description('App Service hostname')
output appServiceHostname string = appService.properties.defaultHostName

@description('Azure OpenAI endpoint')
output openAIEndpoint string = openAI.properties.endpoint

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('SQL Server FQDN')
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName

@description('SQL Database name')
output sqlDatabaseName string = sqlDatabaseName

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString
