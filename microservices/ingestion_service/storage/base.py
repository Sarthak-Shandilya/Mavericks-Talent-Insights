from __future__ import annotations

from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    def read_bytes(self, *, url: str) -> bytes:
        pass
