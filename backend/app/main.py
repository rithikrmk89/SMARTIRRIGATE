import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import SessionLocal, init_db
from app.models.schema import DatasetRecord, MLModelRecord, PredictionRecord
from app.routers import datasets_router, health_router, models_router, predictions_router
from app.services.data_pipeline import data_pipeline
from app.services.ml_service import ml_service
from app.services.sample_generator import generate_irrigation_dataset
from app.services.storage import storage_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("smartirrigate")


def seed_initial_demo_data():
    """
    Seeds an initial FAO-56 benchmark dataset and trains an initial
    RandomForestRegressor model if the database is newly initialized.
    Ensures the student/examiner has a ready-to-use system on first boot.
    """
    db = SessionLocal()
    try:
        dataset_count = db.query(DatasetRecord).count()
        if dataset_count == 0:
            logger.info("Initializing baseline benchmark dataset and demo model...")
            seed_filename = "seed_fao56_irrigation_benchmark.csv"
            raw_path = settings.UPLOAD_DIR / seed_filename

            # 1. Generate realistic benchmark data
            generate_irrigation_dataset(
                num_samples=1000,
                random_seed=42,
                output_path=raw_path,
                include_outliers=False,
            )

            # 2. Ingest through data pipeline
            cleaned_df, metadata = data_pipeline.validate_and_clean(raw_path)
            processed_filename = f"processed_{seed_filename}"
            processed_path = settings.PROCESSED_DIR / processed_filename
            cleaned_df.to_csv(processed_path, index=False)

            dataset_record = DatasetRecord(
                name="FAO-56 Irrigation Benchmark Dataset (Demo)",
                filename=processed_filename,
                storage_path=str(processed_path),
                row_count=metadata["row_count"],
                column_count=metadata["column_count"],
                file_size_bytes=processed_path.stat().st_size,
                missing_values_count=metadata["missing_values_count"],
                columns_json=json.dumps(metadata["columns"]),
                summary_stats_json=json.dumps(metadata["summary_stats"]),
                is_synthetic=True,
            )
            db.add(dataset_record)
            db.commit()
            db.refresh(dataset_record)

            # 3. Train Initial Random Forest Model
            from app.services.ml_service import ALL_FEATURES, TARGET_COLUMN
            train_results = ml_service.train_and_evaluate(
                df=cleaned_df,
                model_name="Random Forest Regressor (FAO Benchmark)",
                model_type="random_forest",
                test_split_ratio=0.2,
                n_estimators=100,
                max_depth=12,
            )

            model_record = MLModelRecord(
                name="Random Forest Regressor (FAO Benchmark)",
                model_type="random_forest",
                dataset_id=dataset_record.id,
                target_column=TARGET_COLUMN,
                features_json=json.dumps(ALL_FEATURES),
                train_rows=train_results["train_rows"],
                test_rows=train_results["test_rows"],
                mae=train_results["mae"],
                rmse=train_results["rmse"],
                r2=train_results["r2"],
                baseline_mae=train_results["baseline_mae"],
                baseline_rmse=train_results["baseline_rmse"],
                baseline_r2=train_results["baseline_r2"],
                feature_importances_json=json.dumps(train_results["feature_importances"]),
                artefact_path=train_results["artefact_path"],
                is_active=True,
            )
            db.add(model_record)
            db.commit()
            db.refresh(model_record)

            # 4. Seed sample predictions for dashboard charts
            sample_predictions = [
                ("Wheat", "Loamy", 38.0, 26.5, 55.0, 0.0, 8.5, 12.0, 2.5),
                ("Rice", "Clay", 68.0, 31.0, 78.0, 4.0, 7.0, 8.0, 5.0),
                ("Maize", "Sandy", 24.0, 33.5, 42.0, 0.0, 9.5, 15.0, 1.8),
                ("Cotton", "Loamy", 30.0, 35.0, 38.0, 0.0, 10.0, 14.0, 3.0),
                ("Tomato", "Silt", 45.0, 24.0, 62.0, 1.5, 8.0, 9.0, 1.0),
            ]

            for crop, soil, sm, temp, hum, rain, sun, wind, area in sample_predictions:
                inp = {
                    "crop_type": crop,
                    "soil_type": soil,
                    "soil_moisture_pct": sm,
                    "temperature_c": temp,
                    "humidity_pct": hum,
                    "rainfall_mm": rain,
                    "sunlight_hours": sun,
                    "wind_speed_kmh": wind,
                    "area_hectares": area,
                }
                pred_mm, vol_m3, vol_l, rec, feat_imp = ml_service.predict(
                    artefact_path=model_record.artefact_path,
                    input_data=inp,
                )
                pred_row = PredictionRecord(
                    crop_type=crop,
                    soil_type=soil,
                    soil_moisture_pct=sm,
                    temperature_c=temp,
                    humidity_pct=hum,
                    rainfall_mm=rain,
                    sunlight_hours=sun,
                    wind_speed_kmh=wind,
                    area_hectares=area,
                    predicted_water_demand_mm_day=pred_mm,
                    total_volume_m3=vol_m3,
                    total_volume_liters=vol_l,
                    recommendation=rec,
                    feature_contributions_json=json.dumps(feat_imp),
                    model_id=model_record.id,
                )
                db.add(pred_row)
            db.commit()
            logger.info("Successfully seeded demo dataset, model, and initial predictions.")
    except Exception as e:
        logger.error(f"Error during initial data seeding: {e}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed demo data if fresh
    init_db()
    seed_initial_demo_data()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="SmartIrrigate Cloud API",
    description=(
        "Cloud-Based Smart Irrigation & Water Demand Prediction System. "
        "Provides validated data ingestion, ML model training (Random Forest vs Baseline), "
        "agronomic water volume prediction, and Microsoft Azure (Blob/Functions/Azure ML) cloud integration."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Restrictive CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error_type": type(exc).__name__},
    )


# Attach Routers
app.include_router(health_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "project": "SmartIrrigate Cloud: Cloud-Based Smart Irrigation and Water Demand Prediction System",
        "status": "online",
        "documentation": "/docs",
        "api_prefix": "/api",
        "storage_mode": storage_service.get_storage_mode()["mode"],
    }
