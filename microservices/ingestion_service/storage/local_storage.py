from pathlib import Path

from storage.base import StorageClient


class LocalStorageClient(StorageClient):
    def read_bytes(self, *, url: str) -> bytes:
        if not url.startswith("local://"):
            raise ValueError("Unsupported local URL")
        path = Path(url.removeprefix("local://"))
        return path.read_bytes()
