"""
Azure Machine Learning (Azure ML) Training Entrypoint Script
SmartIrrigate Cloud: Cloud-Based Smart Irrigation & Water Demand Prediction
"""

import argparse
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

CATEGORICAL_FEATURES = ["crop_type", "soil_type"]
NUMERICAL_FEATURES = [
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "rainfall_mm",
    "sunlight_hours",
    "wind_speed_kmh",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
TARGET_COLUMN = "water_demand_mm_day"


def parse_args():
    parser = argparse.ArgumentParser(description="Azure ML Training Script for SmartIrrigate")
    parser.add_argument("--data-path", type=str, default="./data", help="Directory or file path to training data")
    parser.add_argument("--output-dir", type=str, default="./outputs", help="Output directory for model artefacts")
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=12)
    parser.add_argument("--test-split", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Azure ML SmartIrrigate training with parameters: {args}")

    os.makedirs(args.output_dir, exist_ok=True)

    # Resolve training CSV file
    if os.path.isfile(args.data_path):
        data_file = args.data_path
    else:
        csv_files = [f for f in os.listdir(args.data_path) if f.endswith(".csv")]
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in data path: {args.data_path}")
        data_file = os.path.join(args.data_path, csv_files[0])

    print(f"Reading training dataset from: {data_file}")
    df = pd.read_csv(data_file)

    clean_cols = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
    df.rename(columns=clean_cols, inplace=True)

    X = df[ALL_FEATURES].copy()
    y = df[TARGET_COLUMN].astype(float).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_split, random_state=args.random_state
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    # 1. Baseline Model
    baseline_pipe = Pipeline(steps=[("prep", preprocessor), ("reg", LinearRegression())])
    baseline_pipe.fit(X_train, y_train)
    y_base_pred = baseline_pipe.predict(X_test)
    base_mae = float(mean_absolute_error(y_test, y_base_pred))
    base_rmse = float(np.sqrt(mean_squared_error(y_test, y_base_pred)))
    base_r2 = float(r2_score(y_test, y_base_pred))

    # 2. Random Forest Regressor
    rf = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
        n_jobs=-1
    )
    rf_pipe = Pipeline(steps=[("prep", preprocessor), ("reg", rf)])
    rf_pipe.fit(X_train, y_train)
    y_pred = rf_pipe.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_mae": round(mae, 4),
        "test_rmse": round(rmse, 4),
        "test_r2": round(r2, 4),
        "baseline_mae": round(base_mae, 4),
        "baseline_rmse": round(base_rmse, 4),
        "baseline_r2": round(base_r2, 4),
    }
    print(f"Azure ML Evaluation Metrics: {json.dumps(metrics, indent=2)}")

    # Log with MLflow if in Azure ML environment
    if MLFLOW_AVAILABLE:
        try:
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            mlflow.log_param("n_estimators", args.n_estimators)
            mlflow.log_param("max_depth", args.max_depth)
            mlflow.sklearn.log_model(rf_pipe, "smartirrigate_rf_model")
        except Exception as e:
            print(f"MLflow logging notice: {e}")

    # Save model artefact
    model_path = os.path.join(args.output_dir, "model.joblib")
    joblib.dump(
        {
            "pipeline": rf_pipe,
            "features": ALL_FEATURES,
            "target": TARGET_COLUMN,
            "metrics": metrics,
        },
        model_path
    )

    metrics_path = os.path.join(args.output_dir, "evaluation_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Model artefact successfully stored at: {model_path}")


if __name__ == "__main__":
    main()
