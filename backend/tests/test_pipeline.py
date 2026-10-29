import tempfile
from pathlib import Path
import pandas as pd
import pytest
from app.services.data_pipeline import DataPipeline, data_pipeline
from app.services.sample_generator import generate_irrigation_dataset


def test_standardize_columns():
    df = pd.DataFrame({
        "Crop": ["Wheat"],
        "Soil": ["Loamy"],
        "Soil Moisture": [35.0],
        "Temp": [28.0],
        "RH": [60.0],
        "Rain": [0.0]
    })
    standardized = DataPipeline.standardize_columns(df)
    assert "crop_type" in standardized.columns
    assert "soil_type" in standardized.columns
    assert "soil_moisture_pct" in standardized.columns
    assert "temperature_c" in standardized.columns
    assert "humidity_pct" in standardized.columns
    assert "rainfall_mm" in standardized.columns


def test_generate_irrigation_dataset():
    df = generate_irrigation_dataset(num_samples=50, random_seed=42)
    assert len(df) == 50
    assert "water_demand_mm_day" in df.columns
    assert (df["water_demand_mm_day"] >= 0).all()
    assert (df["soil_moisture_pct"] >= 0).all()


def test_validate_and_clean_pipeline():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        df = pd.DataFrame({
            "crop_type": ["Wheat", "Rice", "Maize"],
            "soil_type": ["Sandy", None, "Clay"],
            "soil_moisture_pct": [30.0, None, 45.0],
            "temperature_c": [25.0, 30.0, 28.0],
            "humidity_pct": [50.0, 60.0, 55.0],
            "rainfall_mm": [0.0, 5.0, 2.0],
            "water_demand_mm_day": [4.5, 6.2, 3.8]
        })
        df.to_csv(tmp.name, index=False)
        tmp_path = Path(tmp.name)

    try:
        cleaned_df, meta = data_pipeline.validate_and_clean(tmp_path)
        assert len(cleaned_df) == 3
        assert cleaned_df["soil_moisture_pct"].isnull().sum() == 0
        assert cleaned_df["soil_type"].isnull().sum() == 0
        assert meta["row_count"] == 3
        assert meta["missing_values_count"] == 2
    finally:
        tmp_path.unlink(missing_ok=True)
