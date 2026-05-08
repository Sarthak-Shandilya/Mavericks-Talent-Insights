from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue

from utils.queue_clients.base import QueueClient

_QUEUES: dict[str, Queue[dict]] = {}


class InMemoryQueueClient(QueueClient):
    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        _QUEUES.setdefault(queue_name, Queue()).put(message)

    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        q = _QUEUES.setdefault(queue_name, Queue())
        while True:
            try:
                message = q.get(timeout=2)
            except Empty:
                continue
            handler(message)
            q.task_done()
