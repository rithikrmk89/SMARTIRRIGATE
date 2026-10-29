# SmartIrrigate Cloud: System Architecture (Microsoft Azure Cloud)

SmartIrrigate Cloud is an end-to-end cloud-native smart irrigation and crop water demand estimation platform designed to eliminate water wastage and optimize agricultural scheduling.

---

## 1. High-Level Architecture Diagram (Microsoft Azure Cloud)

```mermaid
graph TD
    subgraph Data Sources & Ingestion
        A[Agricultural Weather Records / IoT Sensors / CSV Uploads] -->|HTTP Multipart / API| B(FastAPI Ingestion Endpoint)
        A -->|Azure Storage Explorer / azcopy| C[(Azure Blob: smartirrigate-raw-data)]
    end

    subgraph Data Validation & Serverless ETL
        C -->|BlobTrigger Event| D[Azure Functions: Data Processor]
        B -->|Local Pipeline| E[Pandas Data Pipeline Service]
        D -->|Cleaned & Imputed CSV| F[(Azure Blob: smartirrigate-processed)]
        E -->|Cleaned Records| G[(SQLite / Azure Database for PostgreSQL)]
    end

    subgraph Machine Learning Lifecycle
        F -->|Training Input URI| H[Azure Machine Learning: Compute Cluster]
        G -->|Local Data Split 80/20| I[Scikit-Learn Training Engine]
        H -->|Saved Artefact & MLflow| J[(Azure Blob: smartirrigate-models)]
        I -->|joblib Artefact| K[Local Models Storage]
    end

    subgraph Prediction Service & Advisory Engine
        K -->|Active Model Loaded| L[FastAPI Prediction Service]
        J -->|Cloud Model Loaded| L
        L --> M[Volumetric Calculator: Area ha to m³ & Liters]
        L --> N[Agronomic Advisory Engine: Timing & Weather Alerts]
        L --> O[Feature Importance Explainability]
    end

    subgraph Presentation & Client Dashboard
        L -->|REST JSON API / OpenAPI| P[React 19 Vite Dashboard]
        F -.->|Optional Cloud BI| Q[Microsoft Power BI Dashboard]
    end
```

---

## 2. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as Agronomist / Farmer
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant Pipe as Data Pipeline
    participant ML as ML Service (Random Forest)
    participant DB as SQLite / Azure DB
    participant Cloud as Azure Blob / Functions / Azure ML

    Farmer->>UI: Uploads CSV Dataset or Requests Demo Benchmark
    UI->>API: POST /api/datasets/upload or /generate-sample
    API->>Pipe: Validate schema, impute missing values, compute summary stats
    Pipe->>DB: Store Dataset Metadata & Processed Records
    opt Azure Storage Enabled
        Pipe->>Cloud: Upload to Azure Blob Raw / Processed Container
    end
    API-->>UI: Return Dataset Preview & Summary

    Farmer->>UI: Triggers Model Training (80/20 Test Split)
    UI->>API: POST /api/models/train
    API->>ML: Fit Baseline (Linear) & Random Forest Regressors
    ML->>ML: Evaluate MAE, RMSE, R² on held-out test split
    ML->>DB: Save Model Record & Set Active
    API-->>UI: Return Genuine Performance Metrics & Feature Weights

    Farmer->>UI: Inputs Field Crop, Soil, Temperature, Humidity, Area
    UI->>API: POST /api/predictions/predict
    API->>ML: Run Inference with Active Pipeline
    ML->>API: Output mm/day + Field Volume (m³ & L) + Advisory
    API->>DB: Log Prediction to History
    API-->>UI: Return Forecast, Water Schedule, and Feature Weights
    UI-->>Farmer: Displays Water Depth, Total Volume, and Irrigation Schedule
```

---

## 3. Component Responsibilities

| Component | Technology | Primary Responsibility | Fallback / Local Mode |
| :--- | :--- | :--- | :--- |
| **Frontend Dashboard** | React 19, Vite, TypeScript, Tailwind CSS, Recharts | Interactive UI for irrigation prediction, file uploads, metric visualization, and history export. | Runs locally via Vite (`http://localhost:5173`). |
| **Backend REST API** | Python 3.11/3.13, FastAPI, Uvicorn, Pydantic v2 | Input validation, REST routing, CORS management, error handling, and Swagger docs (`/docs`). | Runs locally via Uvicorn (`http://localhost:8000`). |
| **Data Ingestion Pipeline** | Pandas, NumPy | Schema normalization, missing value imputation (median/mode), duplicate handling, outlier protection. | In-process execution within FastAPI server. |
| **Machine Learning Engine** | Scikit-Learn, Joblib | 80/20 train/test split, baseline comparison (Linear Regression), Random Forest training, test MAE/RMSE/R² calculation. | Local CPU parallelization (`n_jobs=-1`). |
| **Storage Adapter** | Azure Storage Blob SDK / Local FileSystem | Dual-mode storage: stores files locally or mirrors to Azure Blob raw, processed, and model containers. | Seamless fallback to `backend/data_storage/` when Azure is disabled. |
| **Database** | SQLAlchemy, SQLite | Persists dataset schemas, trained model records, and prediction audit history. | SQLite file `smartirrigate.db`; zero cloud cost. |
| **Serverless ETL** | Azure Functions | Event-driven Blob Trigger for automated CSV cleaning upon blob creation in `smartirrigate-raw-data`. | Handled locally by `DataPipeline` service. |
| **Managed Training** | Azure Machine Learning | Managed training jobs on Azure ML compute clusters with MLflow tracking and model registry. | Local Scikit-Learn training engine. |
| **Cloud Dashboard** | Microsoft Power BI | Enterprise BI dashboard for regional watershed managers. | In-app interactive Recharts dashboard. |

---

## 4. Cloud Service Mapping

```
Local Development Mode (Default)          Microsoft Azure Cloud Mode (Config-Driven)
--------------------------------          ------------------------------------------
Local FileSystem (./data_storage)  -----> Azure Blob Storage (Raw, Processed, Models)
FastAPI Internal Pipeline          -----> Azure Functions (BlobTrigger ETL)
Scikit-Learn in-memory training    -----> Azure Machine Learning (Compute Cluster Jobs)
SQLite Database                    -----> Azure Database for PostgreSQL / Cosmos DB
Vite Dev Server (Port 5173)        -----> Azure Static Web Apps + Front Door CDN
In-app Recharts Analytics          -----> Microsoft Power BI Reports & Dashboards
```

---

## 5. Architectural Quality Attributes

1. **Zero Fabrication Principle:** Metrics (MAE, RMSE, $R^2$) are computed on genuine 20% test splits using Scikit-learn functions.
2. **Graceful Degradation:** When Azure credentials are not configured, the platform functions 100% locally with zero errors.
3. **Idempotence & Safety:** Azure Function Blob Triggers verify input paths and write exclusively to downstream containers to prevent infinite event loops.
4. **Least-Privilege Security:** Azure Role-Based Access Control (RBAC) grants `Storage Blob Data Contributor` exclusively where necessary.
