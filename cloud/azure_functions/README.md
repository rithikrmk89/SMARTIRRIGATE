# Azure Functions Serverless Data Processor for SmartIrrigate Cloud

## Overview
This serverless function processes agricultural datasets uploaded to an **Azure Blob Storage** raw container (`smartirrigate-raw-data`). It:
1. Normalizes column names to standard agro-meteorological snake_case.
2. Imputes missing numerical sensor values with column medians.
3. Imputes missing categorical values with modes.
4. Outputs cleaned CSV records directly to the Azure Blob `smartirrigate-processed` container.
5. Employs the Azure Functions v2 Python programming model.

## Local Testing with Azure Functions Core Tools

```bash
cd cloud/azure_functions

# Install Azure Functions Core Tools (if not already installed)
# npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Start function locally
func start
```

## Deployment to Microsoft Azure

```bash
# 1. Login to Azure CLI
az login

# 2. Create Azure Function App (Linux Consumption plan)
az functionapp create \
  --resource-group smartirrigate-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name smartirrigate-func-app \
  --storage-account smartirrigatestore

# 3. Deploy code
func azure functionapp publish smartirrigate-func-app
```
