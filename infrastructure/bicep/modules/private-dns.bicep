// =============================================================================
// CSAT Guardian - Private DNS Zones Module
// =============================================================================
// Creates Private DNS Zones for:
// - Azure SQL Database (privatelink.database.usgovcloudapi.net)
// - Azure Key Vault (privatelink.vaultcore.usgovcloudapi.net)
// - Azure OpenAI (privatelink.openai.azure.us)
//
// NOTE: These are Azure Government endpoints (.us and .usgovcloudapi.net)
// =============================================================================

@description('Azure region')
param location string = 'global'  // DNS zones are global resources

@description('Common tags for all resources')
param tags object

@description('VNet resource ID to link DNS zones to')
param vnetId string

@description('VNet name for link naming')
param vnetName string

// -----------------------------------------------------------------------------
// Private DNS Zone Names (Azure Government)
// -----------------------------------------------------------------------------

// Azure Government uses different DNS suffixes than Commercial
var privateDnsZones = {
  sql: 'privatelink.database.usgovcloudapi.net'
  keyVault: 'privatelink.vaultcore.usgovcloudapi.net'
  openAI: 'privatelink.openai.azure.us'
}

// -----------------------------------------------------------------------------
// Private DNS Zones
// -----------------------------------------------------------------------------

resource sqlPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.sql
  location: location
  tags: tags
  properties: {}
}

resource keyVaultPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.keyVault
  location: location
  tags: tags
  properties: {}
}

resource openAIPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZones.openAI
  location: location
  tags: tags
  properties: {}
}

// -----------------------------------------------------------------------------
// VNet Links - Link DNS zones to VNet for resolution
// -----------------------------------------------------------------------------

resource sqlDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: sqlPrivateDnsZone
  name: 'link-${vnetName}-sql'
  location: location
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false  // Auto-registration not needed for private endpoints
  }
}

resource keyVaultDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: keyVaultPrivateDnsZone
  name: 'link-${vnetName}-kv'
  location: location
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

resource openAIDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: openAIPrivateDnsZone
  name: 'link-${vnetName}-oai'
  location: location
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('SQL Private DNS Zone resource ID')
output sqlPrivateDnsZoneId string = sqlPrivateDnsZone.id

@description('Key Vault Private DNS Zone resource ID')
output keyVaultPrivateDnsZoneId string = keyVaultPrivateDnsZone.id

@description('OpenAI Private DNS Zone resource ID')
output openAIPrivateDnsZoneId string = openAIPrivateDnsZone.id

@description('SQL Private DNS Zone name')
output sqlPrivateDnsZoneName string = sqlPrivateDnsZone.name

@description('Key Vault Private DNS Zone name')
output keyVaultPrivateDnsZoneName string = keyVaultPrivateDnsZone.name

@description('OpenAI Private DNS Zone name')
output openAIPrivateDnsZoneName string = openAIPrivateDnsZone.name
