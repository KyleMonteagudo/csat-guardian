// =============================================================================
// CSAT Guardian - Parameters for Commercial Azure Deployment
// =============================================================================
// Target: Commercial Azure (Central US)
// Resource Group: KMonteagudo_CSAT_Guardian (in eastus - that's fine)
// Subscription: a20d761d-cb36-4f83-b827-58ccdb166f39
// =============================================================================

using 'main-commercial.bicep'

param environment = 'dev'
param location = 'centralus'
param baseName = 'csatguardian'
param sqlAdminUsername = 'sqladmin'
param sqlAdminPassword = 'YourSecureP@ssword123!'  // TODO: Use Key Vault or CLI param in production
param enablePublicAccess = false  // All backend services are private-only
param deployDevBox = true
param devBoxAdminUsername = 'testadmin'
param devBoxAdminPassword = 'Password1!'
