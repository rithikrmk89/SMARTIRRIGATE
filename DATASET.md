# SmartIrrigate Cloud: Dataset Specification & Provenance

This document details the data schemas, verified public agro-meteorological sources, licensing, preprocessing transformations, and the synthetic demonstration generator used in the SmartIrrigate Cloud platform.

---

## 1. Verified Public Agricultural Data Sources

The machine learning models in SmartIrrigate Cloud are grounded in established international agricultural standards and open agrometeorological databases:

1. **Food and Agriculture Organization of the United Nations (FAO) — Irrigation and Drainage Paper No. 56**
   - **Title:** *Crop evapotranspiration - Guidelines for computing crop water requirements*
   - **Authors:** Richard G. Allen, Luis S. Pereira, Dirk Raes, Martin Smith (FAO, Rome, Italy).
   - **Standard Reference:** FAO-56 Penman-Monteith equation for reference evapotranspiration ($ET_0$) and single-crop coefficient ($K_c$) methodology.
   - **Public Access:** [FAO Water Reports No. 56](https://www.fao.org/land-water/databases-and-software/cropwat/en/)
   - **License:** Open Access / FAO Copyright Policies (educational and research dissemination permitted with attribution).

2. **India Meteorological Department (IMD) — National Agrometeorological Advisory Services**
   - **Scope:** Gridded daily temperature, relative humidity, precipitation, wind speed, and sunshine duration across agro-climatic zones.
   - **Public Portal:** [IMD Agromet Advisory](https://agromet.imd.gov.in/)
   - **License:** Open Government Data (OGD) Platform India (CC-BY equivalent).

3. **Kaggle Crop Water Requirement & Smart Irrigation Open Benchmarks**
   - **Datasets:** *Crop Water Requirement Dataset* & *Agricultural Sensor Data for Irrigation*
   - **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
   - **Attribution:** Verified open datasets utilized for benchmarking soil moisture and weather regressions.

---

## 2. Dataset Schema & Feature Definitions

| Field Name | Type | Unit | Range | Agronomic Significance |
| :--- | :--- | :--- | :--- | :--- |
| `crop_type` | String | Categorical | 8 Crops | Determines the mid-season crop coefficient ($K_c$) reflecting leaf area index, stomatal resistance, and canopy height. |
| `soil_type` | String | Categorical | 5 Soils | Governs infiltration rate, hydraulic conductivity, and soil water-holding capacity (field capacity vs wilting point). |
| `soil_moisture_pct` | Float | Percentage (%) | 0.0 - 100.0 | Volumetric soil moisture in the root zone. Indicates existing water reserve before scheduling irrigation. |
| `temperature_c` | Float | Degrees Celsius (°C) | -10.0 - 55.0 | Primary driver of sensible heat flux and vapor pressure deficit, accelerating leaf transpiration. |
| `humidity_pct` | Float | Percentage (%) | 10.0 - 100.0 | Atmospheric relative humidity; lower humidity widens the vapor pressure deficit between stomata and air. |
| `rainfall_mm` | Float | Millimeters (mm) | 0.0 - 300.0 | Daily precipitation. Converted to *effective rainfall* ($P_{eff}$) after accounting for surface runoff. |
| `sunlight_hours` | Float | Hours / Day | 0.0 - 16.0 | Direct solar irradiance duration controlling net radiation ($R_n$). |
| `wind_speed_kmh` | Float | Kilometers/Hour (km/h) | 0.0 - 120.0 | Turbulent vapor transfer factor stripping boundary layer humidity from crop canopies. |
| `area_hectares` | Float | Hectares (ha) | 0.1 - 10,000.0 | Farm plot size utilized to scale depth ($mm$) into volumetric water delivery ($m^3$ and Liters). |
| `water_demand_mm_day` | Float | Millimeters / Day | 0.0 - 25.0 | **Target Variable:** Net daily depth of irrigation water required to sustain non-stressed crop growth. |

---

## 3. Demarcation: Synthetic Demo Data vs. Real Telemetry

> [!IMPORTANT]
> **Transparency Declaration:**
> The bundled `data/sample_irrigation_data.csv` and the "Generate Demo Benchmark" button produce **synthetic agronomic approximations**.
> - Every synthetic record includes the flag `data_source: synthetic_fao56_demo`.
> - These records are mathematically generated using the FAO-56 Penman-Monteith physical equations with added stochastic Gaussian noise ($\sigma = 0.28$).
> - They are designed for reproducible academic demonstrations, unit tests, and pipeline verification.
> - **They are never claimed or presented as direct physical IoT sensor measurements.**
>
> In real-world agricultural deployments, the data ingestion pipeline is designed to ingest raw CSV telemetry from automated weather stations (AWS) or soil moisture probe data loggers.

---

## 4. Data Ingestion & Preprocessing Pipeline

The automated preprocessing pipeline (`app/services/data_pipeline.py`) performs the following steps:

1. **Schema Standardization:** Resolves diverse column naming conventions (e.g., `temp`, `temp_c`, `temperature` $\rightarrow$ `temperature_c`).
2. **Missing-Value Imputation:**
   - Numerical columns: Imputed using column medians to avoid outlier skew.
   - Categorical columns: Imputed using modal categories and sanitized to title case.
3. **Derived Feature Handling:** If optional features like `sunlight_hours` or `wind_speed_kmh` are missing from an uploaded CSV, conservative regional agro-climatic defaults (8.0 hours, 10.0 km/h) are assigned.
4. **Target Calculation for Unlabelled Data:** If a user uploads environmental data lacking target labels, the pipeline applies the reference FAO-56 $ET_c$ formulation to bootstrap the initial regression target.
5. **Feature Encoding & Scaling:**
   - Categorical features (`crop_type`, `soil_type`) undergo `OneHotEncoder(handle_unknown='ignore')`.
   - Continuous numerical features undergo `StandardScaler()` zero-mean unit-variance transformation.

---

## 5. Limitations of Meteorological Water Modeling

1. **Micro-climatic Variations:** Regional weather forecasts may vary from canopy-level microclimates inside valley floors or greenhouse tunnels.
2. **Growth Stage Dynamics:** Crop coefficients ($K_c$) fluctuate from initial germination ($K_{c,ini} \approx 0.3$) to mid-season maturity ($K_{c,mid} \approx 1.2$). The demo model utilizes mid-season peak coefficients.
3. **Salinity & Soil Compaction:** Saline soils require additional leaching fractions not accounted for in standard evapotranspiration equations.
