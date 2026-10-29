"""
Amazon SageMaker Training Entrypoint Script for SmartIrrigate Cloud
Compatible with SageMaker Scikit-Learn Container
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
    parser = argparse.ArgumentParser()
    # SageMaker container environment paths
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train-dir", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=12)
    parser.add_argument("--test-split", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting SageMaker SmartIrrigate training with args: {args}")

    # Discover training CSV
    csv_files = [f for f in os.listdir(args.train_dir) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in channel directory: {args.train_dir}")

    data_file = os.path.join(args.train_dir, csv_files[0])
    print(f"Loading training data from {data_file}")
    df = pd.read_csv(data_file)

    # Standardize column names
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

    # Baseline Linear Regression
    baseline_pipe = Pipeline(steps=[("prep", preprocessor), ("reg", LinearRegression())])
    baseline_pipe.fit(X_train, y_train)
    y_base_pred = baseline_pipe.predict(X_test)
    base_mae = float(mean_absolute_error(y_test, y_base_pred))
    base_r2 = float(r2_score(y_test, y_base_pred))

    # Primary Random Forest Regressor
    rf_regressor = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
        n_jobs=-1,
    )
    rf_pipe = Pipeline(steps=[("prep", preprocessor), ("reg", rf_regressor)])
    rf_pipe.fit(X_train, y_train)
    y_pred = rf_pipe.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "baseline_mae": round(base_mae, 4),
        "baseline_r2": round(base_r2, 4),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    print(f"SageMaker Training Evaluation Metrics: {json.dumps(metrics, indent=2)}")

    # Save model artefact to /opt/ml/model (SageMaker automatically zips and uploads to S3)
    model_output_path = os.path.join(args.model_dir, "model.joblib")
    joblib.dump(
        {
            "pipeline": rf_pipe,
            "features": ALL_FEATURES,
            "target": TARGET_COLUMN,
            "metrics": metrics,
        },
        model_output_path,
    )

    # Write evaluation metrics JSON alongside model
    metrics_path = os.path.join(args.model_dir, "evaluation_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Successfully saved model artefact to {model_output_path}")


if __name__ == "__main__":
    main()
