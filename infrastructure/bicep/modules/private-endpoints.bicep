// =============================================================================
// CSAT Guardian - Private Endpoints Module
// =============================================================================
// Creates Private Endpoints for:
// - Azure SQL Server
// - Azure Key Vault
// - Azure OpenAI
//
// Each private endpoint is linked to the appropriate Private DNS Zone
// for automatic DNS resolution within the VNet.
// =============================================================================

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Base name for resources')
param baseName string

@description('Common tags for all resources')
param tags object

@description('Subnet ID for private endpoints')
param privateEndpointsSubnetId string

// Resource IDs for services to create private endpoints for
@description('SQL Server resource ID')
param sqlServerId string

@description('Key Vault resource ID')
param keyVaultId string

@description('Azure OpenAI resource ID')
param openAIId string

// Private DNS Zone IDs for DNS record creation
@description('SQL Private DNS Zone ID')
param sqlPrivateDnsZoneId string

@description('Key Vault Private DNS Zone ID')
param keyVaultPrivateDnsZoneId string

@description('OpenAI Private DNS Zone ID')
param openAIPrivateDnsZoneId string

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

var privateEndpointPrefix = 'pep-${baseName}-${environment}'

// -----------------------------------------------------------------------------
// SQL Server Private Endpoint
// -----------------------------------------------------------------------------

resource sqlPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${privateEndpointPrefix}-sql'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointPrefix}-sql-connection'
        properties: {
          privateLinkServiceId: sqlServerId
          groupIds: [
            'sqlServer'
          ]
        }
      }
    ]
  }
}

resource sqlPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: sqlPrivateEndpoint
  name: 'sqlPrivateDnsZoneGroup'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sql-config'
        properties: {
          privateDnsZoneId: sqlPrivateDnsZoneId
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Key Vault Private Endpoint
// -----------------------------------------------------------------------------

resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${privateEndpointPrefix}-kv'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointPrefix}-kv-connection'
        properties: {
          privateLinkServiceId: keyVaultId
          groupIds: [
            'vault'
          ]
        }
      }
    ]
  }
}

resource keyVaultPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: keyVaultPrivateEndpoint
  name: 'keyVaultPrivateDnsZoneGroup'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'keyvault-config'
        properties: {
          privateDnsZoneId: keyVaultPrivateDnsZoneId
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Azure OpenAI Private Endpoint
// -----------------------------------------------------------------------------

resource openAIPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: '${privateEndpointPrefix}-oai'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointsSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointPrefix}-oai-connection'
        properties: {
          privateLinkServiceId: openAIId
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource openAIPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: openAIPrivateEndpoint
  name: 'openAIPrivateDnsZoneGroup'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'openai-config'
        properties: {
          privateDnsZoneId: openAIPrivateDnsZoneId
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('SQL Private Endpoint ID')
output sqlPrivateEndpointId string = sqlPrivateEndpoint.id

@description('Key Vault Private Endpoint ID')
output keyVaultPrivateEndpointId string = keyVaultPrivateEndpoint.id

@description('OpenAI Private Endpoint ID')
output openAIPrivateEndpointId string = openAIPrivateEndpoint.id

@description('SQL Private Endpoint IP address')
output sqlPrivateEndpointIp string = sqlPrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]

@description('Key Vault Private Endpoint IP address')
output keyVaultPrivateEndpointIp string = keyVaultPrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]

@description('OpenAI Private Endpoint IP address')
output openAIPrivateEndpointIp string = openAIPrivateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
