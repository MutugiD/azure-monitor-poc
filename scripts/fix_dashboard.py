#!/usr/bin/env python3
"""
Dashboard Fix and Diagnostic Script
Checks Log Analytics data and provides instructions to fix dashboard issues
"""

import sys
import os
import time
import json
import subprocess
from datetime import datetime, timedelta

def run_azure_command(command):
    """Run an Azure CLI command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def check_log_analytics_data():
    """Check if data exists in Log Analytics"""
    print("🔍 Checking Log Analytics Data...")

    workspace_id = "7208379a-ae11-4c06-bb1c-a8fc4d0c34b4"

    # Check for any data in the last hour
    queries = [
        "search * | where TimeGenerated > ago(1h) | limit 5",
        "SalesforceEvent_CL | limit 5",
        "MuleSoftPerformance_CL | limit 5",
        "MuleSoftError_CL | limit 5",
        "MuleSoftUptime_CL | limit 5"
    ]

    results = {}

    for query in queries:
        print(f"   Testing query: {query}")
        command = f'az monitor log-analytics query --workspace {workspace_id} --analytics-query "{query}" --output json'
        success, output = run_azure_command(command)

        if success:
            try:
                data = json.loads(output)
                count = len(data.get('tables', [{}])[0].get('rows', []))
                results[query] = count
                print(f"   ✅ Found {count} records")
            except:
                results[query] = 0
                print(f"   ⚠️ No data or parsing error")
        else:
            results[query] = -1
            print(f"   ❌ Query failed: {output}")

    return results

def generate_dashboard_json():
    """Generate a working dashboard JSON configuration"""

    workspace_id = "7208379a-ae11-4c06-bb1c-a8fc4d0c34b4"

    dashboard_config = {
        "properties": {
            "lenses": [
                {
                    "order": 0,
                    "parts": [
                        {
                            "position": {"x": 0, "y": 0, "rowSpan": 4, "colSpan": 6},
                            "metadata": {
                                "inputs": [
                                    {
                                        "name": "resourceTypeMode",
                                        "isOptional": True
                                    },
                                    {
                                        "name": "ComponentId",
                                        "value": {
                                            "workspaceResourceId": f"/subscriptions/2610a706-cf3d-496e-9a5a-3173e855001e/resourceGroups/azure-poc/providers/Microsoft.OperationalInsights/workspaces/azurepoc-workspace"
                                        }
                                    },
                                    {
                                        "name": "Query",
                                        "value": f"""union
(SalesforceEvent_CL | where TimeGenerated > ago(24h) | where isnotempty(responseTime_d) | extend API_System = "Salesforce", ResponseTime = responseTime_d),
(MuleSoftPerformance_CL | where TimeGenerated > ago(24h) | where isnotempty(responseTime_d) | extend API_System = "MuleSoft", ResponseTime = responseTime_d)
| summarize AvgResponseTime = avg(ResponseTime) by API_System, bin(TimeGenerated, 1h)
| render timechart"""
                                    },
                                    {
                                        "name": "TimeRange",
                                        "value": "P1D"
                                    },
                                    {
                                        "name": "Dimensions",
                                        "value": {
                                            "xAxis": {
                                                "name": "TimeGenerated",
                                                "type": "datetime"
                                            },
                                            "yAxis": [
                                                {
                                                    "name": "AvgResponseTime",
                                                    "type": "long"
                                                }
                                            ],
                                            "splitBy": [
                                                {
                                                    "name": "API_System",
                                                    "type": "string"
                                                }
                                            ],
                                            "aggregation": "Average"
                                        }
                                    }
                                ],
                                "type": "Extension/Microsoft_OperationsManagementSuite/PartType/LogsDashboardPart",
                                "settings": {
                                    "content": {
                                        "Query": f"""union
(SalesforceEvent_CL | where TimeGenerated > ago(24h) | where isnotempty(responseTime_d) | extend API_System = "Salesforce", ResponseTime = responseTime_d),
(MuleSoftPerformance_CL | where TimeGenerated > ago(24h) | where isnotempty(responseTime_d) | extend API_System = "MuleSoft", ResponseTime = responseTime_d)
| summarize AvgResponseTime = avg(ResponseTime) by API_System, bin(TimeGenerated, 1h)
| render timechart""",
                                        "ControlType": "AnalyticsChart"
                                    }
                                }
                            }
                        },
                        {
                            "position": {"x": 6, "y": 0, "rowSpan": 4, "colSpan": 6},
                            "metadata": {
                                "inputs": [
                                    {
                                        "name": "resourceTypeMode",
                                        "isOptional": True
                                    },
                                    {
                                        "name": "ComponentId",
                                        "value": {
                                            "workspaceResourceId": f"/subscriptions/2610a706-cf3d-496e-9a5a-3173e855001e/resourceGroups/azure-poc/providers/Microsoft.OperationalInsights/workspaces/azurepoc-workspace"
                                        }
                                    },
                                    {
                                        "name": "Query",
                                        "value": f"""union
(SalesforceEvent_CL | where TimeGenerated > ago(24h) | extend API_System = "Salesforce", IsError = case(statusCode_d >= 400, 1, Success_b == false, 1, 0)),
(MuleSoftError_CL | where TimeGenerated > ago(24h) | extend API_System = "MuleSoft", IsError = 1),
(MuleSoftPerformance_CL | where TimeGenerated > ago(24h) | extend API_System = "MuleSoft", IsError = case(statusCode_d >= 400, 1, 0))
| summarize TotalRequests = count(), ErrorCount = sum(IsError), ErrorRate = (sum(IsError) * 100.0) / count() by API_System, bin(TimeGenerated, 1h)
| render timechart"""
                                    },
                                    {
                                        "name": "TimeRange",
                                        "value": "P1D"
                                    }
                                ],
                                "type": "Extension/Microsoft_OperationsManagementSuite/PartType/LogsDashboardPart",
                                "settings": {
                                    "content": {
                                        "Query": f"""union
(SalesforceEvent_CL | where TimeGenerated > ago(24h) | extend API_System = "Salesforce", IsError = case(statusCode_d >= 400, 1, Success_b == false, 1, 0)),
(MuleSoftError_CL | where TimeGenerated > ago(24h) | extend API_System = "MuleSoft", IsError = 1),
(MuleSoftPerformance_CL | where TimeGenerated > ago(24h) | extend API_System = "MuleSoft", IsError = case(statusCode_d >= 400, 1, 0))
| summarize TotalRequests = count(), ErrorCount = sum(IsError), ErrorRate = (sum(IsError) * 100.0) / count() by API_System, bin(TimeGenerated, 1h)
| render timechart""",
                                        "ControlType": "AnalyticsChart"
                                    }
                                }
                            }
                        }
                    ]
                }
            ],
            "metadata": {
                "model": {
                    "timeRange": {
                        "value": {
                            "relative": {
                                "duration": 24,
                                "timeUnit": 1
                            }
                        },
                        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
                    }
                }
            }
        },
        "location": "westeurope",
        "tags": {
            "hidden-title": "API Monitoring Dashboard"
        }
    }

    return dashboard_config

def main():
    """Main diagnostic and fix function"""
    print("🔧 Dashboard Fix and Diagnostic Tool")
    print("=" * 60)

    # Step 1: Check Log Analytics data
    data_results = check_log_analytics_data()

    print(f"\n📊 Data Analysis:")
    print("-" * 40)

    total_records = sum([count for count in data_results.values() if count > 0])

    if total_records > 0:
        print(f"✅ Found {total_records} total records in Log Analytics")
        print("✅ Data is flowing correctly")

        # Check specific table existence
        custom_tables = [q for q in data_results.keys() if "_CL" in q and data_results[q] > 0]
        if custom_tables:
            print(f"✅ Custom tables created: {len(custom_tables)}")
            for table in custom_tables:
                print(f"   - {table}: {data_results[table]} records")
        else:
            print("⚠️ Custom tables not yet visible (wait 5-15 minutes)")

    else:
        print("❌ No data found in Log Analytics")
        print("   - Events may still be processing (wait 5-15 minutes)")
        print("   - Run: python quick_test.py to generate test data")

    print(f"\n🎯 Dashboard Fix Instructions:")
    print("-" * 40)

    if total_records > 0:
        print("1. ✅ Data exists - Dashboard should work")
        print("2. 🔄 Refresh your browser and dashboard")
        print("3. ⏰ Wait 5-10 minutes for full data propagation")
        print("4. 🔍 Try these queries in Log Analytics:")
        print()
        print("   // Check recent data")
        print("   search * | where TimeGenerated > ago(1h) | summarize count() by Type")
        print()
        print("   // Response times")
        print("   union SalesforceEvent_CL, MuleSoftPerformance_CL")
        print("   | where isnotempty(responseTime_d)")
        print("   | summarize avg(responseTime_d) by SourceSystem_s")
        print()
        print("5. 📊 If dashboard still shows 'Not found':")
        print("   - Go to Azure Portal → Dashboards")
        print("   - Delete current dashboard")
        print("   - Create new dashboard manually with Log Analytics tiles")

    else:
        print("1. 📤 Generate test data first:")
        print("   python quick_test.py")
        print()
        print("2. ⏰ Wait 5-15 minutes for data ingestion")
        print()
        print("3. 🔍 Verify data with this query:")
        print("   search * | where TimeGenerated > ago(1h)")
        print()
        print("4. 🔄 Re-run this diagnostic script")

    print(f"\n🔗 Useful Links:")
    print("-" * 40)
    print("• Azure Portal: https://portal.azure.com")
    print("• Log Analytics: Portal → azurepoc-workspace → Logs")
    print("• Dashboards: Portal → Dashboard → azurepoc-api-dashboard")
    print("• Function App: Portal → azurepoc-function-app → Monitor")

    # Generate updated dashboard config for manual creation
    print(f"\n💾 Creating dashboard configuration...")
    config = generate_dashboard_json()

    with open("dashboard_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("✅ Dashboard configuration saved to: dashboard_config.json")
    print("   Use this if manual dashboard recreation is needed")

if __name__ == "__main__":
    main()