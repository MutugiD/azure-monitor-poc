# 🛠️ Dashboard Fix Guide - "Not Found" Error Solution

## 🎯 Problem Diagnosis

Your dashboard shows "Not found" with 404 errors because:

1. **Custom log tables take 5-15 minutes** to appear after first data ingestion
2. **Dashboard queries** may be referencing tables that don't exist yet
3. **Terraform dashboard configuration** might need updates

## ✅ Immediate Solution Steps

### 1. Verify Data is Flowing (5 minutes)

Go to **Azure Portal** → **Log Analytics workspaces** → **azurepoc-workspace** → **Logs**

Run these queries to check data:

```kql
// Check if ANY data exists
search *
| where TimeGenerated > ago(1h)
| take 10
```

```kql
// Check specific tables (may fail if tables don't exist yet)
union isfuzzy=true
    SalesforceEvent_CL,
    MuleSoftPerformance_CL,
    MuleSoftError_CL,
    MuleSoftUptime_CL
| where TimeGenerated > ago(1h)
| summarize count() by Type
```

### 2. Wait for Custom Tables (5-15 minutes)

Custom log tables (`*_CL`) take time to appear. **This is normal behavior.**

- First data ingestion: 5-15 minutes
- Subsequent data: 1-5 minutes

### 3. Manual Dashboard Creation (Immediate Fix)

If waiting doesn't work, create dashboard manually:

#### A. Delete Current Dashboard
1. Go to **Azure Portal** → **Dashboards**
2. Find `azurepoc-api-dashboard`
3. Click **Delete**

#### B. Create New Dashboard
1. Click **+ Create** → **Custom dashboard**
2. Name it: `API Monitoring Dashboard`
3. Click **Save and publish**

#### C. Add Response Time Tile
1. Click **Edit** on your new dashboard
2. Click **+ Add tile**
3. Choose **Logs** tile
4. Select workspace: `azurepoc-workspace`
5. Enter this query:

```kql
union isfuzzy=true
    (SalesforceEvent_CL
     | where TimeGenerated > ago(24h)
     | where isnotempty(responseTime_d)
     | extend API_System = "Salesforce", ResponseTime = responseTime_d),
    (MuleSoftPerformance_CL
     | where TimeGenerated > ago(24h)
     | where isnotempty(responseTime_d)
     | extend API_System = "MuleSoft", ResponseTime = responseTime_d)
| summarize AvgResponseTime = avg(ResponseTime) by API_System, bin(TimeGenerated, 1h)
| render timechart
```

6. Set **Title**: `API Response Times`
7. Click **Apply**

#### D. Add Error Rate Tile
1. Click **+ Add tile** again
2. Choose **Logs** tile
3. Select workspace: `azurepoc-workspace`
4. Enter this query:

```kql
union isfuzzy=true
    (SalesforceEvent_CL
     | where TimeGenerated > ago(24h)
     | extend API_System = "Salesforce",
              IsError = case(statusCode_d >= 400, 1, Success_b == false, 1, 0)),
    (MuleSoftError_CL
     | where TimeGenerated > ago(24h)
     | extend API_System = "MuleSoft", IsError = 1),
    (MuleSoftPerformance_CL
     | where TimeGenerated > ago(24h)
     | extend API_System = "MuleSoft",
              IsError = case(statusCode_d >= 400, 1, 0))
| summarize TotalRequests = count(),
           ErrorCount = sum(IsError),
           ErrorRate = (sum(IsError) * 100.0) / count()
  by API_System, bin(TimeGenerated, 1h)
| render timechart
```

5. Set **Title**: `API Error Rates`
6. Click **Apply**
7. Click **Save** to save dashboard

## 🧪 Test Data Generation

If no data appears, generate test data:

```bash
# Quick test
python quick_test.py

# Comprehensive dashboard data
python generate_dashboard_data.py
```

## 🔍 Troubleshooting Queries

### Check Table Existence
```kql
// List all custom tables
search *
| distinct Type
| where Type endswith "_CL"
```

### Verify Recent Data
```kql
// Check data from last hour
search *
| where TimeGenerated > ago(1h)
| summarize count() by Type, bin(TimeGenerated, 10m)
| render timechart
```

### Response Time Analysis
```kql
// Test response time data
union isfuzzy=true SalesforceEvent_CL, MuleSoftPerformance_CL
| where TimeGenerated > ago(24h)
| where isnotempty(responseTime_d)
| extend API_System = case(
    SourceSystem_s == "Salesforce", "Salesforce",
    SourceSystem_s == "MuleSoft", "MuleSoft",
    "Other"
)
| summarize
    AvgResponseTime = avg(responseTime_d),
    MaxResponseTime = max(responseTime_d),
    Count = count()
  by API_System
```

### Error Rate Analysis
```kql
// Test error rate data
union isfuzzy=true
    SalesforceEvent_CL,
    MuleSoftPerformance_CL,
    MuleSoftError_CL
| where TimeGenerated > ago(24h)
| extend API_System = case(
    SourceSystem_s == "Salesforce", "Salesforce",
    SourceSystem_s == "MuleSoft", "MuleSoft",
    "Other"
)
| extend IsError = case(
    statusCode_d >= 400, 1,
    Success_b == false, 1,
    Type == "MuleSoftError_CL", 1,
    0
)
| summarize
    TotalRequests = count(),
    ErrorCount = sum(IsError),
    ErrorRate = (sum(IsError) * 100.0) / count()
  by API_System
```

## ⏰ Expected Timeline

| Time | Expected Behavior |
|------|------------------|
| 0-5 min | Functions receive data (✅ working) |
| 5-15 min | Custom tables appear in Log Analytics |
| 15-20 min | Dashboard queries start working |
| 20+ min | Full dashboard functionality |

## 🚨 If Still Not Working

1. **Check Function Logs**:
   ```bash
   az functionapp log tail --name azurepoc-function-app --resource-group azure-poc
   ```

2. **Verify Log Analytics Connection**:
   - Portal → Function App → Configuration → App Settings
   - Check `LOG_ANALYTICS_WORKSPACE_ID` and `LOG_ANALYTICS_PRIMARY_KEY`

3. **Regenerate Dashboard**:
   ```bash
   terraform apply --auto-approve
   ```

4. **Manual Dashboard Creation** (as described above)

## 📞 Quick Commands

```bash
# Test all endpoints
python validate_deployment.py

# Generate dashboard test data
python generate_dashboard_data.py

# Run comprehensive tests
python test_complete_pipeline.py
```

---

**🔑 Key Point**: The "Not found" error is typically a **timing issue**. Custom log tables need 5-15 minutes to appear after first data ingestion. Wait, then refresh your dashboard!