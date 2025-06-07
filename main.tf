terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "2610a706-cf3d-496e-9a5a-3173e855001e"
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.resource_group_location
}

resource "azurerm_storage_account" "poc" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.resource_group_location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Consumption‐tier Service Plan for Functions (updated from deprecated app_service_plan)
resource "azurerm_service_plan" "poc" {
  name                = var.service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  os_type  = "Linux"
  sku_name = "Y1"  # Consumption tier
}

# Log Analytics Workspace - Central log store
resource "azurerm_log_analytics_workspace" "poc" {
  name                = var.log_analytics_workspace_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Application Insights for Function telemetry
resource "azurerm_application_insights" "poc" {
  name                = var.application_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.poc.id
}

# Function App - Python-based HTTP endpoint
resource "azurerm_linux_function_app" "poc" {
  name                = var.function_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.poc.name
  storage_account_access_key = azurerm_storage_account.poc.primary_access_key
  service_plan_id            = azurerm_service_plan.poc.id

  site_config {
    application_stack {
      python_version = "3.9"
    }
    cors {
      allowed_origins = ["*"]
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"     = "python"
    "AzureWebJobsDashboard"        = azurerm_storage_account.poc.primary_connection_string
    "AzureWebJobsStorage"          = azurerm_storage_account.poc.primary_connection_string
    "WEBSITE_RUN_FROM_PACKAGE"     = "1"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.poc.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.poc.connection_string
    "LOG_ANALYTICS_WORKSPACE_ID"   = azurerm_log_analytics_workspace.poc.workspace_id
    "LOG_ANALYTICS_PRIMARY_KEY"    = azurerm_log_analytics_workspace.poc.primary_shared_key
  }

  identity {
    type = "SystemAssigned"
  }
}

# Output important values for use in Python functions and testing
output "function_app_default_hostname" {
  value = azurerm_linux_function_app.poc.default_hostname
  description = "Default hostname of the Function App"
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.poc.workspace_id
  description = "Log Analytics Workspace ID"
}

output "log_analytics_primary_key" {
  value = azurerm_log_analytics_workspace.poc.primary_shared_key
  sensitive = true
  description = "Log Analytics Primary Shared Key"
}

output "application_insights_instrumentation_key" {
  value = azurerm_application_insights.poc.instrumentation_key
  sensitive = true
  description = "Application Insights Instrumentation Key"
}

output "dashboard_id" {
  value = azurerm_portal_dashboard.api_dashboard.id
  description = "Azure Dashboard ID"
}

output "workbook_id" {
  value = azurerm_application_insights_workbook.api_workbook.id
  description = "Azure Workbook ID"
}

# Azure Portal Dashboard for API Metrics
resource "azurerm_portal_dashboard" "api_dashboard" {
  name                = var.dashboard_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  tags = {
    Purpose = "API Monitoring"
    Environment = "POC"
  }

  dashboard_properties = jsonencode({
    lenses = {
      "0" = {
        order = 0
        parts = {
          "0" = {
            position = {
              x = 0
              y = 0
              colSpan = 6
              rowSpan = 4
            }
            metadata = {
              inputs = [
                {
                  name = "resourceTypeMode"
                  isOptional = true
                },
                {
                  name = "ComponentId"
                  value = {
                    SubscriptionId = "2610a706-cf3d-496e-9a5a-3173e855001e"
                    ResourceGroup = azurerm_resource_group.main.name
                    Name = azurerm_log_analytics_workspace.poc.name
                    ResourceType = "Microsoft.OperationalInsights/workspaces"
                  }
                }
              ]
              type = "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart"
              settings = {
                content = {
                  Query = <<-EOT
                    // API Response Times - Key Metric 1
                    union SalesforceEvent_CL, MuleSoftPerformance_CL
                    | where TimeGenerated > ago(24h)
                    | where isnotempty(ResponseTime_d) or isnotempty(responseTime_d)
                    | extend ResponseTime = coalesce(ResponseTime_d, responseTime_d)
                    | extend API_System = case(
                        SourceSystem_s == "Salesforce" or contains(Type, "Salesforce"), "Salesforce",
                        SourceSystem_s == "MuleSoft" or contains(Type, "MuleSoft"), "MuleSoft",
                        "Other"
                    )
                    | summarize AvgResponseTime = avg(ResponseTime), MaxResponseTime = max(ResponseTime), Count = count() by API_System, bin(TimeGenerated, 1h)
                    | order by TimeGenerated desc
                  EOT
                  ControlType = "AnalyticsGrid"
                }
              }
            }
          }
          "1" = {
            position = {
              x = 6
              y = 0
              colSpan = 6
              rowSpan = 4
            }
            metadata = {
              inputs = [
                {
                  name = "resourceTypeMode"
                  isOptional = true
                },
                {
                  name = "ComponentId"
                  value = {
                    SubscriptionId = "2610a706-cf3d-496e-9a5a-3173e855001e"
                    ResourceGroup = azurerm_resource_group.main.name
                    Name = azurerm_log_analytics_workspace.poc.name
                    ResourceType = "Microsoft.OperationalInsights/workspaces"
                  }
                }
              ]
              type = "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart"
              settings = {
                content = {
                  Query = <<-EOT
                    // API Error Rates - Key Metric 2
                    union SalesforceEvent_CL, MuleSoftError_CL, MuleSoftPerformance_CL
                    | where TimeGenerated > ago(24h)
                    | extend API_System = case(
                        SourceSystem_s == "Salesforce" or contains(Type, "Salesforce"), "Salesforce",
                        SourceSystem_s == "MuleSoft" or contains(Type, "MuleSoft"), "MuleSoft",
                        "Other"
                    )
                    | extend IsError = case(
                        StatusCode_d >= 400, 1,
                        Success_b == false, 1,
                        contains(Type, "Error"), 1,
                        0
                    )
                    | summarize TotalRequests = count(), ErrorCount = sum(IsError), ErrorRate = (sum(IsError) * 100.0) / count() by API_System, bin(TimeGenerated, 1h)
                    | order by TimeGenerated desc
                  EOT
                  ControlType = "AnalyticsGrid"
                }
              }
            }
          }
        }
      }
    }
    metadata = {
      model = {
        timeRange = {
          value = {
            relative = {
              duration = 24
              timeUnit = 1
            }
          }
          type = "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
        }
        filterLocale = {
          value = "en-us"
        }
        filters = {
          value = {
            MsPortalFx_TimeRange = {
              model = {
                format = "utc"
                granularity = "auto"
                relative = "24h"
              }
              displayCache = {
                name = "UTC Time"
                value = "Past 24 hours"
              }
              filteredPartIds = [
                "StartboardPart-LogsDashboardPart-0",
                "StartboardPart-LogsDashboardPart-1"
              ]
            }
          }
        }
      }
    }
  })
}

# Generate UUID for workbook
resource "random_uuid" "workbook_id" {}

# Azure Workbook for Advanced API Analytics
resource "azurerm_application_insights_workbook" "api_workbook" {
  name                = random_uuid.workbook_id.result
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  display_name        = "API Monitoring Workbook"

  data_json = jsonencode({
    version = "Notebook/1.0"
    items = [
      {
        type = 9
        content = {
          version = "KqlParameterItem/1.0"
          parameters = [
            {
              id = "timeRange"
              version = "KqlParameterItem/1.0"
              name = "TimeRange"
              type = 4
              isRequired = true
              value = {
                durationMs = 86400000
              }
              typeSettings = {
                selectableValues = [
                  {
                    durationMs = 3600000
                    displayName = "Last hour"
                  },
                  {
                    durationMs = 14400000
                    displayName = "Last 4 hours"
                  },
                  {
                    durationMs = 43200000
                    displayName = "Last 12 hours"
                  },
                  {
                    durationMs = 86400000
                    displayName = "Last 24 hours"
                  }
                ]
              }
            }
          ]
        }
      },
      {
        type = 3
        content = {
          version = "KqlItem/1.0"
          query = <<-EOT
            // API Response Time Trends
            union SalesforceEvent_CL, MuleSoftPerformance_CL
            | where TimeGenerated {TimeRange}
            | where isnotempty(ResponseTime_d) or isnotempty(responseTime_d)
            | extend ResponseTime = coalesce(ResponseTime_d, responseTime_d)
            | extend API_System = case(
                SourceSystem_s == "Salesforce" or contains(Type, "Salesforce"), "Salesforce",
                SourceSystem_s == "MuleSoft" or contains(Type, "MuleSoft"), "MuleSoft",
                "Other"
            )
            | summarize AvgResponseTime = avg(ResponseTime) by API_System, bin(TimeGenerated, 5m)
            | render timechart
          EOT
          size = 1
          title = "API Response Time Trends (Key Metric 1)"
          timeContext = {
            durationMs = 86400000
          }
          queryType = 0
          resourceType = "microsoft.operationalinsights/workspaces"
        }
      },
      {
        type = 3
        content = {
          version = "KqlItem/1.0"
          query = <<-EOT
            // API Error Rate Analysis
            union SalesforceEvent_CL, MuleSoftError_CL, MuleSoftPerformance_CL
            | where TimeGenerated {TimeRange}
            | extend API_System = case(
                SourceSystem_s == "Salesforce" or contains(Type, "Salesforce"), "Salesforce",
                SourceSystem_s == "MuleSoft" or contains(Type, "MuleSoft"), "MuleSoft",
                "Other"
            )
            | extend IsError = case(
                StatusCode_d >= 400, 1,
                Success_b == false, 1,
                contains(Type, "Error"), 1,
                0
            )
            | summarize TotalRequests = count(), ErrorCount = sum(IsError), ErrorRate = (sum(IsError) * 100.0) / count() by API_System, bin(TimeGenerated, 5m)
            | render timechart
          EOT
          size = 1
          title = "API Error Rate Analysis (Key Metric 2)"
          timeContext = {
            durationMs = 86400000
          }
          queryType = 0
          resourceType = "microsoft.operationalinsights/workspaces"
        }
      }
    ]
    styleSettings = {}
    "$schema" = "https://github.com/Microsoft/Application-Insights-Workbooks/blob/master/schema/workbook.json"
  })

  tags = {
    Purpose = "API Analytics"
    Environment = "POC"
  }
}