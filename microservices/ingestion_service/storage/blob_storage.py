from urllib.parse import urlparse

from azure.storage.blob import BlobServiceClient

from storage.base import StorageClient


class AzureBlobStorageClient(StorageClient):
    def __init__(self, connection_string: str) -> None:
        if not connection_string:
            raise ValueError("AZURE_BLOB_CONNECTION_STRING is required")
        self._service = BlobServiceClient.from_connection_string(connection_string)

    def read_bytes(self, *, url: str) -> bytes:
        parsed = urlparse(url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) != 2:
            raise ValueError("Invalid blob URL")
        container, blob_name = path_parts
        client = self._service.get_blob_client(container=container, blob=blob_name)
        return client.download_blob().readall()
