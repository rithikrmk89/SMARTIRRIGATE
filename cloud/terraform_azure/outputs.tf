output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.rg.name
}

output "storage_account_name" {
  description = "Azure Storage Account Name"
  value       = azurerm_storage_account.sa.name
}

output "raw_container_name" {
  description = "Raw Data Blob Container"
  value       = azurerm_storage_container.raw.name
}

output "processed_container_name" {
  description = "Processed Data Blob Container"
  value       = azurerm_storage_container.processed.name
}

output "models_container_name" {
  description = "Models Artefact Blob Container"
  value       = azurerm_storage_container.models.name
}

output "function_app_name" {
  description = "Azure Function App Name"
  value       = azurerm_linux_function_app.etl_func.name
}

output "machine_learning_workspace_name" {
  description = "Azure Machine Learning Workspace Name"
  value       = azurerm_machine_learning_workspace.aml.name
}
