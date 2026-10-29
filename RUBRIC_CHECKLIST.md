# Evaluation Rubric Checklist: Cloud Computing for Data Analytics
**Project Name:** SmartIrrigate Cloud — Cloud-Based Smart Irrigation & Water Demand Prediction System  
**Total Marks:** 40 Marks  
**Audit Date:** Current Session  

---

## Rubric Breakdown & Implementation Status Matrix

| Rubric Item | Marks | Current Status | Relevant Files in Repository | Implementation Reality | Evidence Still Needed |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **1. Problem Statement & Dataset Evaluation with Cloud Storage and Visualization** | **5** | **Partially Complete** (2.5/5) | • `REPORT.md`<br>• `DATASET.md`<br>• `backend/app/services/storage.py`<br>• `frontend/src/pages/DatasetsPage.tsx` | • Problem statement & FAO-56 agtech formulation are fully documented and implemented.<br>• Dataset schema validation, statistics, and preview rows are live in UI.<br>• **Storage:** Cloud adapter code exists for Azure Blob & S3, but system currently runs on **local disk fallback** (`AZURE_STORAGE_ENABLED=false`).<br>• **Visualization:** Visualizations exist in-app (Recharts), but **managed cloud BI tool** (Looker Studio / QuickSight / Azure Data Studio) is merely documented. | 1. Upload dataset to a live cloud bucket (e.g., AWS S3 Free Tier or Supabase S3-compatible).<br>2. Build and link a live **Google Looker Studio** or **Power BI** public dashboard with interactive charts and embed URL. |
| **2. Cloud Architecture & Pipeline Implementation** | **10** | **Substantially Complete** (7/10) | • `backend/Dockerfile`<br>• `frontend/Dockerfile`<br>• `docker-compose.yml`<br>• `cloud/lambda/data_processor.py`<br>• `cloud/azure_functions/`<br>• `.github/workflows/ci.yml`<br>• `.github/workflows/deploy.yml` | • **Docker:** Dockerfiles & Compose configured; cross-platform path resolution and volume persistence fixed.<br>• **Serverless:** Complete AWS Lambda function (`data_processor.py`) & Azure Function v2 scripted for object-created trigger ETL.<br>• **ETL:** Data pipeline cleans, validates, and imputes data.<br>• **CI/CD:** GitHub Actions CI workflow runs pytest (10 tests), frontend build (tsc + Vite), and docker compose validation. | 1. Execute local Docker Desktop multi-container build and capture container health check logs.<br>2. Deploy/test the serverless ETL function with an event payload to demonstrate automated data transformation. |
| **3. Result Analysis & Display using a Managed Cloud ML / Analytics Service** | **5** | **Merely Scripted** (1.5/5) | • `cloud/sagemaker/`<br>• `cloud/azure_ml/`<br>• `backend/app/services/ml_service.py`<br>• `MODEL_REPORT.md` | • App currently trains Scikit-Learn Random Forest Regressor locally on CPU inside FastAPI.<br>• Scripts for AWS SageMaker (`sagemaker_launcher.py`) and Azure ML (`aml_job_launcher.py`) exist in repository but have not executed on cloud compute. | 1. Execute model training or inference on a zero/low-cost managed cloud ML service (e.g., **Google BigQuery ML** or **AWS SageMaker Free Tier**).<br>2. Export genuine execution run logs and evaluation metrics ($R^2$, MAE, RMSE) from the managed service. |
| **4. Project Report** | **5** | **Complete** (4.5/5) | • `REPORT.md`<br>• `ARCHITECTURE.md`<br>• `DEPLOYMENT.md` | • Comprehensive academic report with Abstract, Problem Statement, Math (FAO-56 Penman-Monteith), Comparison Matrix, and Architecture diagrams. | 1. Synchronize report with Render deployment URLs, Docker execution outputs, and cloud storage/visualization links. |
| **5. Online Certification Completion** | **15** | **Pending Student Action** (0/15) | • External credential | • Requires genuine completed certification in Cloud Computing / Data Analytics (e.g., AWS Cloud Practitioner, Azure Fundamentals AZ-900, GCP Digital Leader, or Coursera/NPTEL equivalent). | 1. User must provide genuine certificate PDF/credential link and ID. *(Agent will never fabricate or fake this credential).* |
| **TOTAL** | **40** | **Current Assessed Score: 15.5 / 40** (Excluding Certification) | | | **Target: 40 / 40** |

---

## Detailed Gap Analysis & Action Plan

### Gap 1: Cloud Storage & Cloud Visualization (Rubric 1 — 5 Marks)
- **Current State:** Datasets stored in local `backend/data_storage/processed/`. Frontend displays Recharts.
- **Rubric Requirement:** Cloud storage (AWS S3, Azure Blob, or GCP Storage) + Cloud BI visualization (Looker Studio, QuickSight, Azure Data Studio).
- **Practical Low-Cost Solution:**
  1. **Google Looker Studio (100% Free):** Connect directly to the FAO-56 benchmark dataset (via Google Sheets or CSV on Google Drive) and create interactive watershed & water demand visualizations (gauges, crop demand bar charts, soil moisture vs evapotranspiration scatter plots).
  2. **AWS S3 Free Tier (or Cloudflare R2 / Supabase S3):** Upload raw and processed datasets to an S3 bucket with public-read or presigned access.

### Gap 2: Serverless Function Deployment & Evidence (Rubric 2 — 10 Marks)
- **Current State:** `cloud/lambda/data_processor.py` has complete event-driven code for `s3:ObjectCreated`, but is only stored as a local script.
- **Rubric Requirement:** Actual serverless function execution and ETL demonstration.
- **Practical Low-Cost Solution:**
  1. Package and deploy to AWS Lambda (1 million free requests/month on AWS Free Tier) or GCP Cloud Functions (2 million free invocations/month).
  2. Trigger Lambda with a test S3 event or upload, showing raw CSV transformed into cleaned CSV in the processed destination.
  3. Include execution logs and CloudWatch/Cloud Logging screenshots.

### Gap 3: Managed Cloud ML Service Evidence (Rubric 3 — 5 Marks)
- **Current State:** Model trains via local `scikit-learn` in FastAPI.
- **Rubric Requirement:** SageMaker / BigQuery ML / Google AutoML / Azure ML Studio.
- **Practical Low-Cost Solution:**
  1. **Google BigQuery ML (Free Tier — 10GB storage, 1TB query/month free):** Train a `LINEAR_REG` or `BOOSTED_TREE_REGRESSOR` model directly on BigQuery using SQL (`CREATE OR REPLACE MODEL ...`).
  2. Extract genuine evaluation metrics from `ML.EVALUATE()` and display them on the dashboard alongside the local Random Forest model.
  3. This gives 100% compliant, verifiable cloud ML evidence with zero credit card billing risk.

### Gap 4: Production Docker Containerization & Render Deployment (Rubric 2 — 10 Marks)
- **Current State:** Dockerfiles exist, but required portability fixes (resolving Windows vs Linux file paths, SQLite persistence). Docker Desktop needs to be running.
- **Action:**
  1. Implement robust path resolution in `backend/app/config.py`, `backend/app/services/ml_service.py`, `backend/app/routers/datasets.py`, and `backend/app/routers/models.py`.
  2. Configure environment-variable based API URL in frontend (`VITE_API_BASE_URL`).
  3. Build and test Docker containers locally.
  4. Prepare Render deployment specification (`render.yaml` or Web Service + Static Site).
