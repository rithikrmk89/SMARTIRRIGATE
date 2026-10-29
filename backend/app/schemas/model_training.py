from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TrainModelRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User-friendly name for this model")
    dataset_id: int = Field(..., description="ID of the dataset to train on")
    model_type: str = Field(default="random_forest", pattern="^(random_forest|decision_tree|linear_regression)$")
    test_split_ratio: float = Field(default=0.2, ge=0.1, le=0.4, description="Test split ratio (0.1 - 0.4)")
    n_estimators: int = Field(default=100, ge=10, le=500, description="Trees in Random Forest")
    max_depth: Optional[int] = Field(default=12, ge=2, le=30, description="Max tree depth")


class ModelEvaluationMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float


class ModelDetail(BaseModel):
    id: int
    name: str
    model_type: str
    dataset_id: Optional[int]
    target_column: str
    features: List[str]
    train_rows: int
    test_rows: int
    metrics: ModelEvaluationMetrics
    baseline_metrics: Optional[ModelEvaluationMetrics] = None
    feature_importances: Dict[str, float]
    artefact_path: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
