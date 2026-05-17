import logging
from pathlib import Path

from storage.base import StorageClient

logger = logging.getLogger(__name__)


class LocalStorageClient(StorageClient):
    def read_bytes(self, *, url: str) -> bytes:
        if not url.startswith("local://"):
            raise ValueError("Unsupported local URL")
        path = Path(url.removeprefix("local://"))
        logger.info("local_storage: read path=%s exists=%s", path, path.is_file())
        data = path.read_bytes()
        logger.info("local_storage: read %s bytes from %s", len(data), path)
        return data
