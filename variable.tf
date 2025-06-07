variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "azure-poc"
}

variable "resource_group_location" {
  description = "Azure region in which to create the Resource Group"
  type        = string
  default     = "West Europe"
}

variable "storage_account_name" {
  description = "Storage Account name"
  type        = string
  default     = "azurepocstoragev1"
}

variable "service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
  default     = "azurepocserviceplan"
}

variable "log_analytics_workspace_name" {
  description = "Name of the Log Analytics Workspace"
  type        = string
  default     = "azurepoc-workspace"
}

variable "function_app_name" {
  description = "Name of the Function App"
  type        = string
  default     = "azurepoc-function-app"
}

variable "application_insights_name" {
  description = "Name of Application Insights"
  type        = string
  default     = "azurepoc-app-insights"
}

variable "dashboard_name" {
  description = "Name of the Azure Dashboard"
  type        = string
  default     = "azurepoc-api-dashboard"
}

variable "workbook_name" {
  description = "Name of the Azure Workbook"
  type        = string
  default     = "azurepoc-api-workbook"
}