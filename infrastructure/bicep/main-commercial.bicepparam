// =============================================================================
// CSAT Guardian - Parameters for Commercial Azure Deployment
// =============================================================================
// Target: Commercial Azure (EastUS)
// Resource Group: KMonteagudo_CSAT_Guardian
// Subscription: a20d761d-cb36-4f83-b827-58ccdb166f39
// =============================================================================

using 'main-commercial.bicep'

param environment = 'dev'
param location = 'eastus'
param baseName = 'csatguardian'
param sqlAdminUsername = 'sqladmin'
param sqlAdminPassword = readEnvironmentVariable('SQL_ADMIN_PASSWORD', '')
param enablePublicAccess = false  // All backend services are private-only
param deployDevBox = true
param devBoxAdminUsername = 'testadmin'
param devBoxAdminPassword = 'Password1!'

// Note: Set SQL_ADMIN_PASSWORD environment variable before deployment, or override via CLI:
// az deployment group create ... --parameters sqlAdminPassword='YourSecurePassword123!'
