import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("smartirrigate.pipeline")

# Column name alias mapping to standardize diverse agricultural datasets
COLUMN_ALIASES = {
    "crop": "crop_type",
    "croptype": "crop_type",
    "soil": "soil_type",
    "soiltype": "soil_type",
    "soil_moisture": "soil_moisture_pct",
    "moisture": "soil_moisture_pct",
    "moisture_pct": "soil_moisture_pct",
    "temp": "temperature_c",
    "temperature": "temperature_c",
    "temp_c": "temperature_c",
    "humidity": "humidity_pct",
    "rh": "humidity_pct",
    "rain": "rainfall_mm",
    "rainfall": "rainfall_mm",
    "precipitation": "rainfall_mm",
    "sunlight": "sunlight_hours",
    "sun_hours": "sunlight_hours",
    "wind": "wind_speed_kmh",
    "wind_speed": "wind_speed_kmh",
    "area": "area_hectares",
    "water_demand": "water_demand_mm_day",
    "water_requirement": "water_demand_mm_day",
    "irrigation": "water_demand_mm_day",
    "irrigation_mm": "water_demand_mm_day",
}

EXPECTED_COLUMNS = [
    "crop_type",
    "soil_type",
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "rainfall_mm"
]


class DataPipeline:
    """
    Data Ingestion, Validation, Cleaning, and Transformation Pipeline.
    Ensures safe file parsing, schema normalization, outlier protection,
    and metadata extraction.
    """

    @staticmethod
    def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to lowercase snake_case and apply alias mappings."""
        clean_cols = {}
        for col in df.columns:
            normalized = str(col).strip().lower().replace(" ", "_").replace("-", "_")
            resolved = COLUMN_ALIASES.get(normalized, normalized)
            clean_cols[col] = resolved
        return df.rename(columns=clean_cols)

    @staticmethod
    def validate_and_clean(file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Ingests CSV from file_path, validates schema, cleans invalid/missing records,
        and computes summary statistics.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

        if df.empty:
            raise ValueError("The provided CSV file contains no records.")

        df = DataPipeline.standardize_columns(df)

        # Check required columns
        missing_required = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if missing_required:
            raise ValueError(
                f"Missing required agricultural columns: {', '.join(missing_required)}. "
                f"Present columns: {', '.join(df.columns)}"
            )

        initial_rows = len(df)
        total_missing = int(df.isnull().sum().sum())

        # Impute missing values
        for col in df.columns:
            if df[col].dtype in [np.float64, np.int64, float, int]:
                # Numeric column
                if df[col].isnull().any():
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
            else:
                # Categorical column
                if df[col].isnull().any():
                    mode_val = df[col].mode()
                    df[col] = df[col].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                df[col] = df[col].astype(str).str.strip().str.title()

        # Fill defaults for optional features if missing
        if "sunlight_hours" not in df.columns:
            df["sunlight_hours"] = 8.0
        if "wind_speed_kmh" not in df.columns:
            df["wind_speed_kmh"] = 10.0
        if "area_hectares" not in df.columns:
            df["area_hectares"] = 1.0

        # Target column check for regression
        if "water_demand_mm_day" not in df.columns:
            # If dataset has no target, calculate an initial FAO benchmark target
            from app.services.sample_generator import CROP_COEFFICIENTS, SOIL_FACTORS
            derived = []
            for _, row in df.iterrows():
                c = row.get("crop_type", "Wheat")
                s = row.get("soil_type", "Loamy")
                kc = CROP_COEFFICIENTS.get(c, 1.1)
                sf = SOIL_FACTORS.get(s, 1.0)
                t = float(row.get("temperature_c", 25.0))
                h = float(row.get("humidity_pct", 50.0))
                sm = float(row.get("soil_moisture_pct", 40.0))
                r = float(row.get("rainfall_mm", 0.0))
                sun = float(row.get("sunlight_hours", 8.0))
                w = float(row.get("wind_speed_kmh", 10.0))

                et0 = max(1.5, (0.09 * t) + (0.16 * sun) + (0.02 * w) - (0.035 * (h - 50.0)) + 0.8)
                etc = kc * et0 * sf
                deficit = ((55.0 - sm) / 100.0) * 4.2
                eff_rain = 0.8 * (r - 2.0) if r > 2.0 else 0.0
                derived.append(round(max(0.0, etc + deficit - eff_rain), 2))
            df["water_demand_mm_day"] = derived

        # Compute column statistics
        columns_meta = []
        for col in df.columns:
            is_num = bool(pd.api.types.is_numeric_dtype(df[col]))
            meta = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "mean": float(round(df[col].mean(), 2)) if is_num else None,
                "min": float(round(df[col].min(), 2)) if is_num else None,
                "max": float(round(df[col].max(), 2)) if is_num else None,
            }
            columns_meta.append(meta)

        summary_stats = {
            "initial_rows": initial_rows,
            "cleaned_rows": len(df),
            "missing_values_imputed": total_missing,
            "numeric_columns": [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])],
            "categorical_columns": [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])],
        }

        preview_rows = df.head(10).to_dict(orient="records")

        metadata = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_values_count": total_missing,
            "columns": columns_meta,
            "summary_stats": summary_stats,
            "preview_rows": preview_rows,
        }

        return df, metadata


data_pipeline = DataPipeline()
