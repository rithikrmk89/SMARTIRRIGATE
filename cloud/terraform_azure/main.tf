terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

provider "azurerm" {
  features {}
}

# -------------------------------------------------------------
# 1. Resource Group
# -------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.azure_location

  tags = {
    Project     = "SmartIrrigateCloud"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# -------------------------------------------------------------
# 2. Azure Storage Account & Containers
# -------------------------------------------------------------
resource "azurerm_storage_account" "sa" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = azurerm_resource_group.rg.tags
}

resource "azurerm_storage_container" "raw" {
  name                  = "smartirrigate-raw-data"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "processed" {
  name                  = "smartirrigate-processed"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "models" {
  name                  = "smartirrigate-models"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

# -------------------------------------------------------------
# 3. Azure Application Insights & Log Analytics
# -------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "smartirrigate-law"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "appinsights" {
  name                = "smartirrigate-appinsights"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.logs.id
  application_type    = "web"
}

# -------------------------------------------------------------
# 4. Azure Function App (Linux Consumption for Serverless ETL)
# -------------------------------------------------------------
resource "azurerm_service_plan" "asp" {
  name                = "smartirrigate-asp"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption
}

resource "azurerm_linux_function_app" "etl_func" {
  name                = "smartirrigate-etl-func"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id

  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.appinsights.instrumentation_key
    "AZURE_PROCESSED_CONTAINER"      = azurerm_storage_container.processed.name
    "AzureWebJobsStorage"            = azurerm_storage_account.sa.primary_connection_string
  }

  tags = azurerm_resource_group.rg.tags
}

# -------------------------------------------------------------
# 5. Azure Machine Learning Workspace
# -------------------------------------------------------------
resource "azurerm_key_vault" "kv" {
  name                = "smartirrigate-kv-01"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

data "azurerm_client_config" "current" {}

resource "azurerm_machine_learning_workspace" "aml" {
  name                    = "smartirrigate-aml"
  location                = azurerm_resource_group.rg.location
  resource_group_name     = azurerm_resource_group.rg.name
  application_insights_id = azurerm_application_insights.appinsights.id
  key_vault_id            = azurerm_key_vault.kv.id
  storage_account_id      = azurerm_storage_account.sa.id

  identity {
    type = "SystemAssigned"
  }

  tags = azurerm_resource_group.rg.tags
}
