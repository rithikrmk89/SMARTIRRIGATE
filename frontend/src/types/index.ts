export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  database: {
    status: string;
    engine: string;
    total_datasets: number;
    total_models: number;
    total_predictions: number;
  };
  storage: {
    mode: string;
    cloud_provider?: string;
    raw_container?: string;
    processed_container?: string;
    models_container?: string;
    account_name?: string;
    raw_bucket?: string;
    processed_bucket?: string;
    models_bucket?: string;
    region?: string;
    status: string;
  };
  active_model?: {
    id: number;
    name: string;
    model_type: string;
    r2_score: number;
    mae: number;
  } | null;
  cloud_services: {
    azure_blob_storage?: string;
    azure_functions?: string;
    azure_machine_learning?: string;
    azure_power_bi?: string;
    aws_s3?: string;
    aws_lambda?: string;
    aws_sagemaker?: string;
    aws_quicksight?: string;
  };
}

export interface ColumnMeta {
  name: string;
  dtype: string;
  non_null_count: number;
  null_count: number;
  unique_count: number;
  mean?: number | null;
  min?: number | null;
  max?: number | null;
}

export interface DatasetItem {
  id: number;
  name: string;
  filename: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  missing_values_count: number;
  is_synthetic: boolean;
  created_at: string;
}

export interface DatasetDetail extends DatasetItem {
  columns: ColumnMeta[];
  summary_stats: {
    initial_rows: number;
    cleaned_rows: number;
    missing_values_imputed: number;
    numeric_columns: string[];
    categorical_columns: string[];
  };
  preview_rows: Record<string, any>[];
  storage_path: string;
}

export interface MLModelItem {
  id: number;
  name: string;
  model_type: string;
  dataset_id?: number | null;
  target_column: string;
  features: string[];
  train_rows: number;
  test_rows: number;
  metrics: {
    mae: number;
    rmse: number;
    r2: number;
  };
  baseline_metrics?: {
    mae: number;
    rmse: number;
    r2: number;
  } | null;
  feature_importances: Record<string, number>;
  artefact_path: string;
  is_active: boolean;
  created_at: string;
}

export interface PredictionInput {
  crop_type: string;
  soil_type: string;
  soil_moisture_pct: number;
  temperature_c: number;
  humidity_pct: number;
  rainfall_mm: number;
  sunlight_hours: number;
  wind_speed_kmh: number;
  area_hectares: number;
}

export interface PredictionResult {
  id?: number;
  crop_type: string;
  soil_type: string;
  predicted_water_demand_mm_day: number;
  total_volume_m3: number;
  total_volume_liters: number;
  area_hectares: number;
  recommendation: string;
  feature_contributions: Record<string, number>;
  model_name: string;
  model_r2: number;
  assumptions_note: string;
  created_at?: string;
}

export interface PredictionHistoryItem {
  id: number;
  crop_type: string;
  soil_type: string;
  soil_moisture_pct: number;
  temperature_c: number;
  humidity_pct: number;
  rainfall_mm: number;
  sunlight_hours: number;
  wind_speed_kmh: number;
  area_hectares: number;
  predicted_water_demand_mm_day: number;
  total_volume_m3: number;
  total_volume_liters: number;
  recommendation: string;
  model_id?: number | null;
  created_at: string;
}

export interface DashboardStats {
  total_predictions: number;
  total_datasets: number;
  total_models: number;
  active_model_name?: string | null;
  active_model_r2?: number | null;
  avg_predicted_water_demand_mm: number;
  total_water_volume_m3_scheduled: number;
  recent_predictions: PredictionHistoryItem[];
  crop_distribution: Record<string, number>;
  storage_mode: string;
  cloud_status: Record<string, any>;
}
