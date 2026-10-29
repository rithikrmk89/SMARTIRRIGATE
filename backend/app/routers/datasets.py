import json
import logging
from pathlib import Path
from typing import List
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import resolve_storage_path, settings
from app.database import get_db
from app.models.schema import DatasetRecord
from app.schemas.dataset import DatasetDetail, DatasetSummary, GenerateSampleRequest
from app.services.data_pipeline import data_pipeline
from app.services.sample_generator import generate_irrigation_dataset
from app.services.storage import storage_service

logger = logging.getLogger("smartirrigate.datasets")
router = APIRouter(prefix="/datasets", tags=["Dataset Management"])

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


@router.get("", response_model=List[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)):
    """List all available datasets with metadata summary."""
    records = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    return records


@router.post("/upload", response_model=DatasetDetail)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload and validate a CSV dataset for training and analysis.
    Performs schema validation, column standardization, missing-value imputation,
    and metadata extraction.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files (.csv) are accepted."
        )

    # Safe file writing to upload directory
    clean_filename = f"upload_{int(pd.Timestamp.now().timestamp())}_{file.filename}"
    upload_path = settings.UPLOAD_DIR / clean_filename

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    with open(upload_path, "wb") as f:
        f.write(content)

    try:
        cleaned_df, metadata = data_pipeline.validate_and_clean(upload_path)
    except Exception as e:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Persist cleaned version
    processed_filename = f"processed_{clean_filename}"
    processed_path = settings.PROCESSED_DIR / processed_filename
    cleaned_df.to_csv(processed_path, index=False)

    # Save to storage service (mirrors to Azure Blob if enabled)
    storage_service.save_file(
        source_path=processed_path,
        target_dir=settings.PROCESSED_DIR,
        filename=processed_filename,
        cloud_container=settings.AZURE_RAW_CONTAINER,
    )

    record = DatasetRecord(
        name=file.filename.replace(".csv", "").replace("_", " ").title(),
        filename=processed_filename,
        storage_path=str(processed_path),
        row_count=metadata["row_count"],
        column_count=metadata["column_count"],
        file_size_bytes=len(content),
        missing_values_count=metadata["missing_values_count"],
        columns_json=json.dumps(metadata["columns"]),
        summary_stats_json=json.dumps(metadata["summary_stats"]),
        is_synthetic=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetDetail(
        id=record.id,
        name=record.name,
        filename=record.filename,
        row_count=record.row_count,
        column_count=record.column_count,
        file_size_bytes=record.file_size_bytes,
        missing_values_count=record.missing_values_count,
        is_synthetic=record.is_synthetic,
        created_at=record.created_at,
        columns=metadata["columns"],
        summary_stats=metadata["summary_stats"],
        preview_rows=metadata["preview_rows"],
        storage_path=record.storage_path,
    )


@router.post("/generate-sample", response_model=DatasetDetail)
def generate_sample_dataset(request: GenerateSampleRequest, db: Session = Depends(get_db)):
    """
    Generate a realistic synthetic agricultural dataset based on the FAO-56 Penman-Monteith method.
    The resulting dataset is explicitly flagged as synthetic demo data.
    """
    filename = f"synthetic_irrigation_{int(pd.Timestamp.now().timestamp())}.csv"
    raw_path = settings.UPLOAD_DIR / filename

    generate_irrigation_dataset(
        num_samples=request.num_samples,
        random_seed=settings.RANDOM_STATE,
        output_path=raw_path,
        include_outliers=request.include_outliers,
    )

    cleaned_df, metadata = data_pipeline.validate_and_clean(raw_path)
    processed_filename = f"processed_{filename}"
    processed_path = settings.PROCESSED_DIR / processed_filename
    cleaned_df.to_csv(processed_path, index=False)

    storage_service.save_file(
        source_path=processed_path,
        target_dir=settings.PROCESSED_DIR,
        filename=processed_filename,
        cloud_container=settings.AZURE_RAW_CONTAINER,
    )

    record = DatasetRecord(
        name=f"FAO-56 Benchmark Synthetic Demo ({request.num_samples} rows)",
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
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetDetail(
        id=record.id,
        name=record.name,
        filename=record.filename,
        row_count=record.row_count,
        column_count=record.column_count,
        file_size_bytes=record.file_size_bytes,
        missing_values_count=record.missing_values_count,
        is_synthetic=record.is_synthetic,
        created_at=record.created_at,
        columns=metadata["columns"],
        summary_stats=metadata["summary_stats"],
        preview_rows=metadata["preview_rows"],
        storage_path=record.storage_path,
    )


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve full details, statistics, and preview rows of a specific dataset."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    file_path = resolve_storage_path(record.storage_path, settings.PROCESSED_DIR)
    preview_rows = []
    if file_path.exists():
        try:
            df = pd.read_csv(file_path, nrows=10)
            preview_rows = df.to_dict(orient="records")
        except Exception:
            pass

    return DatasetDetail(
        id=record.id,
        name=record.name,
        filename=record.filename,
        row_count=record.row_count,
        column_count=record.column_count,
        file_size_bytes=record.file_size_bytes,
        missing_values_count=record.missing_values_count,
        is_synthetic=record.is_synthetic,
        created_at=record.created_at,
        columns=json.loads(record.columns_json or "[]"),
        summary_stats=json.loads(record.summary_stats_json or "{}"),
        preview_rows=preview_rows,
        storage_path=record.storage_path,
    )


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Delete a dataset and its physical file."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    file_path = resolve_storage_path(record.storage_path, settings.PROCESSED_DIR)
    storage_service.delete_file(
        file_path_str=str(file_path),
        cloud_container=settings.AZURE_RAW_CONTAINER,
        blob_name=record.filename,
    )
    db.delete(record)
    db.commit()
    return {"message": "Dataset successfully deleted", "id": dataset_id}
