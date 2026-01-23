// =============================================================================
// CSAT Guardian - Azure OpenAI Module
// =============================================================================
// Creates Azure OpenAI (Cognitive Services) with:
// - GPT-4o deployment for sentiment analysis and chat
// - Prepared for private endpoint connectivity
//
// NOTE: Azure OpenAI in Azure Government has limited region availability
// =============================================================================

@description('Environment name')
param environment string

@description('Azure region')
param location string

@description('Base name for resources')
param baseName string

@description('Common tags for all resources')
param tags object

@description('Enable public network access (set to false after private endpoint is configured)')
param publicNetworkAccess bool = true

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

var openAIName = 'oai-${baseName}-${environment}'

// -----------------------------------------------------------------------------
// Azure OpenAI (Cognitive Services Account)
// -----------------------------------------------------------------------------

resource openAI 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAIName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: publicNetworkAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      defaultAction: publicNetworkAccess ? 'Allow' : 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    // Disable local authentication when using Managed Identity (recommended for prod)
    // disableLocalAuth: true  // Uncomment for production
  }
}

// -----------------------------------------------------------------------------
// GPT-4o Deployment
// -----------------------------------------------------------------------------

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAI
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 10  // Tokens per minute (TPM) in thousands
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'  // Latest available in Azure Government
    }
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('Azure OpenAI resource ID')
output openAIId string = openAI.id

@description('Azure OpenAI resource name')
output openAIName string = openAI.name

@description('Azure OpenAI endpoint')
output openAIEndpoint string = openAI.properties.endpoint

@description('Azure OpenAI API key (primary)')
@secure()
output openAIKey string = openAI.listKeys().key1

@description('GPT-4o deployment name')
output gpt4oDeploymentName string = gpt4oDeployment.name
