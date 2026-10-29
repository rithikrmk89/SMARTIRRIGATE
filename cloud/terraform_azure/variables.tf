variable "azure_location" {
  description = "Target Azure Region"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = "smartirrigate-rg"
}

variable "storage_account_name" {
  description = "Globally unique Azure Storage Account name (lowercase, alphanumeric, 3-24 chars)"
  type        = string
  default     = "smartirrigatestore"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}
