from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class QueueClient(ABC):
    @abstractmethod
    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        pass

    @abstractmethod
    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        pass
