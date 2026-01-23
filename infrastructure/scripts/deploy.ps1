# =============================================================================
# CSAT Guardian - Azure Government Deployment Script
# =============================================================================
# This script deploys the CSAT Guardian infrastructure to Azure Government.
#
# IMPORTANT: This script targets AZURE GOVERNMENT cloud.
# You must be logged in to Azure Government (az cloud set --name AzureUSGovernment)
#
# Prerequisites:
#   - Azure CLI installed and logged in (az cloud set --name AzureUSGovernment && az login)
#   - Contributor access to target Government subscription
#   - PowerShell 7+
#
# Usage:
#   ./deploy.ps1 -Environment dev -Location usgovvirginia
#   ./deploy.ps1 -Environment prod -Location usgovvirginia -DeployOpenAI
# =============================================================================

[CmdletBinding()]
param(
    # Environment to deploy (dev, test, prod)
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "test", "prod")]
    [string]$Environment,

    # Azure Government region
    [Parameter(Mandatory = $false)]
    [ValidateSet("usgovvirginia", "usgovarizona", "usgovtexas")]
    [string]$Location = "usgovvirginia",

    # Whether to deploy Azure OpenAI (set to false if using existing)
    [Parameter(Mandatory = $false)]
    [switch]$DeployOpenAI,

    # Existing Azure OpenAI endpoint (if not deploying new)
    [Parameter(Mandatory = $false)]
    [string]$ExistingOpenAIEndpoint = "",

    # SQL Admin password (will prompt if not provided)
    [Parameter(Mandatory = $false)]
    [SecureString]$SqlAdminPassword
)

# =============================================================================
# Configuration
# =============================================================================

$ErrorActionPreference = "Stop"

$baseName = "csatguardian"
$resourceGroupName = "rg-$baseName-$Environment"
$bicepPath = Join-Path $PSScriptRoot "..\bicep\main.bicep"

# =============================================================================
# Functions
# =============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Blue
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

Write-Step "Pre-flight Checks"

# Check Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is not installed. Please install from https://aka.ms/installazurecli"
}
Write-Success "Azure CLI found"

# Check logged in to Azure
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    throw "Not logged in to Azure. Please run 'az cloud set --name AzureUSGovernment' then 'az login' first."
}
Write-Success "Logged in as: $($account.user.name)"
Write-Info "Subscription: $($account.name) ($($account.id))"

# Verify we're connected to Azure Government
$cloud = az cloud show 2>$null | ConvertFrom-Json
if ($cloud.name -ne "AzureUSGovernment") {
    Write-Warning "Current cloud: $($cloud.name)"
    Write-Warning "This script is designed for Azure Government."
    Write-Warning "Run 'az cloud set --name AzureUSGovernment' to switch."
    throw "Not connected to Azure Government cloud."
}
Write-Success "Connected to Azure Government cloud"

# Check Bicep file exists
if (-not (Test-Path $bicepPath)) {
    throw "Bicep template not found at: $bicepPath"
}
Write-Success "Bicep template found"

# Prompt for SQL password if not provided
if (-not $SqlAdminPassword) {
    Write-Info "Please enter SQL Administrator password:"
    $SqlAdminPassword = Read-Host -AsSecureString
}

# Convert secure string to plain text for Azure CLI
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SqlAdminPassword)
$sqlPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

# =============================================================================
# Create Resource Group
# =============================================================================

Write-Step "Creating Resource Group"

$rgExists = az group exists --name $resourceGroupName | ConvertFrom-Json

if ($rgExists) {
    Write-Info "Resource group '$resourceGroupName' already exists"
} else {
    az group create `
        --name $resourceGroupName `
        --location $Location `
        --tags Application="CSAT Guardian" Environment=$Environment ManagedBy="Script"
    
    Write-Success "Created resource group: $resourceGroupName"
}

# =============================================================================
# Deploy Infrastructure
# =============================================================================

Write-Step "Deploying Infrastructure (this may take 5-10 minutes)"

$deploymentName = "csat-guardian-$Environment-$(Get-Date -Format 'yyyyMMddHHmmss')"

$deployParams = @(
    "--resource-group", $resourceGroupName,
    "--template-file", $bicepPath,
    "--name", $deploymentName,
    "--parameters", "environment=$Environment",
    "--parameters", "sqlAdminPassword=$sqlPasswordPlain",
    "--parameters", "deployOpenAI=$($DeployOpenAI.IsPresent.ToString().ToLower())"
)

if ($ExistingOpenAIEndpoint) {
    $deployParams += "--parameters"
    $deployParams += "existingOpenAIEndpoint=$ExistingOpenAIEndpoint"
}

Write-Info "Starting deployment: $deploymentName"

$result = az deployment group create @deployParams 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host $result -ForegroundColor Red
    throw "Deployment failed"
}

$deployment = $result | ConvertFrom-Json
Write-Success "Deployment completed successfully"

# =============================================================================
# Display Outputs
# =============================================================================

Write-Step "Deployment Outputs"

$outputs = $deployment.properties.outputs

Write-Host ""
Write-Host "  Resource Group:     $resourceGroupName" -ForegroundColor White
Write-Host "  Key Vault:          $($outputs.keyVaultUri.value)" -ForegroundColor White
Write-Host "  SQL Server:         $($outputs.sqlServerFqdn.value)" -ForegroundColor White
Write-Host "  SQL Database:       $($outputs.sqlDatabaseName.value)" -ForegroundColor White
Write-Host "  Container Registry: $($outputs.containerRegistryLoginServer.value)" -ForegroundColor White
Write-Host "  Container App URL:  $($outputs.containerAppUrl.value)" -ForegroundColor White

if ($outputs.openAIEndpoint.value) {
    Write-Host "  Azure OpenAI:       $($outputs.openAIEndpoint.value)" -ForegroundColor White
}

# =============================================================================
# Next Steps
# =============================================================================

Write-Step "Next Steps"

Write-Host "  1. Store Azure OpenAI API key in Key Vault:" -ForegroundColor Yellow
Write-Host "     az keyvault secret set --vault-name kv-$baseName-$Environment --name AzureOpenAI--ApiKey --value YOUR_KEY" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Build and push container image (Azure Gov uses .azurecr.us):" -ForegroundColor Yellow
Write-Host "     az acr build --registry acr$baseName$Environment --image csat-guardian:latest ./src" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Update container app with new image:" -ForegroundColor Yellow
Write-Host "     az containerapp update --name ca-$baseName-$Environment --resource-group $resourceGroupName --image acr$baseName$Environment.azurecr.us/csat-guardian:latest" -ForegroundColor Yellow
Write-Host ""
Write-Host "  4. Seed the database with sample data:" -ForegroundColor Yellow
Write-Host "     ./seed-database.ps1 -Environment $Environment" -ForegroundColor Yellow
Write-Host ""
Write-Host "  5. Access the application:" -ForegroundColor Yellow
Write-Host "     $($outputs.containerAppUrl.value)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  IMPORTANT: Azure Government Endpoints:" -ForegroundColor Yellow
Write-Host "    - Key Vault: https://kv-$baseName-$Environment.vault.usgovcloudapi.net/" -ForegroundColor Yellow
Write-Host "    - SQL Server: sql-$baseName-$Environment.database.usgovcloudapi.net" -ForegroundColor Yellow
Write-Host "    - Container Registry: acr$baseName$Environment.azurecr.us" -ForegroundColor Yellow

Write-Host ""
Write-Success "Deployment complete!"
Write-Host ""
