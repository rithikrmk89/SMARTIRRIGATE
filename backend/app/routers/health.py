from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.schema import MLModelRecord, PredictionRecord, DatasetRecord
from app.services.storage import storage_service

router = APIRouter(prefix="/health", tags=["Health & Status"])


@router.get("")
def get_health_status(db: Session = Depends(get_db)):
    """Health check endpoint displaying system status, storage mode, and active models."""
    db_status = "connected"
    dataset_count = 0
    model_count = 0
    prediction_count = 0
    active_model = None

    try:
        dataset_count = db.query(DatasetRecord).count()
        model_count = db.query(MLModelRecord).count()
        prediction_count = db.query(PredictionRecord).count()
        active = db.query(MLModelRecord).filter(MLModelRecord.is_active.is_(True)).first()
        if active:
            active_model = {
                "id": active.id,
                "name": active.name,
                "model_type": active.model_type,
                "r2_score": active.r2,
                "mae": active.mae,
            }
    except Exception as e:
        db_status = f"degraded: {str(e)}"

    storage_info = storage_service.get_storage_mode()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "SmartIrrigate Cloud API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": db_status,
            "engine": "SQLite (Local) / RDS compatible",
            "total_datasets": dataset_count,
            "total_models": model_count,
            "total_predictions": prediction_count,
        },
        "storage": storage_info,
        "active_model": active_model,
        "cloud_services": {
            "azure_blob_storage": "enabled" if settings.AZURE_STORAGE_ENABLED else "local_fallback",
            "azure_functions": "configured_template",
            "azure_machine_learning": "configured_template",
            "azure_power_bi": "configured" if settings.AZURE_POWERBI_DASHBOARD_URL else "in_app_fallback",
        },
    }
