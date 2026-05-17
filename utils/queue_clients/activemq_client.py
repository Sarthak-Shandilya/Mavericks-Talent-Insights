"""STOMP client for Apache ActiveMQ — used when settings.queue_type == \"generic\"."""

from __future__ import annotations

import json
import time
from collections.abc import Callable

import stomp

from utils.queue_clients.base import QueueClient


class _Handler(stomp.ConnectionListener):
    def __init__(self, callback: Callable[[dict], None]) -> None:
        self._callback = callback

    def on_message(self, frame: stomp.utils.FrameType) -> None:
        payload = json.loads(frame.body)
        self._callback(payload)


class ActiveMqQueueClient(QueueClient):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        destination_prefix: str,
    ) -> None:
        self._conn = stomp.Connection([(host, port)])
        self._user = user
        self._password = password
        self._destination_prefix = destination_prefix
        self._connected = False

    def _ensure_connected(self) -> None:
        if self._connected and self._conn.is_connected():
            return
        self._conn.connect(self._user, self._password, wait=True)
        self._connected = True

    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        self._ensure_connected()
        destination = f"{self._destination_prefix}{queue_name}"
        self._conn.send(
            destination=destination,
            body=json.dumps(message),
            headers={"persistent": "true", "message-id": message_id},
        )

    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        self._ensure_connected()
        destination = f"{self._destination_prefix}{queue_name}"
        self._conn.set_listener("ingestion-handler", _Handler(handler))
        self._conn.subscribe(destination=destination, id="ingestion-service", ack="auto")
        while True:
            time.sleep(1.0)
