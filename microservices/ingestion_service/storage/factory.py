from configs.settings import get_settings
from storage.base import StorageClient
from storage.local_storage import LocalStorageClient


def get_storage_client() -> StorageClient:
    settings = get_settings()
    if settings.storage_type == "local":
        return LocalStorageClient()
    if settings.storage_type == "azure_blob":
        from storage.blob_storage import AzureBlobStorageClient

        return AzureBlobStorageClient(settings.azure_blob_connection_string)
    raise ValueError(f"Unsupported STORAGE_TYPE: {settings.storage_type}")
