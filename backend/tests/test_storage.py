from pathlib import Path
import tempfile
import pytest
from app.services.storage import StorageService
from app.config import settings


def test_storage_mode_default_local():
    service = StorageService()
    mode_info = service.get_storage_mode()
    assert "mode" in mode_info
    assert "Local" in mode_info["mode"]
    assert mode_info["status"] == "local_active"


def test_storage_save_and_delete_file():
    service = StorageService()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Test content for Azure storage adapter fallback")
        tmp_path = Path(tmp.name)

    dest_dir = settings.DATA_DIR / "test_temp"
    try:
        saved_path = service.save_file(
            source_path=tmp_path,
            target_dir=dest_dir,
            filename="saved_test_blob.txt",
            cloud_container=settings.AZURE_RAW_CONTAINER
        )
        assert Path(saved_path).exists()
        assert Path(saved_path).name == "saved_test_blob.txt"

        deleted = service.delete_file(
            file_path_str=saved_path,
            cloud_container=settings.AZURE_RAW_CONTAINER,
            blob_name="saved_test_blob.txt"
        )
        assert deleted is True
        assert not Path(saved_path).exists()
    finally:
        tmp_path.unlink(missing_ok=True)
        if dest_dir.exists():
            import shutil
            shutil.rmtree(dest_dir, ignore_errors=True)
