import csv
import io
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schema import DatasetRecord, MLModelRecord, PredictionRecord
from app.schemas.prediction import DashboardStats, PredictionHistoryItem, PredictionInput, PredictionOutput
from app.services.ml_service import ml_service
from app.services.storage import storage_service

logger = logging.getLogger("smartirrigate.predictions")
router = APIRouter(prefix="/predictions", tags=["Predictions & Advisory"])


@router.post("/predict", response_model=PredictionOutput)
def create_prediction(input_data: PredictionInput, db: Session = Depends(get_db)):
    """
    Predict crop water demand and calculate total field volume.
    Returns:
    - Water demand (mm/day)
    - Total required water volume (m³ and Liters)
    - Actionable agronomic advisory & irrigation scheduling
    - Explainable feature importances from the active model
    """
    active_model = db.query(MLModelRecord).filter(MLModelRecord.is_active.is_(True)).first()
    if not active_model:
        # Check if any model exists; if so, activate the latest one
        active_model = db.query(MLModelRecord).order_by(MLModelRecord.created_at.desc()).first()
        if active_model:
            active_model.is_active = True
            db.commit()
            db.refresh(active_model)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No trained machine learning model found. Please train a model on a dataset first."
            )

    try:
        predicted_mm, total_m3, total_liters, recommendation, feature_importances = ml_service.predict(
            artefact_path=active_model.artefact_path,
            input_data=input_data.model_dump(),
        )
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )

    # Persist prediction in SQLite history
    record = PredictionRecord(
        crop_type=input_data.crop_type,
        soil_type=input_data.soil_type,
        soil_moisture_pct=input_data.soil_moisture_pct,
        temperature_c=input_data.temperature_c,
        humidity_pct=input_data.humidity_pct,
        rainfall_mm=input_data.rainfall_mm,
        sunlight_hours=input_data.sunlight_hours,
        wind_speed_kmh=input_data.wind_speed_kmh,
        area_hectares=input_data.area_hectares,
        predicted_water_demand_mm_day=predicted_mm,
        total_volume_m3=total_m3,
        total_volume_liters=total_liters,
        recommendation=recommendation,
        feature_contributions_json=json.dumps(feature_importances),
        model_id=active_model.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionOutput(
        id=record.id,
        crop_type=record.crop_type,
        soil_type=record.soil_type,
        predicted_water_demand_mm_day=record.predicted_water_demand_mm_day,
        total_volume_m3=record.total_volume_m3,
        total_volume_liters=record.total_volume_liters,
        area_hectares=record.area_hectares,
        recommendation=record.recommendation,
        feature_contributions=feature_importances,
        model_name=active_model.name,
        model_r2=active_model.r2,
        assumptions_note=(
            "Model predictions represent estimated Evapotranspiration (ETc) water demand "
            "adjusted for soil moisture deficit and effective rainfall. These are statistical "
            "model estimates, not physical telemetry sensor readings."
        ),
        created_at=record.created_at,
    )


@router.get("/history", response_model=List[PredictionHistoryItem])
def get_prediction_history(
    crop: Optional[str] = Query(None, description="Filter by crop name"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Query prediction history with optional crop filtering."""
    query = db.query(PredictionRecord)
    if crop:
        query = query.filter(PredictionRecord.crop_type.ilike(f"%{crop}%"))
    records = query.order_by(PredictionRecord.created_at.desc()).limit(limit).all()
    return records


@router.get("/export")
def export_predictions_csv(db: Session = Depends(get_db)):
    """Export prediction records to a downloadable CSV file."""
    records = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id", "timestamp", "crop_type", "soil_type", "soil_moisture_pct",
        "temperature_c", "humidity_pct", "rainfall_mm", "sunlight_hours",
        "wind_speed_kmh", "area_hectares", "predicted_water_demand_mm_day",
        "total_volume_m3", "total_volume_liters", "recommendation"
    ])

    for r in records:
        writer.writerow([
            r.id, r.created_at.isoformat() if r.created_at else "",
            r.crop_type, r.soil_type, r.soil_moisture_pct,
            r.temperature_c, r.humidity_pct, r.rainfall_mm,
            r.sunlight_hours, r.wind_speed_kmh, r.area_hectares,
            r.predicted_water_demand_mm_day, r.total_volume_m3,
            r.total_volume_liters, r.recommendation.replace("\n", " ")
        ])

    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=smartirrigate_predictions.csv"
    return response


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Aggregated metrics and distribution figures for the responsive dashboard."""
    total_preds = db.query(PredictionRecord).count()
    total_datasets = db.query(DatasetRecord).count()
    total_models = db.query(MLModelRecord).count()

    active_model = db.query(MLModelRecord).filter(MLModelRecord.is_active.is_(True)).first()

    recent = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(8).all()

    # Calculate average demand and total volume
    all_preds = db.query(PredictionRecord).all()
    if all_preds:
        avg_demand = round(sum(p.predicted_water_demand_mm_day for p in all_preds) / len(all_preds), 2)
        total_vol = round(sum(p.total_volume_m3 for p in all_preds), 2)
    else:
        avg_demand = 0.0
        total_vol = 0.0

    # Crop frequency distribution
    crop_counts = {}
    for p in all_preds:
        c = p.crop_type.title()
        crop_counts[c] = crop_counts.get(c, 0) + 1

    storage_mode_info = storage_service.get_storage_mode()

    return DashboardStats(
        total_predictions=total_preds,
        total_datasets=total_datasets,
        total_models=total_models,
        active_model_name=active_model.name if active_model else None,
        active_model_r2=active_model.r2 if active_model else None,
        avg_predicted_water_demand_mm=avg_demand,
        total_water_volume_m3_scheduled=total_vol,
        recent_predictions=recent,
        crop_distribution=crop_counts,
        storage_mode=storage_mode_info.get("mode", "Local"),
        cloud_status=storage_mode_info,
    )


@router.delete("/{prediction_id}")
def delete_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Delete a single prediction record."""
    record = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction record not found")
    db.delete(record)
    db.commit()
    return {"message": "Prediction deleted", "id": prediction_id}


@router.delete("")
def clear_all_predictions(db: Session = Depends(get_db)):
    """Clear all prediction records."""
    count = db.query(PredictionRecord).delete()
    db.commit()
    return {"message": f"Cleared {count} prediction records"}
