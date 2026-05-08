from __future__ import annotations

from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    def save_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> str:
        """Save bytes and return URL/URI."""

    @abstractmethod
    def read_bytes(self, *, url: str) -> bytes:
        """Read bytes from a previously returned URL/URI."""
