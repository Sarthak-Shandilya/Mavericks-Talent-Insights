from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue

from utils.queue_clients.base import QueueClient

_QUEUES: dict[str, Queue[dict]] = {}


class InMemoryQueueClient(QueueClient):
    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        q = _QUEUES.setdefault(queue_name, Queue())
        q.put(message)

    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        q = _QUEUES.setdefault(queue_name, Queue())
        while True:
            try:
                item = q.get(timeout=2.0)
            except Empty:
                continue
            handler(item)
            q.task_done()
