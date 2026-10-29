import os
from pathlib import Path
from typing import Any, List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration for SmartIrrigate Cloud.
    Loads settings from environment variables or .env file with safe defaults.
    Supports local development mode and Microsoft Azure cloud integration.
    """
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database
    DATABASE_URL: str = "sqlite:///./smartirrigate.db"

    # Storage Paths (Local Development Mode)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data_storage"
    UPLOAD_DIR: Path = BASE_DIR / "data_storage" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data_storage" / "processed"
    MODELS_DIR: Path = BASE_DIR / "data_storage" / "models"

    # Microsoft Azure Cloud Storage Configuration
    AZURE_STORAGE_ENABLED: bool = False
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = None
    AZURE_RAW_CONTAINER: str = "smartirrigate-raw-data"
    AZURE_PROCESSED_CONTAINER: str = "smartirrigate-processed"
    AZURE_MODELS_CONTAINER: str = "smartirrigate-models"

    # Azure Machine Learning & Power BI Integrations
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: Optional[str] = "smartirrigate-rg"
    AZURE_ML_WORKSPACE_NAME: Optional[str] = "smartirrigate-aml"
    AZURE_ML_COMPUTE_NAME: str = "cpu-cluster"
    AZURE_POWERBI_DASHBOARD_URL: Optional[str] = None

    # Model Defaults
    DEFAULT_MODEL_TYPE: str = "random_forest"
    RANDOM_STATE: int = 42
    TEST_SPLIT_RATIO: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self) -> None:
        """Ensure necessary local storage folders exist."""
        for directory in [self.DATA_DIR, self.UPLOAD_DIR, self.PROCESSED_DIR, self.MODELS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()


def resolve_storage_path(path_str: str, default_dir: Path) -> Path:
    """
    Robustly resolves a stored file path across operating systems and containers.
    If the path was recorded with a Windows drive (e.g. C:\\...) and is now running
    in Linux/Docker/Render, it falls back to resolving the filename relative to default_dir.
    """
    if not path_str:
        return default_dir
    p = Path(path_str)
    if p.exists():
        return p
    # Handle Windows backslashes gracefully on POSIX
    filename = Path(str(path_str).replace("\\", "/")).name
    alt = default_dir / filename
    if alt.exists():
        return alt
    return p

