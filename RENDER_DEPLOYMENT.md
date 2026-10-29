# SmartIrrigate Cloud: Render Free-Tier Deployment Guide

This guide details how to deploy SmartIrrigate Cloud onto **Render** at **$0 cost** using the Free Tier (Web Service for FastAPI backend + Static Site for React frontend).

---

## 1. Architecture Overview on Render

```
+-----------------------------------------------------------------------------+
|                               Render Cloud                                  |
|                                                                             |
|  +---------------------------------------+                                  |
|  | Render Static Site (React 19 + Vite)   |                                  |
|  | URL: https://smartirrigate-ui.onrender.com |                             |
|  | (100% Free, Global CDN, Custom Domain)|                                  |
|  +---------------------------------------+                                  |
|                     |                                                       |
|                     | HTTPS REST API Calls (VITE_API_BASE_URL)              |
|                     v                                                       |
|  +---------------------------------------+     Auto-Seeder (Fresh Boot)     |
|  | Render Web Service (FastAPI + Python) | ----------------------------+    |
|  | URL: https://smartirrigate-api.onrender.com |                       |    |
|  | (Free Tier: 512MB RAM, 0.1 CPU, $0/mo)|                             v    |
|  +---------------------------------------+                +---------------+ |
|                     |                                     | SQLite Demo DB| |
|                     +-----------------------------------> | 1,000 samples | |
|                                                           | Active RF ML  | |
|                                                           +---------------+ |
+-----------------------------------------------------------------------------+
```

---

## 2. Free-Tier Characteristics & Data Persistence Reality

> [!IMPORTANT]
> **Ephemeral Filesystem on Render Free Tier:**
> - Render Free Web Services run in ephemeral containers. If no web traffic is received for 15 minutes, Render spins down the service to 0 instances to conserve resources.
> - When a new request arrives, Render spins up the container (cold start takes **30–50 seconds**).
> - Any files created on disk during runtime (such as newly uploaded custom CSV files or newly trained model artefacts) are discarded when the container sleeps or redeploys.
> 
> **How SmartIrrigate Cloud Handles This Automatically ($0 Cost):**
> - The application includes a self-healing startup lifespan hook (`backend/app/main.py:lifespan`).
> - When the backend container wakes up on Render, it detects the fresh environment, automatically generates the 1,000-sample FAO-56 benchmark dataset, trains the Random Forest Regressor ($R^2 \approx 0.93$), saves the `.joblib` model artefact, and seeds 6 demo predictions into SQLite.
> - **Result:** The examiner or evaluator will always see a fully working, populated, demonstrable application without manual setup.
> 
> **Options for Permanent Cloud Persistence (if desired):**
> 1. **Free Cloud Database:** Connect a free PostgreSQL instance from **Supabase** or **Neon** by setting `DATABASE_URL=postgresql://...` (100% free forever, persistent tables).
> 2. **Free Cloud Storage:** Set `AZURE_STORAGE_ENABLED=true` or use an S3-compatible bucket (AWS S3 Free Tier / Supabase Storage) to persist datasets and models permanently.
> 3. *Paid Render Persistent Disk:* Render offers persistent disks starting at $0.25/GB/month, but this requires upgrading the service to the paid "Starter" plan ($7/month). **We do not recommend this as free alternatives exist.**

---

## 3. Deployment Methods

### Option A: Automated Blueprint Deployment via `render.yaml` (Recommended)

1. Push your repository to **GitHub** (public or private).
2. Log in to your [Render Dashboard](https://dashboard.render.com/).
3. Click **Blueprints** in the top navigation bar.
4. Click **New Blueprint Instance**.
5. Connect your GitHub repository.
6. Render will automatically parse [`render.yaml`](file:///c:/Users/RITHIK%20MANIKANDAN/Desktop/cloud%20project/render.yaml) and configure both services:
   - `smartirrigate-backend` (Web Service, Python runtime)
   - `smartirrigate-frontend` (Static Site)
7. Click **Apply**.
8. Once deployed, resolve the circular URLs as described in [Section 4](#4-resolving-the-circular-url-dependency).

---

### Option B: Step-by-Step Manual Dashboard Deployment

If you prefer to configure each service manually via the Render UI:

#### Step 1: Deploy Backend Web Service
1. In the Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name:** `smartirrigate-backend` (or a name of your choice)
   - **Region:** `Oregon (US West)` or closest to your location
   - **Branch:** `main` (or `master`)
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
4. Expand **Advanced**:
   - **Health Check Path:** `/api/health`
   - **Auto-Deploy:** `Yes`
5. Under **Environment Variables**, add:
   | Key | Value | Purpose |
   | :--- | :--- | :--- |
   | `ENVIRONMENT` | `production` | Production mode |
   | `DEBUG` | `false` | Disable debug logs |
   | `DATABASE_URL` | `sqlite:///./smartirrigate.db` | Local SQLite in container |
   | `AZURE_STORAGE_ENABLED` | `false` | Run with built-in storage |
   | `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173,*` | Temporary until frontend URL is known |
6. Click **Create Web Service**.
7. Wait 2–3 minutes for the build to finish. Copy your backend URL (e.g. `https://smartirrigate-backend-xxxx.onrender.com`).

#### Step 2: Deploy Frontend Static Site
1. In the Render Dashboard, click **New +** $\rightarrow$ **Static Site**.
2. Connect the same GitHub repository.
3. Configure the following fields:
   - **Name:** `smartirrigate-frontend` (or a name of your choice)
   - **Branch:** `main` (or `master`)
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. Under **Environment Variables**, add:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://smartirrigate-backend-xxxx.onrender.com/api` |
   *(Replace with your actual backend URL from Step 1)*
5. Under **Redirects/Rewrites**:
   - **Type:** `Rewrite`
   - **Source:** `/*`
   - **Destination:** `/index.html`
   *(Ensures React Router client-side routing works on page refreshes)*
6. Click **Create Static Site**.
7. Copy your frontend URL (e.g. `https://smartirrigate-frontend-yyyy.onrender.com`).

---

## 4. Resolving the Circular URL Dependency

Because frontend and backend each need to know the other's public URL:

1. **Update Backend CORS Origins:**
   - In Render Dashboard $\rightarrow$ Click your **Backend Web Service** $\rightarrow$ **Environment**.
   - Update `CORS_ORIGINS` to include your live frontend URL:
     ```
     https://smartirrigate-frontend-yyyy.onrender.com,http://localhost:3000,http://localhost:5173
     ```
   - Click **Save Changes** (Render will automatically redeploy the backend).

2. **Verify Frontend API Base:**
   - In Render Dashboard $\rightarrow$ Click your **Frontend Static Site** $\rightarrow$ **Environment**.
   - Verify `VITE_API_BASE_URL` is set to:
     ```
     https://smartirrigate-backend-xxxx.onrender.com/api
     ```
   - If changed, click **Save Changes** and trigger a manual redeploy (**Manual Deploy $\rightarrow$ Deploy latest commit**) because Vite environment variables are embedded into JavaScript at build time.

---

## 5. Post-Deployment Verification Checklist

Once both services show green checkmarks in Render:

| Check | Action / Endpoint | Expected Response |
| :--- | :--- | :--- |
| **Backend Root** | `https://<backend>.onrender.com/` | JSON: `{"project": "SmartIrrigate Cloud...", "status": "online"}` |
| **Backend Health** | `https://<backend>.onrender.com/api/health` | JSON: `{"status": "healthy", "database": {"status": "connected"}}` |
| **Swagger Docs** | `https://<backend>.onrender.com/docs` | Interactive FastAPI documentation UI |
| **Frontend Home** | `https://<frontend>.onrender.com/` | SmartIrrigate Cloud Agtech Dashboard loads with real stats |
| **Prediction Test** | Navigate to `/predict` on UI $\rightarrow$ Submit sample | Water demand ($mm/\text{day}$) and plot volume ($m^3$) rendered with feature importance bars |
| **Dataset Ingestion** | Navigate to `/datasets` $\rightarrow$ Inspect schema | Shows 1,000 rows FAO-56 benchmark dataset |
| **Model Studio** | Navigate to `/models` | Shows active Random Forest model ($R^2 \ge 0.90$) |

---

## 6. Cold Start Notice for Viva / Evaluators

When presenting the live Render link to professors or examiners:
- Open the backend URL `https://<backend>.onrender.com/api/health` in your browser **1–2 minutes before the presentation**.
- This wakes up the free-tier container from its idle sleep state, ensuring the dashboard loads instantaneously when you present.

