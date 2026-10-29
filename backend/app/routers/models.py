import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schema import DatasetRecord, MLModelRecord
from app.schemas.model_training import ModelDetail, ModelEvaluationMetrics, TrainModelRequest
from app.config import resolve_storage_path, settings
from app.services.ml_service import ml_service
from app.services.storage import storage_service

logger = logging.getLogger("smartirrigate.models")
router = APIRouter(prefix="/models", tags=["Model Training & Management"])


def _format_model_detail(record: MLModelRecord) -> ModelDetail:
    return ModelDetail(
        id=record.id,
        name=record.name,
        model_type=record.model_type,
        dataset_id=record.dataset_id,
        target_column=record.target_column,
        features=json.loads(record.features_json or "[]"),
        train_rows=record.train_rows,
        test_rows=record.test_rows,
        metrics=ModelEvaluationMetrics(
            mae=record.mae,
            rmse=record.rmse,
            r2=record.r2,
        ),
        baseline_metrics=ModelEvaluationMetrics(
            mae=record.baseline_mae or 0.0,
            rmse=record.baseline_rmse or 0.0,
            r2=record.baseline_r2 or 0.0,
        ) if record.baseline_mae is not None else None,
        feature_importances=json.loads(record.feature_importances_json or "{}"),
        artefact_path=record.artefact_path,
        is_active=record.is_active,
        created_at=record.created_at,
    )


@router.get("", response_model=List[ModelDetail])
def list_models(db: Session = Depends(get_db)):
    """List all trained regression models with validation metrics."""
    records = db.query(MLModelRecord).order_by(MLModelRecord.created_at.desc()).all()
    return [_format_model_detail(r) for r in records]


@router.get("/active", response_model=Optional[ModelDetail])
def get_active_model(db: Session = Depends(get_db)):
    """Get the currently active prediction model."""
    record = db.query(MLModelRecord).filter(MLModelRecord.is_active.is_(True)).first()
    if not record:
        return None
    return _format_model_detail(record)


@router.post("/train", response_model=ModelDetail)
def train_model(request: TrainModelRequest, db: Session = Depends(get_db)):
    """
    Train a supported regression model on the selected dataset.
    Strictly calculates MAE, RMSE, and R² against a held-out test split (never fabricated).
    Also trains a baseline model for comparative performance evaluation.
    """
    dataset = db.query(DatasetRecord).filter(DatasetRecord.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified dataset not found")

    file_path = resolve_storage_path(dataset.storage_path, settings.PROCESSED_DIR)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file missing at storage path: {dataset.storage_path}"
        )

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read dataset file: {str(e)}"
        )

    try:
        train_results = ml_service.train_and_evaluate(
            df=df,
            model_name=request.name,
            model_type=request.model_type,
            test_split_ratio=request.test_split_ratio,
            n_estimators=request.n_estimators,
            max_depth=request.max_depth,
        )
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Training error: {str(e)}")

    # If no other model is active, activate this new one automatically
    existing_active = db.query(MLModelRecord).filter(MLModelRecord.is_active.is_(True)).first()
    should_activate = existing_active is None

    from app.services.ml_service import ALL_FEATURES, TARGET_COLUMN

    record = MLModelRecord(
        name=request.name,
        model_type=train_results["model_type"],
        dataset_id=dataset.id,
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
        is_active=should_activate,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _format_model_detail(record)


@router.post("/{model_id}/activate", response_model=ModelDetail)
def activate_model(model_id: int, db: Session = Depends(get_db)):
    """Set the specified model as active for incoming prediction requests."""
    target_model = db.query(MLModelRecord).filter(MLModelRecord.id == model_id).first()
    if not target_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    # Deactivate all others
    db.query(MLModelRecord).update({MLModelRecord.is_active: False})
    target_model.is_active = True
    db.commit()
    db.refresh(target_model)

    return _format_model_detail(target_model)


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Delete a trained model and remove its local artefact."""
    target_model = db.query(MLModelRecord).filter(MLModelRecord.id == model_id).first()
    if not target_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    model_path = resolve_storage_path(target_model.artefact_path, settings.MODELS_DIR)
    storage_service.delete_file(
        file_path_str=str(model_path),
        s3_bucket=None,
    )
    db.delete(target_model)
    db.commit()
    return {"message": "Model successfully deleted", "id": model_id}
