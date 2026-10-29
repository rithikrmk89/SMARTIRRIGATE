# Azure Machine Learning (Azure ML) Integration for SmartIrrigate Cloud

## Overview
SmartIrrigate Cloud supports managed model training using **Azure Machine Learning**:
- Training pipeline runs on an Azure ML compute cluster (e.g. `Standard_DS3_v2` or `Standard_D2s_v3`).
- Tracks experiments and evaluation metrics (`MAE`, `RMSE`, `$R^2$`) automatically via Azure ML MLflow integration.
- Registers model artefacts (`model.joblib`) into the Azure ML Model Registry.

## Prerequisites
1. Azure CLI installed: `az login`
2. Azure ML Workspace provisioned (via Terraform or Azure Portal).
3. Compute cluster created in the workspace (default name: `cpu-cluster`).

## Submitting a Training Job
```bash
# Set your Azure Subscription ID
export AZURE_SUBSCRIPTION_ID="your-azure-subscription-id"
export AZURE_RESOURCE_GROUP="smartirrigate-rg"
export AZURE_ML_WORKSPACE_NAME="smartirrigate-aml"

# Run the launcher
python cloud/azure_ml/aml_job_launcher.py
```
