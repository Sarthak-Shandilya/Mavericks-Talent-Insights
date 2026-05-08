from __future__ import annotations

from pathlib import Path

from storage.base import StorageClient


class LocalStorageClient(StorageClient):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> str:
        path = (self.base_dir / key).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{path.as_posix()}"

    def read_bytes(self, *, url: str) -> bytes:
        if not url.startswith("local://"):
            raise ValueError("Unsupported local URL format")
        path = Path(url.removeprefix("local://"))
        return path.read_bytes()
