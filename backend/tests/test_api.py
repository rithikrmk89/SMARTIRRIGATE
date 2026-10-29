from fastapi.testclient import TestClient
import pytest
from app.main import app, seed_initial_demo_data
from app.database import init_db

# Initialize database tables and seed baseline data for testing
init_db()
seed_initial_demo_data()

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "SmartIrrigate Cloud" in data["project"]


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "storage" in data


def test_datasets_endpoints():
    # List datasets
    response = client.get("/api/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert isinstance(datasets, list)

    # Generate sample dataset
    gen_response = client.post(
        "/api/datasets/generate-sample",
        json={"num_samples": 100, "include_outliers": False}
    )
    assert gen_response.status_code == 200
    new_dataset = gen_response.json()
    assert new_dataset["row_count"] == 100
    assert new_dataset["is_synthetic"] is True

    # Get dataset details
    detail_res = client.get(f"/api/datasets/{new_dataset['id']}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["columns"]) > 0


def test_prediction_and_stats():
    # Make a prediction
    pred_payload = {
        "crop_type": "Wheat",
        "soil_type": "Loamy",
        "soil_moisture_pct": 32.0,
        "temperature_c": 29.0,
        "humidity_pct": 45.0,
        "rainfall_mm": 0.0,
        "sunlight_hours": 9.0,
        "wind_speed_kmh": 12.0,
        "area_hectares": 1.5,
    }
    response = client.post("/api/predictions/predict", json=pred_payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_water_demand_mm_day" in data
    assert data["total_volume_m3"] > 0
    assert "recommendation" in data

    # Check dashboard stats
    stats_res = client.get("/api/predictions/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_predictions"] >= 1
    assert "crop_distribution" in stats

    # Check export
    export_res = client.get("/api/predictions/export")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers.get("content-type", "")
