import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import resolve_storage_path, settings
from app.services.storage import storage_service

logger = logging.getLogger("smartirrigate.ml")

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


class MLService:
    """
    Machine Learning Model Lifecycle Service:
    - Trains baseline (Linear Regression / Mean Dummy) and primary (RandomForestRegressor)
    - Strictly computes MAE, RMSE, R² on 20% unseen test split
    - Extracts feature importance for explainability
    - Generates agronomic water recommendations and field volumetric totals
    """

    @staticmethod
    def _build_preprocessor():
        return ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ]
        )

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        model_name: str,
        model_type: str = "random_forest",
        test_split_ratio: float = 0.2,
        n_estimators: int = 100,
        max_depth: Optional[int] = 12,
    ) -> Dict[str, Any]:
        """
        Trains the selected model alongside a baseline model on the dataset.
        Evaluates metrics strictly on the held-out test split.
        """
        # Ensure all required columns exist
        for col in ALL_FEATURES + [TARGET_COLUMN]:
            if col not in df.columns:
                raise ValueError(f"Dataset is missing required feature/target: {col}")

        X = df[ALL_FEATURES].copy()
        y = df[TARGET_COLUMN].astype(float).values

        if len(X) < 30:
            raise ValueError(f"Dataset has only {len(X)} rows. Minimum 30 rows required for reliable training.")

        # Train/Test Split (stratification not used for continuous regression target)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_split_ratio, random_state=settings.RANDOM_STATE
        )

        preprocessor = self._build_preprocessor()

        # 1. Train Baseline Model (Linear Regression)
        baseline_pipeline = Pipeline(
            steps=[
                ("preprocessor", self._build_preprocessor()),
                ("regressor", LinearRegression()),
            ]
        )
        baseline_pipeline.fit(X_train, y_train)
        y_baseline_pred = baseline_pipeline.predict(X_test)

        baseline_mae = float(mean_absolute_error(y_test, y_baseline_pred))
        baseline_rmse = float(np.sqrt(mean_squared_error(y_test, y_baseline_pred)))
        baseline_r2 = float(r2_score(y_test, y_baseline_pred))

        # 2. Select and Train Primary Model
        if model_type == "decision_tree":
            primary_regressor = DecisionTreeRegressor(
                max_depth=max_depth,
                random_state=settings.RANDOM_STATE,
            )
        elif model_type == "linear_regression":
            primary_regressor = LinearRegression()
        else:
            # Default: RandomForestRegressor
            primary_regressor = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=settings.RANDOM_STATE,
                n_jobs=-1,
            )

        model_pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("regressor", primary_regressor),
            ]
        )

        model_pipeline.fit(X_train, y_train)
        y_pred = model_pipeline.predict(X_test)

        # Strictly calculated test metrics
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))

        # 3. Extract Feature Importance for Explainability
        feature_importances = self._calculate_feature_importances(model_pipeline, primary_regressor)

        # 4. Save Model Artefact
        safe_name = "".join(c for c in model_name if c.isalnum() or c in ("-", "_")).lower()
        artefact_filename = f"model_{safe_name}_{int(pd.Timestamp.now().timestamp())}.joblib"
        artefact_path = settings.MODELS_DIR / artefact_filename

        joblib.dump(
            {
                "pipeline": model_pipeline,
                "features": ALL_FEATURES,
                "target": TARGET_COLUMN,
                "metrics": {"mae": mae, "rmse": rmse, "r2": r2},
                "feature_importances": feature_importances,
                "model_type": model_type,
            },
            artefact_path,
        )

        # Mirror to Azure Blob Storage if enabled
        storage_service.save_file(
            source_path=artefact_path,
            target_dir=settings.MODELS_DIR,
            filename=artefact_filename,
            cloud_container=settings.AZURE_MODELS_CONTAINER,
        )

        return {
            "model_type": model_type,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "baseline_mae": round(baseline_mae, 4),
            "baseline_rmse": round(baseline_rmse, 4),
            "baseline_r2": round(baseline_r2, 4),
            "feature_importances": feature_importances,
            "artefact_path": str(artefact_path),
        }

    def _calculate_feature_importances(self, pipeline: Pipeline, regressor: Any) -> Dict[str, float]:
        """Aggregate feature importance scores back to human-readable domain features."""
        try:
            if hasattr(regressor, "feature_importances_"):
                raw_importances = regressor.feature_importances_
                ohe = pipeline.named_steps["preprocessor"].named_transformers_["cat"]
                cat_encoded_cols = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
                all_transformed_cols = NUMERICAL_FEATURES + cat_encoded_cols

                raw_dict = dict(zip(all_transformed_cols, raw_importances))

                # Aggregate categorical one-hot encoded weights back to parent feature
                aggregated = {}
                for num_col in NUMERICAL_FEATURES:
                    aggregated[num_col] = float(round(raw_dict.get(num_col, 0.0), 4))

                for cat_col in CATEGORICAL_FEATURES:
                    total_cat_imp = sum(
                        raw_dict[c] for c in cat_encoded_cols if c.startswith(f"{cat_col}_")
                    )
                    aggregated[cat_col] = float(round(total_cat_imp, 4))

                # Normalize so they sum to 1.0 for clear UI display
                total = sum(aggregated.values())
                if total > 0:
                    normalized = {k: round(v / total, 4) for k, v in aggregated.items()}
                else:
                    normalized = aggregated
                return dict(sorted(normalized.items(), key=lambda item: item[1], reverse=True))

            elif hasattr(regressor, "coef_"):
                # Linear Regression coefficients magnitude
                raw_coefs = np.abs(regressor.coef_)
                total = float(np.sum(raw_coefs)) or 1.0
                norm_coefs = raw_coefs / total
                ohe = pipeline.named_steps["preprocessor"].named_transformers_["cat"]
                cat_cols = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
                all_cols = NUMERICAL_FEATURES + cat_cols

                raw_dict = dict(zip(all_cols, norm_coefs))
                aggregated = {num: float(round(raw_dict.get(num, 0.0), 4)) for num in NUMERICAL_FEATURES}
                for cat_col in CATEGORICAL_FEATURES:
                    aggregated[cat_col] = float(
                        round(sum(raw_dict[c] for c in cat_cols if c.startswith(f"{cat_col}_")), 4)
                    )
                return dict(sorted(aggregated.items(), key=lambda item: item[1], reverse=True))
        except Exception as e:
            logger.warning(f"Could not compute explicit feature importance: {e}")

        # Fallback uniform weights
        return {f: round(1.0 / len(ALL_FEATURES), 4) for f in ALL_FEATURES}

    def predict(
        self,
        artefact_path: str,
        input_data: Dict[str, Any],
    ) -> Tuple[float, float, float, str, Dict[str, float]]:
        """
        Executes model inference, computes volumetric field requirement,
        and generates expert agronomic recommendation.
        """
        model_file = resolve_storage_path(artefact_path, settings.MODELS_DIR)
        if not model_file.exists():
            raise FileNotFoundError(f"Model artefact not found at: {artefact_path}")

        loaded = joblib.load(model_file)
        pipeline = loaded["pipeline"]
        feature_importances = loaded.get("feature_importances", {})

        # Build single-row DataFrame with expected schema
        row = {
            "crop_type": [str(input_data["crop_type"]).title()],
            "soil_type": [str(input_data["soil_type"]).title()],
            "soil_moisture_pct": [float(input_data["soil_moisture_pct"])],
            "temperature_c": [float(input_data["temperature_c"])],
            "humidity_pct": [float(input_data["humidity_pct"])],
            "rainfall_mm": [float(input_data["rainfall_mm"])],
            "sunlight_hours": [float(input_data.get("sunlight_hours", 8.0))],
            "wind_speed_kmh": [float(input_data.get("wind_speed_kmh", 10.0))],
        }
        df_input = pd.DataFrame(row)

        pred_raw = pipeline.predict(df_input)[0]
        # Physically bound prediction: water demand cannot be negative
        predicted_demand_mm = max(0.0, float(round(pred_raw, 2)))

        # Volumetric irrigation calculation:
        # 1 mm over 1 hectare (10,000 m²) = 10 m³ = 10,000 Liters
        area_ha = float(input_data.get("area_hectares", 1.0))
        total_m3 = round(predicted_demand_mm * 10.0 * area_ha, 2)
        total_liters = round(total_m3 * 1000.0, 1)

        recommendation = self._generate_recommendation(input_data, predicted_demand_mm, total_m3)

        return predicted_demand_mm, total_m3, total_liters, recommendation, feature_importances

    def _generate_recommendation(
        self,
        inputs: Dict[str, Any],
        predicted_demand_mm: float,
        total_m3: float,
    ) -> str:
        """Rule-based agronomic advisory tailored to crop, soil, and weather inputs."""
        rainfall = float(inputs.get("rainfall_mm", 0.0))
        soil_moisture = float(inputs.get("soil_moisture_pct", 50.0))
        crop = str(inputs.get("crop_type", "Crop")).title()
        soil = str(inputs.get("soil_type", "Loamy")).title()
        temp = float(inputs.get("temperature_c", 25.0))

        if rainfall >= 18.0:
            return (
                f"Significant rainfall ({rainfall} mm) recorded or forecast. "
                f"Halt automated irrigation to prevent root hypoxia, nutrient leaching, and soil erosion."
            )

        if soil_moisture >= 75.0:
            return (
                f"Soil moisture ({soil_moisture}%) is currently near field saturation. "
                f"No irrigation required today for {crop}. Check moisture again in 24 hours."
            )

        if predicted_demand_mm <= 0.5:
            return (
                f"Minimal crop water requirement ({predicted_demand_mm} mm/day). "
                f"Natural soil reserve and microclimate are sufficient. System in standby mode."
            )

        advice_parts = []
        if temp >= 34.0:
            advice_parts.append(
                f"High ambient temperature ({temp}°C) creates intense evaporative demand. "
                f"Deliver the required {total_m3} m³ during pre-dawn (4:30 AM - 7:30 AM) or dusk to prevent 30-40% evaporative loss."
            )
        else:
            advice_parts.append(
                f"Deliver {total_m3} m³ ({predicted_demand_mm} mm/day depth) to sustain optimal vegetative growth for {crop}."
            )

        if soil == "Sandy":
            advice_parts.append(
                "Coarse sandy soil exhibits rapid percolation. Split irrigation into two cycles (morning & evening) to maximize root zone retention."
            )
        elif soil == "Clay":
            advice_parts.append(
                "Clay soil has a slow infiltration rate. Use low-pressure micro-drip emitters to avoid surface pooling and fungal leaf moisture."
            )
        else:
            advice_parts.append(
                "Standard scheduled drip irrigation or furrow-pulse cycle is recommended."
            )

        return " ".join(advice_parts)


ml_service = MLService()
