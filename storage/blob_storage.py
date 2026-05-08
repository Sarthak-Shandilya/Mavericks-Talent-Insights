from __future__ import annotations

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from storage.base import StorageClient


class AzureBlobStorageClient(StorageClient):
    def __init__(self, connection_string: str, container: str) -> None:
        if not connection_string:
            raise ValueError("AZURE_BLOB_CONNECTION_STRING is required for azure_blob storage")
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container = self._client.get_container_client(container)
        try:
            self._container.create_container()
        except ResourceExistsError:
            pass

    def save_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> str:
        blob = self._container.get_blob_client(key)
        blob.upload_blob(data, overwrite=True, content_type=content_type)
        return blob.url

    def read_bytes(self, *, url: str) -> bytes:
        blob_name = url.split("/", 3)[-1]
        blob = self._container.get_blob_client(blob_name)
        return blob.download_blob().readall()
