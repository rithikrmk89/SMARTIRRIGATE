# SmartIrrigate Cloud: Microsoft Azure Cloud Deployment & DevOps Guide

This guide covers deployment procedures for Microsoft Azure Cloud services (Azure Blob Storage, Azure Functions, Azure Machine Learning, Managed Identity/RBAC, Power BI), Docker multi-container setups, and CI/CD pipelines.

---

## 1. Local Development Mode (Default & Zero Cloud Cost)

SmartIrrigate Cloud is configured by default to run in **Local Development Mode**:
- SQLite database (`smartirrigate.db`) stores metadata and prediction audit records.
- Local filesystem storage (`backend/data_storage/`) stores raw uploads, processed datasets, and model artefacts.
- **Zero Azure account credentials or cloud subscription costs are required.**

---

## 2. Microsoft Azure Production Deployment Architecture

When transitioning from local testing to Microsoft Azure Cloud, set `AZURE_STORAGE_ENABLED=true` in your `.env` file.

```
+-----------------------------------------------------------------------------------+
|                               Microsoft Azure Cloud                               |
|                                                                                   |
|  +---------------------------+     Blob Trigger      +-------------------------+  |
|  | Azure Blob Storage:       | --------------------> | Azure Functions: ETL    |  |
|  | smartirrigate-raw-data    |                       | (Python v2 App Model)   |  |
|  +---------------------------+                       +-------------------------+  |
|                                                                    |              |
|                                                                    v              |
|  +---------------------------+     Training Input    +-------------------------+  |
|  | Azure Machine Learning    | <-------------------- | Azure Blob Storage:     |  |
|  | (AML Command Job)         |                       | smartirrigate-processed |  |
|  +---------------------------+                       +-------------------------+  |
|            |                                                                      |
|            v                                                                      |
|  +---------------------------+     Model Loading     +-------------------------+  |
|  | Azure Blob Storage:       | --------------------> | Azure Container Apps /  |  |
|  | smartirrigate-models      |                       | App Service (FastAPI)   |  |
|  +---------------------------+                       +-------------------------+  |
|                                                                    |              |
|                                                                    v              |
|                                                      +-------------------------+  |
|                                                      | Azure Static Web Apps / |  |
|                                                      | Front Door (React UI)   |  |
|                                                      +-------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Azure Cloud Provisioning

### Step 3.1: Automated Provisioning via Terraform (Recommended)
Prerequisites: Install [Terraform](https://www.terraform.io/) and authenticate with Azure CLI (`az login`).

```bash
cd cloud/terraform_azure
terraform init
terraform plan
terraform apply -auto-approve
```
Terraform automatically provisions:
- Azure Resource Group (`smartirrigate-rg`).
- Azure Storage Account with TLS 1.2 and disabled public blob access.
- Private Blob Containers: `smartirrigate-raw-data`, `smartirrigate-processed`, and `smartirrigate-models`.
- Log Analytics Workspace & Application Insights.
- Linux Consumption Service Plan and Azure Function App (`smartirrigate-etl-func`).
- Azure Key Vault and Azure Machine Learning Workspace (`smartirrigate-aml`).

### Step 3.2: Automated Provisioning via Azure Bicep (Alternative)
```bash
az group create --name smartirrigate-rg --location eastus
az deployment group create \
  --resource-group smartirrigate-rg \
  --template-file cloud/bicep/main.bicep
```

### Step 3.3: Manual Azure CLI Setup (Step-by-Step)
```bash
# Set variables
export LOCATION="eastus"
export RG="smartirrigate-rg"
export STORAGE_NAME="smartirrigatestore$RANDOM"

# 1. Create Resource Group
az group create --name $RG --location $LOCATION

# 2. Create Storage Account
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RG \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# 3. Retrieve connection string
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_NAME \
  --resource-group $RG \
  --output tsv)

# 4. Create Blob Containers
az storage container create --name smartirrigate-raw-data --connection-string $AZURE_STORAGE_CONNECTION_STRING
az storage container create --name smartirrigate-processed --connection-string $AZURE_STORAGE_CONNECTION_STRING
az storage container create --name smartirrigate-models --connection-string $AZURE_STORAGE_CONNECTION_STRING
```

### Step 3.4: Azure Functions Serverless Data Processor Setup
1. Navigate to the function directory:
   ```bash
   cd cloud/azure_functions
   ```
2. Deploy directly to your Azure Function App:
   ```bash
   func azure functionapp publish smartirrigate-func-app
   ```
   *The function automatically activates a Blob Trigger on container `smartirrigate-raw-data/{name}.csv` and writes cleaned, imputed records to `smartirrigate-processed`.*

### Step 3.5: Azure Machine Learning Training Execution
To trigger managed cloud model training on an Azure ML compute cluster:
```bash
export AZURE_SUBSCRIPTION_ID="your-azure-subscription-id"
export AZURE_RESOURCE_GROUP="smartirrigate-rg"
export AZURE_ML_WORKSPACE_NAME="smartirrigate-aml"

python cloud/azure_ml/aml_job_launcher.py
```

### Step 3.6: Microsoft Power BI Cloud Dashboard Integration (Optional)
If your organization utilizes Microsoft Power BI:
1. In Power BI Desktop, select **Get Data** $\rightarrow$ **Azure** $\rightarrow$ **Azure Blob Storage**.
2. Connect using your storage account name and key or Azure AD credentials.
3. Import the `smartirrigate-processed` dataset to build regional watershed reports.
4. Publish the report to Power BI Service, generate an Embed URL, and paste it into `AZURE_POWERBI_DASHBOARD_URL` in `.env`.
5. *If Power BI is not configured, the in-app interactive Recharts dashboard serves as the operational dashboard.*

---

## 4. Docker Multi-Container Deployment

SmartIrrigate includes Dockerfiles and a Docker Compose file for local or containerized production deployment:

```bash
# Build and launch both backend and frontend containers
docker compose up --build -d

# Check service status
docker compose ps

# View container logs
docker compose logs -f
```
- **Frontend Container:** Accessible on `http://localhost:3000`
- **Backend API:** Accessible on `http://localhost:8000` (Swagger docs on `http://localhost:8000/docs`)

---

## 5. Security & RBAC Least-Privilege Guidance

1. **Secret Isolation:** Never commit `.env` containing Azure storage keys or connection strings.
2. **Managed Identities (Recommended for Azure):** In production Azure Container Apps or VMs, use **System-Assigned Managed Identity** with the `Storage Blob Data Contributor` role rather than raw account keys.
3. **Network Isolation:** Enable Azure Storage firewall rules to restrict traffic to designated virtual networks and Azure services.
4. **CORS Restrictions:** Configure `CORS_ORIGINS` to allow only your frontend origin domain.
