// =============================================================================
// CSAT Guardian - Networking Module
// =============================================================================
// Creates VNet with subnets for:
// - App Service VNet Integration
// - Private Endpoints
// =============================================================================

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Base name for resources')
param baseName string

@description('Common tags for all resources')
param tags object

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

var vnetName = 'vnet-${baseName}-${environment}'
var vnetAddressPrefix = '10.100.0.0/16'

// Subnet definitions
var subnets = {
  appService: {
    name: 'snet-appservice'
    addressPrefix: '10.100.1.0/24'
    // App Service VNet integration requires delegation
    delegations: [
      {
        name: 'appservice-delegation'
        properties: {
          serviceName: 'Microsoft.Web/serverFarms'
        }
      }
    ]
    serviceEndpoints: []
    privateEndpointNetworkPolicies: 'Enabled'
  }
  privateEndpoints: {
    name: 'snet-privateendpoints'
    addressPrefix: '10.100.2.0/24'
    delegations: []
    serviceEndpoints: []
    // Must be disabled for private endpoints
    privateEndpointNetworkPolicies: 'Disabled'
  }
}

// -----------------------------------------------------------------------------
// Virtual Network
// -----------------------------------------------------------------------------

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: subnets.appService.name
        properties: {
          addressPrefix: subnets.appService.addressPrefix
          delegations: subnets.appService.delegations
          serviceEndpoints: subnets.appService.serviceEndpoints
          privateEndpointNetworkPolicies: subnets.appService.privateEndpointNetworkPolicies
        }
      }
      {
        name: subnets.privateEndpoints.name
        properties: {
          addressPrefix: subnets.privateEndpoints.addressPrefix
          delegations: subnets.privateEndpoints.delegations
          serviceEndpoints: subnets.privateEndpoints.serviceEndpoints
          privateEndpointNetworkPolicies: subnets.privateEndpoints.privateEndpointNetworkPolicies
        }
      }
    ]
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('VNet resource ID')
output vnetId string = vnet.id

@description('VNet name')
output vnetName string = vnet.name

@description('App Service subnet resource ID')
output appServiceSubnetId string = vnet.properties.subnets[0].id

@description('Private Endpoints subnet resource ID')
output privateEndpointsSubnetId string = vnet.properties.subnets[1].id

@description('App Service subnet name')
output appServiceSubnetName string = subnets.appService.name

@description('Private Endpoints subnet name')
output privateEndpointsSubnetName string = subnets.privateEndpoints.name
