from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PredictionInput(BaseModel):
    crop_type: str = Field(..., description="Crop (e.g. Wheat, Rice, Maize, Cotton, Tomato, Sugarcane, Potato, Barley)")
    soil_type: str = Field(..., description="Soil texture (Sandy, Loamy, Clay, Silt, Peaty)")
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Volumetric soil moisture percentage (0-100%)")
    temperature_c: float = Field(..., ge=-10.0, le=60.0, description="Ambient air temperature in Celsius (-10 to 60°C)")
    humidity_pct: float = Field(..., ge=0.0, le=100.0, description="Relative atmospheric humidity (0-100%)")
    rainfall_mm: float = Field(..., ge=0.0, le=500.0, description="Precipitation/rainfall in mm (0-500mm)")
    sunlight_hours: float = Field(default=8.0, ge=0.0, le=16.0, description="Daily sunshine duration in hours")
    wind_speed_kmh: float = Field(default=10.0, ge=0.0, le=120.0, description="Wind speed in km/h")
    area_hectares: float = Field(default=1.0, gt=0.0, le=10000.0, description="Field size in hectares")


class PredictionOutput(BaseModel):
    id: Optional[int] = None
    crop_type: str
    soil_type: str
    predicted_water_demand_mm_day: float
    total_volume_m3: float
    total_volume_liters: float
    area_hectares: float
    recommendation: str
    feature_contributions: Dict[str, float]
    model_name: str
    model_r2: float
    assumptions_note: str
    created_at: Optional[datetime] = None


class PredictionHistoryItem(BaseModel):
    id: int
    crop_type: str
    soil_type: str
    soil_moisture_pct: float
    temperature_c: float
    humidity_pct: float
    rainfall_mm: float
    sunlight_hours: float
    wind_speed_kmh: float
    area_hectares: float
    predicted_water_demand_mm_day: float
    total_volume_m3: float
    total_volume_liters: float
    recommendation: str
    model_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_predictions: int
    total_datasets: int
    total_models: int
    active_model_name: Optional[str] = None
    active_model_r2: Optional[float] = None
    avg_predicted_water_demand_mm: float
    total_water_volume_m3_scheduled: float
    recent_predictions: List[PredictionHistoryItem]
    crop_distribution: Dict[str, int]
    storage_mode: str
    cloud_status: Dict[str, Any] = {}
