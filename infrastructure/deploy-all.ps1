# =============================================================================
# CSAT Guardian - Complete Deployment Script (Commercial Azure)
# =============================================================================
# This script deploys everything needed for CSAT Guardian to Commercial Azure:
# 1. Infrastructure (Bicep) - VNet, SQL, OpenAI, Key Vault, App Service
# 2. Database schema and sample data
# 3. Application code to App Service
#
# Prerequisites:
# - Azure CLI installed and logged in
# - PowerShell 5.1 or later
# - ODBC Driver 18 for SQL Server (for database seeding)
#
# Usage:
#   .\deploy-all.ps1 -SqlPassword "YourSecurePassword123!"
#
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SqlPassword,
    
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId = "a20d761d-cb36-4f83-b827-58ccdb166f39",
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "KMonteagudo_CSAT_Guardian",
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipInfrastructure,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipDatabase,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipAppDeployment
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "`n========================================" -ForegroundColor Cyan; Write-Host $msg -ForegroundColor Cyan; Write-Host "========================================" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# =============================================================================
# Configuration
# =============================================================================

$baseName = "csatguardian"
$environment = "dev"

# Resource names (must match Bicep)
$sqlServerName = "sql-$baseName-$environment"
$sqlDatabaseName = "sqldb-$baseName-$environment"
$appServiceName = "app-$baseName-$environment"
$keyVaultName = "kv-$baseName-$environment"
$openAIName = "oai-$baseName-$environment"

# Paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$bicepFile = Join-Path $scriptDir "bicep\main-commercial.bicep"
$srcDir = Join-Path $projectRoot "src"

Write-Host @"

   ██████╗███████╗ █████╗ ████████╗     ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗
  ██╔════╝██╔════╝██╔══██╗╚══██╔══╝    ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║
  ██║     ███████╗███████║   ██║       ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║
  ██║     ╚════██║██╔══██║   ██║       ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║
  ╚██████╗███████║██║  ██║   ██║       ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║
   ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                                                       
  Deployment Script for Commercial Azure
  
"@ -ForegroundColor Magenta

Write-Info "Subscription: $SubscriptionId"
Write-Info "Resource Group: $ResourceGroupName"
Write-Info "Location: $Location"
Write-Info "Project Root: $projectRoot"

# =============================================================================
# Step 0: Verify Prerequisites
# =============================================================================

Write-Step "Step 0: Verifying Prerequisites"

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI installed (version $($azVersion.'azure-cli'))"
} catch {
    Write-Err "Azure CLI not found. Please install from https://aka.ms/installazurecliwindows"
    exit 1
}

# Set subscription
Write-Info "Setting subscription..."
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to set subscription. Please run 'az login' first."
    exit 1
}
Write-Success "Subscription set to $SubscriptionId"

# Verify resource group exists
$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "false") {
    Write-Err "Resource group '$ResourceGroupName' does not exist."
    Write-Info "Create it with: az group create --name $ResourceGroupName --location $Location"
    exit 1
}
Write-Success "Resource group '$ResourceGroupName' exists"

# =============================================================================
# Step 1: Deploy Infrastructure (Bicep)
# =============================================================================

if (-not $SkipInfrastructure) {
    Write-Step "Step 1: Deploying Infrastructure (Bicep)"
    
    Write-Info "This will create: VNet, SQL Server, Azure OpenAI, Key Vault, App Service..."
    Write-Info "Bicep file: $bicepFile"
    
    $deploymentName = "csat-guardian-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    az deployment group create `
        --name $deploymentName `
        --resource-group $ResourceGroupName `
        --template-file $bicepFile `
        --parameters environment=$environment location=$Location baseName=$baseName sqlAdminPassword=$SqlPassword `
        --output table
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Infrastructure deployment failed!"
        exit 1
    }
    
    Write-Success "Infrastructure deployed successfully!"
    
    # Get outputs
    Write-Info "Retrieving deployment outputs..."
    $outputs = az deployment group show --name $deploymentName --resource-group $ResourceGroupName --query properties.outputs --output json | ConvertFrom-Json
    
    $appServiceUrl = $outputs.appServiceUrl.value
    $sqlServerFqdn = $outputs.sqlServerFqdn.value
    $openAIEndpoint = $outputs.openAIEndpoint.value
    $keyVaultUri = $outputs.keyVaultUri.value
    
    Write-Success "App Service URL: $appServiceUrl"
    Write-Success "SQL Server: $sqlServerFqdn"
    Write-Success "OpenAI Endpoint: $openAIEndpoint"
    Write-Success "Key Vault: $keyVaultUri"
    
} else {
    Write-Info "Skipping infrastructure deployment (--SkipInfrastructure)"
    
    # Still need to get values for later steps
    $sqlServerFqdn = "$sqlServerName.database.windows.net"
    $appServiceUrl = "https://$appServiceName.azurewebsites.net"
}

# =============================================================================
# Step 2: Seed Database
# =============================================================================

if (-not $SkipDatabase) {
    Write-Step "Step 2: Seeding Database"
    
    Write-Info "Waiting 30 seconds for SQL Server to be fully ready..."
    Start-Sleep -Seconds 30
    
    # Add current IP to SQL firewall
    Write-Info "Adding current IP to SQL Server firewall..."
    $myIp = (Invoke-RestMethod -Uri "https://api.ipify.org?format=text" -TimeoutSec 10)
    Write-Info "Your IP: $myIp"
    
    az sql server firewall-rule create `
        --resource-group $ResourceGroupName `
        --server $sqlServerName `
        --name "DeploymentIP-$(Get-Date -Format 'yyyyMMddHHmmss')" `
        --start-ip-address $myIp `
        --end-ip-address $myIp `
        --output none
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to add firewall rule. You may need to do this manually in Azure Portal."
    } else {
        Write-Success "Firewall rule added for $myIp"
    }
    
    # Build connection string
    $connectionString = "Server=tcp:$sqlServerFqdn,1433;Initial Catalog=$sqlDatabaseName;Persist Security Info=False;User ID=sqladmin;Password=$SqlPassword;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
    
    Write-Info "Creating database schema and seeding data..."
    
    # SQL Script for schema and data
    $sqlScript = @"
-- =============================================================================
-- CSAT Guardian - Database Schema and Sample Data
-- =============================================================================

-- Create Engineers table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Engineers')
CREATE TABLE Engineers (
    Id NVARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(255) NOT NULL,
    TeamsId NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE()
);

-- Create Customers table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers')
CREATE TABLE Customers (
    Id NVARCHAR(50) PRIMARY KEY,
    Company NVARCHAR(255) NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETUTCDATE()
);

-- Create Cases table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cases')
CREATE TABLE Cases (
    Id NVARCHAR(50) PRIMARY KEY,
    Title NVARCHAR(500) NOT NULL,
    Description NVARCHAR(MAX),
    Status NVARCHAR(50) NOT NULL DEFAULT 'active',
    Priority NVARCHAR(50) NOT NULL DEFAULT 'medium',
    OwnerId NVARCHAR(50) NOT NULL,
    CustomerId NVARCHAR(50) NOT NULL,
    CreatedOn DATETIME2 NOT NULL,
    ModifiedOn DATETIME2 NOT NULL,
    FOREIGN KEY (OwnerId) REFERENCES Engineers(Id),
    FOREIGN KEY (CustomerId) REFERENCES Customers(Id)
);

-- Create TimelineEntries table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TimelineEntries')
CREATE TABLE TimelineEntries (
    Id NVARCHAR(50) PRIMARY KEY,
    CaseId NVARCHAR(50) NOT NULL,
    EntryType NVARCHAR(50) NOT NULL,
    Subject NVARCHAR(500),
    Content NVARCHAR(MAX),
    CreatedOn DATETIME2 NOT NULL,
    CreatedBy NVARCHAR(100),
    IsCustomerCommunication BIT DEFAULT 0,
    FOREIGN KEY (CaseId) REFERENCES Cases(Id)
);

-- Create Alerts table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Alerts')
CREATE TABLE Alerts (
    Id NVARCHAR(50) PRIMARY KEY,
    CaseId NVARCHAR(50) NOT NULL,
    EngineerId NVARCHAR(50) NOT NULL,
    AlertType NVARCHAR(50) NOT NULL,
    Message NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    SentAt DATETIME2,
    FOREIGN KEY (CaseId) REFERENCES Cases(Id),
    FOREIGN KEY (EngineerId) REFERENCES Engineers(Id)
);

-- Clear existing data (for idempotent deployment)
DELETE FROM TimelineEntries;
DELETE FROM Alerts;
DELETE FROM Cases;
DELETE FROM Customers;
DELETE FROM Engineers;

-- Insert Engineers
INSERT INTO Engineers (Id, Name, Email, TeamsId) VALUES
('eng-001', 'John Smith', 'john.smith@microsoft.com', 'john.smith'),
('eng-002', 'Sarah Johnson', 'sarah.johnson@microsoft.com', 'sarah.johnson'),
('eng-003', 'Mike Chen', 'mike.chen@microsoft.com', 'mike.chen');

-- Insert Customers
INSERT INTO Customers (Id, Company) VALUES
('cust-001', 'Contoso Ltd'),
('cust-002', 'Fabrikam Inc'),
('cust-003', 'Northwind Traders'),
('cust-004', 'Adventure Works'),
('cust-005', 'Woodgrove Bank'),
('cust-006', 'Tailspin Toys');

-- Insert Cases (6 scenarios covering different situations)
INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
('case-001', 'Azure VM Performance Optimization', 'Customer reports slow VM performance during peak hours. Need help optimizing configuration.', 'active', 'medium', 'eng-001', 'cust-001', DATEADD(day, -10, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE())),
('case-002', 'Storage Account Access Issues', 'Getting 403 errors when accessing blob storage from web app. Urgent production issue.', 'active', 'high', 'eng-001', 'cust-002', DATEADD(day, -5, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-003', 'Azure SQL Query Performance', 'Some queries taking longer than expected. Need query optimization assistance.', 'active', 'medium', 'eng-002', 'cust-003', DATEADD(day, -7, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE())),
('case-004', 'Billing Discrepancy Investigation', 'Customer disputes charges for last month. Claims they were billed for resources not used.', 'active', 'high', 'eng-001', 'cust-004', DATEADD(day, -14, GETUTCDATE()), DATEADD(day, -10, GETUTCDATE())),
('case-005', 'App Service Deployment Failures', 'CI/CD pipeline failing intermittently. Need help debugging deployment issues.', 'active', 'medium', 'eng-002', 'cust-005', DATEADD(day, -8, GETUTCDATE()), DATEADD(day, -6, GETUTCDATE())),
('case-006', 'Network Connectivity Problems', 'VMs in different subnets unable to communicate. NSG rules appear correct.', 'active', 'critical', 'eng-003', 'cust-006', DATEADD(day, -12, GETUTCDATE()), DATEADD(day, -8, GETUTCDATE()));

-- Insert Timeline Entries for Case 1 (Happy path - good sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-001-01', 'case-001', 'email', 'RE: VM Performance', 'Hi, thanks for looking into this. We are seeing slow response times during business hours (9am-5pm EST).', DATEADD(day, -9, GETUTCDATE()), 'Customer', 1),
('tl-001-02', 'case-001', 'note', 'Initial Analysis', 'Reviewed VM metrics. CPU peaks at 95% during reported times. Recommend scaling up or implementing auto-scale.', DATEADD(day, -8, GETUTCDATE()), 'John Smith', 0),
('tl-001-03', 'case-001', 'email', 'RE: VM Performance', 'Thank you so much for the quick response! The recommendations look great. We will implement auto-scaling.', DATEADD(day, -3, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 2 (Frustrated customer - negative sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-002-01', 'case-002', 'email', 'URGENT: Storage Access', 'This is URGENT! Our production application is DOWN because we cannot access storage. We need this fixed IMMEDIATELY!', DATEADD(day, -4, GETUTCDATE()), 'Customer', 1),
('tl-002-02', 'case-002', 'note', 'Troubleshooting', 'Checking storage account configuration and access policies.', DATEADD(day, -3, GETUTCDATE()), 'John Smith', 0),
('tl-002-03', 'case-002', 'email', 'RE: Storage Access', 'We have been waiting for 2 days now. This is completely unacceptable. We are losing money every hour this is down!', DATEADD(day, -1, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 3 (Neutral sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-003-01', 'case-003', 'email', 'Query Performance', 'We have some queries that are slower than expected. Can you help us optimize them?', DATEADD(day, -6, GETUTCDATE()), 'Customer', 1),
('tl-003-02', 'case-003', 'note', 'Analysis', 'Requested query execution plans for analysis.', DATEADD(day, -5, GETUTCDATE()), 'Sarah Johnson', 0),
('tl-003-03', 'case-003', 'email', 'RE: Query Performance', 'Here are the execution plans as requested. Let us know what you find.', DATEADD(day, -2, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 4 (Declining sentiment - 7-day breach)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-004-01', 'case-004', 'email', 'Billing Question', 'Hi, we noticed some unexpected charges on our bill. Can you help clarify?', DATEADD(day, -13, GETUTCDATE()), 'Customer', 1),
('tl-004-02', 'case-004', 'note', 'Reviewing charges', 'Looking into billing details for the customer account.', DATEADD(day, -12, GETUTCDATE()), 'John Smith', 0),
('tl-004-03', 'case-004', 'email', 'RE: Billing', 'It has been a week and we still have not heard back. This is getting frustrating. We need answers!', DATEADD(day, -10, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 5 (7-day warning approaching)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-005-01', 'case-005', 'email', 'Deployment Issues', 'Our deployments are failing randomly. Sometimes they work, sometimes they dont.', DATEADD(day, -7, GETUTCDATE()), 'Customer', 1),
('tl-005-02', 'case-005', 'note', 'Initial review', 'Requested deployment logs and pipeline configuration.', DATEADD(day, -6, GETUTCDATE()), 'Sarah Johnson', 0);

-- Insert Timeline Entries for Case 6 (7-day breach with declining sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-006-01', 'case-006', 'email', 'Network Issue', 'VMs cannot communicate across subnets. This is blocking our project timeline.', DATEADD(day, -11, GETUTCDATE()), 'Customer', 1),
('tl-006-02', 'case-006', 'note', 'Checking NSGs', 'Reviewed NSG rules, they appear correct. Need deeper investigation.', DATEADD(day, -10, GETUTCDATE()), 'Mike Chen', 0),
('tl-006-03', 'case-006', 'email', 'RE: Network Issue', 'We have been stuck on this for over a week now. Our deadline is approaching and we are very worried. Please escalate if needed!', DATEADD(day, -8, GETUTCDATE()), 'Customer', 1);

PRINT 'Database schema created and sample data inserted successfully!';
"@

    # Save SQL script to temp file
    $sqlScriptPath = Join-Path $env:TEMP "csat-guardian-seed.sql"
    $sqlScript | Out-File -FilePath $sqlScriptPath -Encoding UTF8
    
    # Execute SQL script using sqlcmd
    Write-Info "Executing SQL script..."
    
    # Try using sqlcmd
    try {
        sqlcmd -S $sqlServerFqdn -d $sqlDatabaseName -U sqladmin -P $SqlPassword -i $sqlScriptPath -I
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database seeded successfully!"
        } else {
            Write-Err "sqlcmd failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Err "sqlcmd not found or failed. Error: $_"
        Write-Info "You can manually run the SQL script from: $sqlScriptPath"
        Write-Info "Or use Azure Portal Query Editor to run it."
    }
    
    # Clean up temp file
    Remove-Item $sqlScriptPath -ErrorAction SilentlyContinue
    
} else {
    Write-Info "Skipping database seeding (--SkipDatabase)"
}

# =============================================================================
# Step 3: Deploy Application Code
# =============================================================================

if (-not $SkipAppDeployment) {
    Write-Step "Step 3: Deploying Application Code"
    
    Write-Info "Preparing application for deployment..."
    
    # Create deployment package
    $deployDir = Join-Path $env:TEMP "csat-guardian-deploy"
    $zipPath = Join-Path $env:TEMP "csat-guardian-deploy.zip"
    
    # Clean up previous deployment files
    if (Test-Path $deployDir) { Remove-Item $deployDir -Recurse -Force }
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    
    # Create deployment directory
    New-Item -ItemType Directory -Path $deployDir | Out-Null
    
    # Copy source files
    Write-Info "Copying source files..."
    Copy-Item -Path (Join-Path $srcDir "*") -Destination $deployDir -Recurse -Force
    
    # Copy requirements.txt to root
    Copy-Item -Path (Join-Path $projectRoot "requirements.txt") -Destination $deployDir -Force
    
    # Create startup command file
    $startupContent = "python -m uvicorn api:app --host 0.0.0.0 --port 8000"
    $startupContent | Out-File -FilePath (Join-Path $deployDir "startup.txt") -Encoding UTF8
    
    # Create ZIP file
    Write-Info "Creating deployment package..."
    Compress-Archive -Path (Join-Path $deployDir "*") -DestinationPath $zipPath -Force
    
    $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
    Write-Info "Deployment package size: $zipSize MB"
    
    # Deploy to App Service
    Write-Info "Deploying to App Service (this may take a few minutes)..."
    
    az webapp deploy `
        --resource-group $ResourceGroupName `
        --name $appServiceName `
        --src-path $zipPath `
        --type zip `
        --async false
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "App deployment failed!"
        Write-Info "You can try deploying manually with:"
        Write-Info "  az webapp deploy --resource-group $ResourceGroupName --name $appServiceName --src-path $zipPath --type zip"
        exit 1
    }
    
    Write-Success "Application deployed successfully!"
    
    # Clean up
    Remove-Item $deployDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    
    # Restart app to apply changes
    Write-Info "Restarting App Service..."
    az webapp restart --resource-group $ResourceGroupName --name $appServiceName
    
    Write-Info "Waiting 30 seconds for app to start..."
    Start-Sleep -Seconds 30
    
} else {
    Write-Info "Skipping app deployment (--SkipAppDeployment)"
}

# =============================================================================
# Step 4: Verification
# =============================================================================

Write-Step "Step 4: Verification"

$appUrl = "https://$appServiceName.azurewebsites.net"

Write-Info "Testing application health endpoint..."
try {
    $response = Invoke-RestMethod -Uri "$appUrl/api/health" -TimeoutSec 60
    Write-Success "Application is running!"
    Write-Host "  Status: $($response.status)" -ForegroundColor Green
    Write-Host "  Environment: $($response.environment)" -ForegroundColor Green
} catch {
    Write-Err "Health check failed: $_"
    Write-Info "The app may still be starting. Check the URL manually in a few minutes."
}

# =============================================================================
# Summary
# =============================================================================

Write-Step "Deployment Complete!"

Write-Host @"

   CSAT Guardian has been deployed successfully!

   Application URL:  $appUrl
   Swagger Docs:     $appUrl/docs
   
   Azure Resources Created:
   - Virtual Network:    vnet-$baseName-$environment
   - SQL Server:         $sqlServerFqdn
   - Azure OpenAI:       oai-$baseName-$environment.openai.azure.com
   - Key Vault:          kv-$baseName-$environment.vault.azure.net
   - App Service:        $appServiceName.azurewebsites.net
   
   Test the API:
   - Health Check:  curl $appUrl/api/health
   - Engineers:     curl $appUrl/api/engineers
   - Cases:         curl $appUrl/api/cases
   
   To disable public access (recommended after testing):
   1. Go to Azure Portal
   2. Set public network access to 'Disabled' on SQL, Key Vault, and OpenAI
   
"@ -ForegroundColor Green

Write-Host "Deployment completed at $(Get-Date)" -ForegroundColor Cyan
