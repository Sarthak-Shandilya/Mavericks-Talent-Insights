from __future__ import annotations

from urllib.parse import urlparse

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from storage.base import StorageClient


class AzureBlobStorageClient(StorageClient):
    def __init__(self, connection_string: str, container: str) -> None:
        if not connection_string:
            raise ValueError("AZURE_BLOB_CONNECTION_STRING is required")
        self._service = BlobServiceClient.from_connection_string(connection_string)
        self._container_name = container
        self._container = self._service.get_container_client(container)
        try:
            self._container.create_container()
        except ResourceExistsError:
            pass

    def save_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> str:
        blob = self._container.get_blob_client(key)
        blob.upload_blob(data, overwrite=True, content_type=content_type)
        return blob.url

    def read_bytes(self, *, url: str) -> bytes:
        parsed = urlparse(url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) != 2:
            raise ValueError("Invalid blob URL")
        container, blob_name = path_parts
        client = self._service.get_blob_client(container=container, blob=blob_name)
        return client.download_blob().readall()
