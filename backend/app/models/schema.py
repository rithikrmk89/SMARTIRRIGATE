from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class DatasetRecord(Base):
    """Metadata table for uploaded or generated irrigation datasets."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    missing_values_count = Column(Integer, default=0)
    columns_json = Column(Text, default="[]")
    summary_stats_json = Column(Text, default="{}")
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    models = relationship("MLModelRecord", back_populates="dataset", cascade="all, delete-orphan")


class MLModelRecord(Base):
    """Trained machine learning models and genuine evaluation metrics."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(64), nullable=False)  # random_forest, linear_regression, decision_tree
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    target_column = Column(String(64), default="water_demand_mm_day")
    features_json = Column(Text, default="[]")
    train_rows = Column(Integer, default=0)
    test_rows = Column(Integer, default=0)

    # Primary model evaluation metrics (strictly calculated on test split)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)

    # Baseline comparison metrics
    baseline_mae = Column(Float, nullable=True)
    baseline_rmse = Column(Float, nullable=True)
    baseline_r2 = Column(Float, nullable=True)

    # Explainability & Model Artefact
    feature_importances_json = Column(Text, default="{}")
    artefact_path = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    dataset = relationship("DatasetRecord", back_populates="models")
    predictions = relationship("PredictionRecord", back_populates="model")


class PredictionRecord(Base):
    """Inference history for water demand estimation and crop irrigation."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    crop_type = Column(String(64), nullable=False)
    soil_type = Column(String(64), nullable=False)
    soil_moisture_pct = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    rainfall_mm = Column(Float, nullable=False)
    sunlight_hours = Column(Float, default=8.0)
    wind_speed_kmh = Column(Float, default=10.0)
    area_hectares = Column(Float, default=1.0)

    # Outputs
    predicted_water_demand_mm_day = Column(Float, nullable=False)
    total_volume_m3 = Column(Float, nullable=False)
    total_volume_liters = Column(Float, nullable=False)
    recommendation = Column(Text, nullable=False)
    feature_contributions_json = Column(Text, default="{}")

    model_id = Column(Integer, ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    model = relationship("MLModelRecord", back_populates="predictions")
