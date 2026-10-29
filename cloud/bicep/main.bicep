@description('Location for all resources.')
param location string = resourceGroup().location

@description('Storage Account Name (3-24 lowercase letters/numbers)')
param storageAccountName string = 'smartirrigate${uniqueString(resourceGroup().id)}'

@description('Environment name tag')
param environment string = 'production'

// 1. Azure Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
  tags: {
    Project: 'SmartIrrigateCloud'
    Environment: environment
  }
}

// Blob Service & Containers
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'smartirrigate-raw-data'
  properties: {
    publicAccess: 'None'
  }
}

resource processedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'smartirrigate-processed'
  properties: {
    publicAccess: 'None'
  }
}

resource modelsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'smartirrigate-models'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountId string = storageAccount.id
output storageAccountNameOutput string = storageAccount.name
output rawContainerOutput string = rawContainer.name
output processedContainerOutput string = processedContainer.name
output modelsContainerOutput string = modelsContainer.name
