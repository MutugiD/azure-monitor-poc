# Azure API Monitoring Dashboard - Salesforce & MuleSoft

A comprehensive monitoring solution that simulates and tracks API metrics from Salesforce and MuleSoft systems, providing real-time dashboards and analytics through Azure Monitor.

## 🎯 Overview

This project creates a complete API monitoring pipeline that:
- **Simulates** realistic Salesforce and MuleSoft API events
- **Processes** events through Azure Functions with intelligent routing
- **Stores** data in Azure Log Analytics with custom log types
- **Visualizes** metrics through Azure Dashboards and Workbooks
- **Monitors** 2 key metrics: API Response Times and Error Rates

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   API Simulator │───▶│  Azure Functions │───▶│  Log Analytics      │
│                 │    │                  │    │                     │
│ • Salesforce    │    │ • salesforceLog  │    │ • SalesforceEvent   │
│ • MuleSoft      │    │ • mulesoftLog    │    │ • MuleSoftPerf      │
│ • Event Types   │    │ • universalLog   │    │ • MuleSoftError     │
└─────────────────┘    └──────────────────┘    │ • MuleSoftUptime    │
                                               └─────────────────────┘
                                                          │
                                               ┌─────────────────────┐
                                               │  Azure Dashboards   │
                                               │                     │
                                               │ • Response Times    │
                                               │ • Error Rates       │
                                               │ • Real-time Charts  │
                                               └─────────────────────┘
```

## 📋 Prerequisites

### Required Software
- **Terraform** >= 1.0
- **Azure CLI** >= 2.0
- **Python** >= 3.9
- **Azure Functions Core Tools** >= 4.0

### Azure Requirements
- **Azure Subscription** with Contributor access
- **Service Principal** for Terraform authentication
- **Resource Group** creation permissions

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd azure-monitor/azure-poc
```

### 2. Azure Authentication
```bash
# Create service principal
az ad sp create-for-rbac --name terraform-poc-sp --role Contributor --scopes /subscriptions/YOUR_SUBSCRIPTION_ID --sdk-auth

# Set environment variables
set ARM_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
set ARM_CLIENT_ID=YOUR_CLIENT_ID
set ARM_CLIENT_SECRET=YOUR_CLIENT_SECRET
set ARM_TENANT_ID=YOUR_TENANT_ID
```

### 3. Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy resources
terraform apply --auto-approve
```

### 4. Deploy Function Code
```bash
cd func-app
func azure functionapp publish azurepoc-function-app
cd ..
```

### 5. Test the Pipeline
```bash
# Run comprehensive tests
python test_complete_pipeline.py

# Run quick simulation
python quick_test.py
```

## 📁 Project Structure

```
azure-poc/
├── main.tf                    # Main Terraform configuration
├── variable.tf                # Terraform variables
├── terraform.tfvars.example   # Example variables file
├── func-app/                  # Azure Function code
│   ├── function_app.py        # Main function logic
│   ├── requirements.txt       # Python dependencies
│   ├── host.json             # Function host configuration
│   └── local.settings.json   # Local development settings
├── api_simulator.py           # Multi-API event simulator
├── quick_test.py             # Quick functionality test
├── test_complete_pipeline.py  # Comprehensive test suite
└── README.md                 # This file
```

## 🔧 Configuration

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `resource_group_name` | Azure Resource Group name | `azure-poc` |
| `resource_group_location` | Azure region | `West Europe` |
| `storage_account_name` | Storage account (must be unique) | `azurepocstoragev1` |
| `function_app_name` | Function App name (must be unique) | `azurepoc-function-app` |
| `log_analytics_workspace_name` | Log Analytics workspace | `azurepoc-workspace` |
| `dashboard_name` | Azure Dashboard name | `azurepoc-api-dashboard` |

### Customization
Create `terraform.tfvars`:
```hcl
resource_group_name = "my-api-monitoring"
storage_account_name = "myapimonitoringstorage"
function_app_name = "my-api-function-app"
```

## 📊 Monitoring & Dashboards

### Key Metrics Tracked

#### 1. API Response Times
- **Salesforce APIs**: Login, Data operations, Query performance
- **MuleSoft APIs**: Integration latency, Processing time, Resource usage
- **Visualization**: Time series charts, Average/Max response times

#### 2. API Error Rates
- **Error Detection**: HTTP 4xx/5xx status codes, Failed operations
- **Error Types**: Authentication, Timeout, Rate limiting, System errors
- **Visualization**: Error percentage trends, Error count by system

### Dashboard Access
1. **Azure Portal** → **Dashboards** → `azurepoc-api-dashboard`
2. **Log Analytics** → `azurepoc-workspace` → **Workbooks**
3. **Application Insights** → `azurepoc-app-insights`

### Sample KQL Queries

#### Recent Events Overview
```kql
union SalesforceEvent_CL, MuleSoftPerformance_CL, MuleSoftError_CL, MuleSoftUptime_CL
| where TimeGenerated > ago(1h)
| summarize Count = count() by Type, bin(TimeGenerated, 5m)
| render timechart
```

#### Response Time Analysis
```kql
union SalesforceEvent_CL, MuleSoftPerformance_CL
| where TimeGenerated > ago(24h)
| where isnotempty(ResponseTime_d) or isnotempty(responseTime_d)
| extend ResponseTime = coalesce(ResponseTime_d, responseTime_d)
| extend API_System = case(
    SourceSystem_s == "Salesforce", "Salesforce",
    SourceSystem_s == "MuleSoft", "MuleSoft",
    "Other"
)
| summarize AvgResponseTime = avg(ResponseTime), MaxResponseTime = max(ResponseTime)
  by API_System, bin(TimeGenerated, 1h)
| render timechart
```

#### Error Rate Monitoring
```kql
union SalesforceEvent_CL, MuleSoftError_CL, MuleSoftPerformance_CL
| where TimeGenerated > ago(24h)
| extend API_System = case(
    SourceSystem_s == "Salesforce", "Salesforce",
    SourceSystem_s == "MuleSoft", "MuleSoft",
    "Other"
)
| extend IsError = case(
    StatusCode_d >= 400, 1,
    Success_b == false, 1,
    contains(Type, "Error"), 1,
    0
)
| summarize TotalRequests = count(), ErrorCount = sum(IsError),
  ErrorRate = (sum(IsError) * 100.0) / count()
  by API_System, bin(TimeGenerated, 1h)
| render timechart
```

## 🧪 Testing

### Automated Testing
```bash
# Full pipeline test
python test_complete_pipeline.py

# Quick functionality check
python quick_test.py

# Custom simulation
python api_simulator.py
```

### Test Coverage
- ✅ **Function Endpoints**: All 3 endpoints (Salesforce, MuleSoft, Universal)
- ✅ **Event Generation**: 6 event types with validation
- ✅ **Data Flow**: End-to-end event processing
- ✅ **Performance**: Load testing with 20+ events
- ✅ **Error Handling**: Invalid JSON, empty payloads
- ✅ **Dashboard Data**: Comprehensive test data generation

### Manual Verification
1. **Azure Portal** → **Log Analytics** → Run KQL queries
2. **Function App** → **Monitor** → Check execution logs
3. **Dashboard** → Verify charts display data
4. **Application Insights** → Review performance metrics

## 🔍 Troubleshooting

### Common Issues

#### 1. Terraform Deployment Failures

**Issue**: `InvalidSubscriptionId` error
```bash
Error: InvalidSubscriptionId: The provided subscription identifier is malformed
```
**Solution**:
```bash
# Verify subscription ID (no extra spaces)
az account show --query id -o tsv

# Re-authenticate
az login --service-principal -u $ARM_CLIENT_ID -p $ARM_CLIENT_SECRET --tenant $ARM_TENANT_ID
```

**Issue**: Resource name conflicts
```bash
Error: A resource with the ID already exists
```
**Solution**:
```bash
# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/SUB_ID/resourceGroups/RESOURCE_GROUP

# Or use unique names in terraform.tfvars
```

#### 2. Function Deployment Issues

**Issue**: Function deployment fails
```bash
Error: Failed to deploy function package
```
**Solution**:
```bash
# Check Azure CLI authentication
az account show

# Verify Function App exists
az functionapp list --resource-group azure-poc

# Redeploy with verbose logging
func azure functionapp publish azurepoc-function-app --verbose
```

**Issue**: Function returns 500 errors
```bash
Status: 500 Internal Server Error
```
**Solution**:
```bash
# Check function logs
az functionapp logs tail --name azurepoc-function-app --resource-group azure-poc

# Verify environment variables
az functionapp config appsettings list --name azurepoc-function-app --resource-group azure-poc
```

#### 3. Log Analytics Issues

**Issue**: Custom log tables not appearing
```bash
Error: Failed to resolve table expression named 'SalesforceEvent_CL'
```
**Solution**:
- **Wait 5-15 minutes** for custom log tables to be created
- Verify events are being sent successfully (check Function logs)
- Use broader search: `search * | where TimeGenerated > ago(1h)`

**Issue**: No data in dashboards
```bash
Dashboard shows "No data available"
```
**Solution**:
```bash
# Generate test data
python quick_test.py

# Check Log Analytics directly
# Azure Portal → Log Analytics → Logs → Run: search *

# Verify time range in dashboard (last 24 hours)
```

**Issue**: Dashboard shows "Not found" with 404 errors
```bash
Dashboard tiles show "Not found" error
```
**Solution**:
- **This is normal** - Custom log tables take 5-15 minutes to appear after first data ingestion
- **Wait 5-15 minutes**, then refresh dashboard
- If still not working, follow manual dashboard creation in `DASHBOARD_FIX_GUIDE.md`
- Verify data exists: `search * | where TimeGenerated > ago(1h)`

#### 4. Authentication Issues

**Issue**: Service Principal permissions
```bash
Error: Insufficient privileges to complete the operation
```
**Solution**:
```bash
# Assign Contributor role
az role assignment create --assignee $ARM_CLIENT_ID --role Contributor --scope /subscriptions/$ARM_SUBSCRIPTION_ID

# Verify permissions
az role assignment list --assignee $ARM_CLIENT_ID
```

### Debug Commands

```bash
# Check Terraform state
terraform show

# Validate configuration
terraform validate

# Check Azure resources
az resource list --resource-group azure-poc --output table

# Test function endpoints
curl -X POST "https://azurepoc-function-app.azurewebsites.net/api/salesforceLogHandler" \
  -H "Content-Type: application/json" \
  -d '{"eventType":"Test","timestamp":"2024-12-07T15:00:00Z","eventId":"test-123"}'

# Check Log Analytics
az monitor log-analytics query --workspace "WORKSPACE_ID" --analytics-query "search *"
```

## 📈 Performance & Scaling

### Current Capacity
- **Function App**: Consumption tier (auto-scaling)
- **Log Analytics**: 500MB/day free tier
- **Event Rate**: ~10-50 events/minute tested
- **Response Time**: <500ms average

### Scaling Considerations
- **Higher Volume**: Upgrade to Premium Function plan
- **Data Retention**: Increase Log Analytics retention
- **Global Distribution**: Deploy to multiple regions
- **Cost Optimization**: Use reserved capacity for predictable workloads

## 🔒 Security

### Current Security Features
- ✅ **HTTPS Only**: All endpoints use TLS
- ✅ **Managed Identity**: Function App uses system-assigned identity
- ✅ **Key Vault Integration**: Ready for secret management
- ✅ **Network Security**: Default Azure network protection

### Production Recommendations
- **API Keys**: Implement authentication for Function endpoints
- **Network Isolation**: Use VNet integration
- **Monitoring**: Enable Azure Security Center
- **Compliance**: Configure data retention policies

## 🚀 Deployment Automation

### CI/CD Pipeline (GitHub Actions Example)
```yaml
name: Deploy API Monitoring
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v1

    - name: Terraform Deploy
      run: |
        terraform init
        terraform apply -auto-approve
      env:
        ARM_SUBSCRIPTION_ID: ${{ secrets.ARM_SUBSCRIPTION_ID }}
        ARM_CLIENT_ID: ${{ secrets.ARM_CLIENT_ID }}
        ARM_CLIENT_SECRET: ${{ secrets.ARM_CLIENT_SECRET }}
        ARM_TENANT_ID: ${{ secrets.ARM_TENANT_ID }}

    - name: Deploy Functions
      run: |
        cd func-app
        func azure functionapp publish azurepoc-function-app
```

## 📞 Support & Contributing

### Getting Help
1. **Check logs**: Function App → Monitor → Logs
2. **Review documentation**: This README
3. **Run diagnostics**: `python test_complete_pipeline.py`
4. **Azure Support**: For Azure-specific issues

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-metric`
3. Test changes: `python test_complete_pipeline.py`
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏷️ Version History

- **v1.0.0** - Initial release with Salesforce and MuleSoft monitoring
- **v1.1.0** - Added comprehensive testing suite
- **v1.2.0** - Enhanced dashboard with 2 key metrics focus
- **v1.3.0** - Added troubleshooting guide and automation

---

**Built with ❤️ for API monitoring and observability**"# azure-monitor-poc" 
"# azure-monitor-poc" 
