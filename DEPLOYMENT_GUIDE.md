# 🚀 Quick Deployment Guide - Azure API Monitoring

## Prerequisites Checklist
- [ ] Azure CLI installed and authenticated (`az login`)
- [ ] Terraform >= 1.0 installed
- [ ] Python >= 3.9 installed
- [ ] Azure Functions Core Tools >= 4.0 installed
- [ ] Azure subscription with Contributor access

## 5-Minute Deployment

### 1. Clone & Configure
```bash
git clone <repository-url>
cd azure-monitor/azure-poc

# Copy and customize variables (optional)
copy terraform.tfvars.example terraform.tfvars
```

### 2. Deploy Infrastructure
```bash
terraform init
terraform apply --auto-approve
```

### 3. Deploy Functions
```bash
cd func-app
func azure functionapp publish azurepoc-function-app
cd ..
```

### 4. Validate Deployment
```bash
python validate_deployment.py
```

### 5. Generate Test Data
```bash
python quick_test.py
```

## Automated Deployment (Windows)
```powershell
# Run everything automatically
.\deploy.ps1 -RunTests

# Custom subscription
.\deploy.ps1 -SubscriptionId "your-subscription-id" -RunTests
```

## Key Resources Created

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `azure-poc` | Container for all resources |
| Function App | `azurepoc-function-app` | API event processing |
| Log Analytics | `azurepoc-workspace` | Data storage and querying |
| Storage Account | `azurepocstoragev1` | Function app storage |
| Dashboard | `azurepoc-api-dashboard` | Monitoring visualization |
| App Insights | `azurepoc-app-insights` | Application monitoring |

## Verification Steps

### 1. Test Function Endpoints
```bash
# Quick validation
python validate_deployment.py

# Comprehensive testing
python test_complete_pipeline.py
```

### 2. Check Azure Portal
1. **Function App**: Verify functions are running
2. **Log Analytics**: Check for incoming data
3. **Dashboard**: View API metrics
4. **Application Insights**: Monitor performance

### 3. Sample KQL Queries
```kql
// Check recent events
search * | where TimeGenerated > ago(1h) | summarize count() by Type

// API Response Times
union SalesforceEvent_CL, MuleSoftPerformance_CL
| where isnotempty(ResponseTime_d) or isnotempty(responseTime_d)
| extend ResponseTime = coalesce(ResponseTime_d, responseTime_d)
| summarize avg(ResponseTime) by bin(TimeGenerated, 1h)

// Error Rates
union SalesforceEvent_CL, MuleSoftError_CL
| extend IsError = case(StatusCode_d >= 400, 1, Success_b == false, 1, 0)
| summarize ErrorRate = (sum(IsError) * 100.0) / count() by bin(TimeGenerated, 1h)
```

## Troubleshooting Quick Fixes

### Function App Issues
```bash
# Check function status
az functionapp list --resource-group azure-poc --output table

# View function logs
az functionapp logs tail --name azurepoc-function-app --resource-group azure-poc

# Restart function app
az functionapp restart --name azurepoc-function-app --resource-group azure-poc
```

### Terraform Issues
```bash
# Validate configuration
terraform validate

# Check current state
terraform show

# Force refresh
terraform refresh
```

### No Data in Dashboards
1. **Wait 5-15 minutes** for custom log tables to be created
2. **Generate test data**: `python quick_test.py`
3. **Check time range** in dashboard (last 24 hours)
4. **Verify function logs** for successful event processing

## URLs & Access Points

- **Function App**: https://azurepoc-function-app.azurewebsites.net
- **Azure Portal**: https://portal.azure.com
- **Log Analytics**: Portal → Log Analytics Workspaces → azurepoc-workspace
- **Dashboard**: Portal → Dashboards → azurepoc-api-dashboard

## Clean Up Resources
```bash
# Remove all resources
terraform destroy --auto-approve

# Or delete resource group
az group delete --name azure-poc --yes --no-wait
```

## Support
- 📖 **Full Documentation**: README.md
- 🧪 **Testing**: test_complete_pipeline.py
- 🔧 **Validation**: validate_deployment.py
- 🚀 **Automation**: deploy.ps1

---
**Total deployment time: ~5-10 minutes** ⏱️