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
// sqlAdminPassword is passed via CLI: --parameters sqlAdminPassword='YourPassword'
param enablePublicAccess = false  // All backend services are private-only
param deployDevBox = true
param devBoxAdminUsername = 'testadmin'
param devBoxAdminPassword = 'Password1!'
