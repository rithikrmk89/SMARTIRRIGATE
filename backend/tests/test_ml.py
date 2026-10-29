from pathlib import Path
import pytest
from app.services.ml_service import ml_service
from app.services.sample_generator import generate_irrigation_dataset


def test_ml_train_and_evaluate():
    # Generate small dataset for testing
    df = generate_irrigation_dataset(num_samples=120, random_seed=42)

    results = ml_service.train_and_evaluate(
        df=df,
        model_name="Test Random Forest",
        model_type="random_forest",
        test_split_ratio=0.2,
        n_estimators=20,
        max_depth=5,
    )

    assert "mae" in results
    assert "rmse" in results
    assert "r2" in results
    assert "baseline_mae" in results
    assert results["mae"] >= 0.0
    assert results["rmse"] >= 0.0
    assert Path(results["artefact_path"]).exists()

    # Test inference using the generated artefact
    input_data = {
        "crop_type": "Wheat",
        "soil_type": "Loamy",
        "soil_moisture_pct": 35.0,
        "temperature_c": 28.0,
        "humidity_pct": 50.0,
        "rainfall_mm": 0.0,
        "sunlight_hours": 8.0,
        "wind_speed_kmh": 10.0,
        "area_hectares": 2.0,
    }

    pred_mm, vol_m3, vol_l, rec, feat_imp = ml_service.predict(
        artefact_path=results["artefact_path"],
        input_data=input_data,
    )

    assert pred_mm >= 0.0
    # 1 mm over 2 hectares = 20 m³ = 20,000 Liters
    assert vol_m3 == round(pred_mm * 10.0 * 2.0, 2)
    assert vol_l == round(vol_m3 * 1000.0, 1)
    assert len(rec) > 10
    assert isinstance(feat_imp, dict)
