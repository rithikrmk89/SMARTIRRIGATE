from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ColumnMetadata(BaseModel):
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    unique_count: int
    mean: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class DatasetSummary(BaseModel):
    id: int
    name: str
    filename: str
    row_count: int
    column_count: int
    file_size_bytes: int
    missing_values_count: int
    is_synthetic: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetDetail(DatasetSummary):
    columns: List[ColumnMetadata]
    summary_stats: Dict[str, Any]
    preview_rows: List[Dict[str, Any]]
    storage_path: str


class GenerateSampleRequest(BaseModel):
    num_samples: int = Field(default=1200, ge=100, le=10000, description="Number of synthetic sample rows to generate")
    include_outliers: bool = Field(default=False, description="Whether to include a few realistic field anomaly rows")
