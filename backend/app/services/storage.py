import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger("smartirrigate.storage")


class StorageService:
    """
    Unified Storage Adapter.
    Handles dual-mode storage:
    1. Local storage in configured directories (Default)
    2. Microsoft Azure Blob Storage (when AZURE_STORAGE_ENABLED=True)
    """

    def __init__(self):
        self.blob_service_client = None
        self.is_azure = settings.AZURE_STORAGE_ENABLED
        if self.is_azure:
            try:
                from azure.storage.blob import BlobServiceClient

                if settings.AZURE_STORAGE_CONNECTION_STRING:
                    self.blob_service_client = BlobServiceClient.from_connection_string(
                        settings.AZURE_STORAGE_CONNECTION_STRING
                    )
                    logger.info("Connected to Azure Blob Storage via Connection String.")
                elif settings.AZURE_STORAGE_ACCOUNT_NAME and settings.AZURE_STORAGE_ACCOUNT_KEY:
                    account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                    self.blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=settings.AZURE_STORAGE_ACCOUNT_KEY
                    )
                    logger.info(f"Connected to Azure Blob Storage account: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
                elif settings.AZURE_STORAGE_ACCOUNT_NAME:
                    # Managed Identity / DefaultAzureCredential
                    from azure.identity import DefaultAzureCredential
                    account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                    self.blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=DefaultAzureCredential()
                    )
                    logger.info(f"Connected to Azure Blob Storage using DefaultAzureCredential for account: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
                else:
                    logger.warning("AZURE_STORAGE_ENABLED is True but neither AZURE_STORAGE_CONNECTION_STRING nor AZURE_STORAGE_ACCOUNT_NAME was provided. Falling back to local storage.")
                    self.is_azure = False
            except Exception as e:
                logger.warning(f"Could not initialize Azure Blob Storage client: {e}. Falling back to local storage.")
                self.blob_service_client = None
                self.is_azure = False

    def get_storage_mode(self) -> Dict[str, str]:
        """Return current active storage mode and details."""
        if self.is_azure and self.blob_service_client is not None:
            return {
                "mode": "Azure Blob Storage",
                "cloud_provider": "Microsoft Azure",
                "raw_container": settings.AZURE_RAW_CONTAINER,
                "processed_container": settings.AZURE_PROCESSED_CONTAINER,
                "models_container": settings.AZURE_MODELS_CONTAINER,
                "account_name": settings.AZURE_STORAGE_ACCOUNT_NAME or "connection_string_auth",
                "status": "connected"
            }
        return {
            "mode": "Local Filesystem & SQLite",
            "cloud_provider": "Local Fallback (Zero Cloud Cost)",
            "base_dir": str(settings.DATA_DIR),
            "status": "local_active"
        }

    def save_file(
        self,
        source_path: Path,
        target_dir: Path,
        filename: str,
        cloud_container: Optional[str] = None,
        s3_bucket: Optional[str] = None  # backward-compatible parameter alias
    ) -> str:
        """
        Save file locally, and optionally mirror to Azure Blob Storage if cloud mode is enabled.
        Returns the canonical local file path.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        dest_path = target_dir / filename
        if source_path.resolve() != dest_path.resolve():
            shutil.copyfile(source_path, dest_path)

        container = cloud_container or s3_bucket
        if self.is_azure and self.blob_service_client is not None and container:
            try:
                container_client = self.blob_service_client.get_container_client(container)
                if not container_client.exists():
                    container_client.create_container()
                blob_client = container_client.get_blob_client(filename)
                with open(dest_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                logger.info(f"Uploaded {filename} to Azure Blob container: {container}")
            except Exception as e:
                logger.error(f"Failed to upload {filename} to Azure Blob container {container}: {e}")

        return str(dest_path)

    def delete_file(
        self,
        file_path_str: str,
        cloud_container: Optional[str] = None,
        blob_name: Optional[str] = None,
        s3_bucket: Optional[str] = None,  # backward alias
        s3_key: Optional[str] = None      # backward alias
    ) -> bool:
        """Delete file from local storage and Azure Blob Storage if configured."""
        try:
            path = Path(file_path_str)
            if path.exists():
                path.unlink()

            container = cloud_container or s3_bucket
            blob = blob_name or s3_key
            if self.is_azure and self.blob_service_client is not None and container and blob:
                try:
                    container_client = self.blob_service_client.get_container_client(container)
                    blob_client = container_client.get_blob_client(blob)
                    if blob_client.exists():
                        blob_client.delete_blob()
                        logger.info(f"Deleted blob {blob} from Azure container {container}")
                except Exception as az_err:
                    logger.warning(f"Could not delete {blob} from Azure Blob container {container}: {az_err}")

            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path_str}: {e}")
            return False


storage_service = StorageService()
