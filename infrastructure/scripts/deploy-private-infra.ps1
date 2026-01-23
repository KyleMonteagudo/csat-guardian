# =============================================================================
# CSAT Guardian - Private Infrastructure Deployment Script
# =============================================================================
# This script deploys the private networking infrastructure for CSAT Guardian.
#
# Prerequisites:
# - Azure CLI installed and logged in
# - Azure Government cloud selected
# - Existing resources: SQL Server, Key Vault, Log Analytics, App Insights
#
# Usage:
#   .\deploy-private-infra.ps1 -SqlAdminPassword "YourSecurePassword123!"
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [SecureString]$SqlAdminPassword,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-csatguardian-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "usgovvirginia",
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($Message) Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BicepDir = Split-Path -Parent $ScriptDir
$TemplateFile = Join-Path $BicepDir "bicep\main-private.bicep"
$ParametersFile = Join-Path $BicepDir "bicep\main-private.bicepparam"

Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  CSAT Guardian - Private Infrastructure" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# Verify Azure CLI and cloud
Write-Step "Verifying Azure configuration..."
$cloud = az cloud show --query name -o tsv
if ($cloud -ne "AzureUSGovernment") {
    Write-Warning "Current cloud is '$cloud'. Switching to AzureUSGovernment..."
    az cloud set --name AzureUSGovernment
}
Write-Success "Azure Government cloud selected"

# Verify logged in
$account = az account show --query "{name:name, id:id}" -o json | ConvertFrom-Json
Write-Success "Logged in as: $($account.name)"

# Verify resource group exists
Write-Step "Verifying resource group..."
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq "false") {
    Write-Error "Resource group '$ResourceGroup' does not exist!"
    exit 1
}
Write-Success "Resource group '$ResourceGroup' exists"

# Verify existing resources
Write-Step "Verifying existing resources..."
$existingResources = @(
    @{ type = "Microsoft.Sql/servers"; name = "sql-csatguardian-dev" },
    @{ type = "Microsoft.KeyVault/vaults"; name = "kv-csatguardian-dev" },
    @{ type = "Microsoft.OperationalInsights/workspaces"; name = "log-csatguardian-dev" },
    @{ type = "Microsoft.Insights/components"; name = "appi-csatguardian-dev" }
)

foreach ($resource in $existingResources) {
    $exists = az resource show --resource-group $ResourceGroup --resource-type $resource.type --name $resource.name --query "id" -o tsv 2>$null
    if (-not $exists) {
        Write-Error "Required resource '$($resource.name)' not found!"
        exit 1
    }
    Write-Success "Found: $($resource.name)"
}

# Convert SecureString to plain text for az cli
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SqlAdminPassword)
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Build deployment command
$deploymentName = "csatguardian-private-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Step "Deploying infrastructure..."
Write-Host "  Template: $TemplateFile"
Write-Host "  Parameters: $ParametersFile"
Write-Host "  Deployment: $deploymentName"

if ($WhatIf) {
    Write-Warning "WhatIf mode - validating template only..."
    az deployment group what-if `
        --resource-group $ResourceGroup `
        --template-file $TemplateFile `
        --parameters $ParametersFile `
        --parameters sqlAdminPassword=$PlainPassword
} else {
    $result = az deployment group create `
        --resource-group $ResourceGroup `
        --name $deploymentName `
        --template-file $TemplateFile `
        --parameters $ParametersFile `
        --parameters sqlAdminPassword=$PlainPassword `
        --query "{state:properties.provisioningState, outputs:properties.outputs}" `
        -o json | ConvertFrom-Json
    
    if ($result.state -eq "Succeeded") {
        Write-Success "Deployment completed successfully!"
        
        Write-Host "`n=============================================" -ForegroundColor Green
        Write-Host "  Deployment Outputs" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Green
        
        Write-Host "VNet ID:           $($result.outputs.vnetId.value)"
        Write-Host "OpenAI Endpoint:   $($result.outputs.openAIEndpoint.value)"
        Write-Host "OpenAI Deployment: $($result.outputs.openAIDeploymentName.value)"
        Write-Host "App Service URL:   $($result.outputs.appServiceUrl.value)"
        Write-Host "Key Vault URI:     $($result.outputs.keyVaultUri.value)"
        Write-Host "SQL Server FQDN:   $($result.outputs.sqlServerFqdn.value)"
        
        Write-Host "`nPrivate Endpoint IPs:" -ForegroundColor Cyan
        $privateEndpoints = $result.outputs.privateEndpointsDeployed.value
        Write-Host "  SQL:      $($privateEndpoints.sql)"
        Write-Host "  Key Vault: $($privateEndpoints.keyVault)"
        Write-Host "  OpenAI:   $($privateEndpoints.openAI)"
        
        Write-Host "`n=============================================" -ForegroundColor Yellow
        Write-Host "  Next Steps" -ForegroundColor Yellow
        Write-Host "=============================================" -ForegroundColor Yellow
        Write-Host "1. Update your .env file with the new OpenAI endpoint"
        Write-Host "2. Deploy your Streamlit app to App Service"
        Write-Host "3. Test private connectivity"
        Write-Host "4. Set enablePublicAccess=false and redeploy to fully lock down"
        
    } else {
        Write-Error "Deployment failed with state: $($result.state)"
        exit 1
    }
}

# Clean up
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
