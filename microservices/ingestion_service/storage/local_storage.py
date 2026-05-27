import logging
from pathlib import Path

from storage.base import StorageClient

logger = logging.getLogger(__name__)


class LocalStorageClient(StorageClient):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> str:
        path = (self.base_dir / key).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        url = f"local://{path.as_posix()}"
        logger.info("local_storage: saved %s bytes to %s", len(data), path)
        return url

    def read_bytes(self, *, url: str) -> bytes:
        if not url.startswith("local://"):
            raise ValueError("Unsupported local URL")
        path = Path(url.removeprefix("local://"))
        logger.info("local_storage: read path=%s exists=%s", path, path.is_file())
        data = path.read_bytes()
        logger.info("local_storage: read %s bytes from %s", len(data), path)
        return data
