# Azure API Monitoring - Automated Deployment Script
# PowerShell script for Windows deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "azure-poc",

    [Parameter(Mandatory=$false)]
    [switch]$SkipTerraform,

    [Parameter(Mandatory=$false)]
    [switch]$SkipFunctions,

    [Parameter(Mandatory=$false)]
    [switch]$RunTests
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

# Header
Write-Host "🚀 Azure API Monitoring - Automated Deployment" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Magenta

# Check prerequisites
Write-Info "Checking prerequisites..."

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI version: $($azVersion.'azure-cli')"
} catch {
    Write-Error "Azure CLI not found. Please install Azure CLI first."
    exit 1
}

# Check Terraform
try {
    $tfVersion = terraform version -json | ConvertFrom-Json
    Write-Success "Terraform version: $($tfVersion.terraform_version)"
} catch {
    Write-Error "Terraform not found. Please install Terraform first."
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python version: $pythonVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.9+ first."
    exit 1
}

# Check Azure Functions Core Tools
try {
    $funcVersion = func --version 2>&1
    Write-Success "Azure Functions Core Tools version: $funcVersion"
} catch {
    Write-Warning "Azure Functions Core Tools not found. Function deployment will be skipped."
    $SkipFunctions = $true
}

# Azure Authentication
Write-Info "Checking Azure authentication..."
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Success "Authenticated as: $($account.user.name)"
    Write-Success "Subscription: $($account.name) ($($account.id))"

    if ($SubscriptionId -and $account.id -ne $SubscriptionId) {
        Write-Info "Switching to subscription: $SubscriptionId"
        az account set --subscription $SubscriptionId
    }
} catch {
    Write-Error "Not authenticated to Azure. Please run 'az login' first."
    exit 1
}

# Terraform Deployment
if (-not $SkipTerraform) {
    Write-Info "Starting Terraform deployment..."

    # Initialize Terraform
    Write-Info "Initializing Terraform..."
    terraform init
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform init failed"
        exit 1
    }
    Write-Success "Terraform initialized"

    # Validate configuration
    Write-Info "Validating Terraform configuration..."
    terraform validate
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform validation failed"
        exit 1
    }
    Write-Success "Terraform configuration valid"

    # Plan deployment
    Write-Info "Creating Terraform plan..."
    terraform plan -out=tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform plan failed"
        exit 1
    }
    Write-Success "Terraform plan created"

    # Apply deployment
    Write-Info "Applying Terraform configuration..."
    terraform apply tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Terraform apply failed"
        exit 1
    }
    Write-Success "Infrastructure deployed successfully"

    # Get outputs
    Write-Info "Getting deployment outputs..."
    $outputs = terraform output -json | ConvertFrom-Json
    Write-Success "Function App URL: $($outputs.function_app_url.value)"
    Write-Success "Log Analytics Workspace ID: $($outputs.log_analytics_workspace_id.value)"
} else {
    Write-Warning "Skipping Terraform deployment"
}

# Function App Deployment
if (-not $SkipFunctions) {
    Write-Info "Deploying Azure Functions..."

    # Check if func-app directory exists
    if (-not (Test-Path "func-app")) {
        Write-Error "func-app directory not found"
        exit 1
    }

    # Deploy functions
    Push-Location func-app
    try {
        Write-Info "Publishing functions to Azure..."
        func azure functionapp publish azurepoc-function-app --python
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Function deployment failed"
            exit 1
        }
        Write-Success "Functions deployed successfully"
    } finally {
        Pop-Location
    }
} else {
    Write-Warning "Skipping Function deployment"
}

# Install Python dependencies for testing
Write-Info "Installing Python dependencies..."
try {
    pip install requests -q
    Write-Success "Python dependencies installed"
} catch {
    Write-Warning "Failed to install Python dependencies. Testing may fail."
}

# Run Tests
if ($RunTests) {
    Write-Info "Running comprehensive tests..."

    # Wait for functions to be ready
    Write-Info "Waiting for functions to be ready..."
    Start-Sleep -Seconds 30

    # Run test suite
    try {
        python test_complete_pipeline.py
        Write-Success "Tests completed"
    } catch {
        Write-Warning "Tests failed or encountered errors"
    }
} else {
    Write-Info "Skipping tests. Run with -RunTests to execute test suite."
}

# Deployment Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Magenta
Write-Host "🎉 Deployment Summary" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Magenta

Write-Success "Infrastructure: Deployed"
if (-not $SkipFunctions) { Write-Success "Functions: Deployed" }
Write-Success "Resource Group: $ResourceGroupName"

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run tests: python test_complete_pipeline.py" -ForegroundColor White
Write-Host "2. Generate sample data: python quick_test.py" -ForegroundColor White
Write-Host "3. View dashboards in Azure Portal" -ForegroundColor White
Write-Host "4. Check Log Analytics for incoming data" -ForegroundColor White

Write-Host "`n🔗 Useful Links:" -ForegroundColor Yellow
Write-Host "• Azure Portal: https://portal.azure.com" -ForegroundColor White
Write-Host "• Function App: https://azurepoc-function-app.azurewebsites.net" -ForegroundColor White
Write-Host "• Documentation: README.md" -ForegroundColor White

Write-Host "`n🏁 Deployment completed successfully!" -ForegroundColor Green