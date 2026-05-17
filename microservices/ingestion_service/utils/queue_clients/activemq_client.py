"""STOMP client for Apache ActiveMQ — used when settings.queue_type == \"generic\"."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable

import stomp

from utils.queue_clients.base import QueueClient

logger = logging.getLogger(__name__)


class _Handler(stomp.ConnectionListener):
    def __init__(self, callback: Callable[[dict], None]) -> None:
        self._callback = callback

    def on_message(self, frame: stomp.utils.FrameType) -> None:
        logger.info("activemq: MESSAGE frame received body_len=%s", len(frame.body or ""))
        self._callback(json.loads(frame.body))


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
        self._prefix = destination_prefix
        self._connected = False

    def _connect(self) -> None:
        if self._connected and self._conn.is_connected():
            return
        logger.info("activemq: STOMP connect (host/port from settings)…")
        self._conn.connect(self._user, self._password, wait=True)
        self._connected = True
        logger.info("activemq: STOMP connected")

    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        self._connect()
        dest = f"{self._prefix}{queue_name}"
        logger.info("activemq: SEND destination=%s message_id=%s", dest, message_id)
        self._conn.send(
            destination=dest,
            body=json.dumps(message),
            headers={"persistent": "true", "message-id": message_id},
        )

    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        self._connect()
        dest = f"{self._prefix}{queue_name}"
        logger.info("activemq: SUBSCRIBE destination=%s ack=auto", dest)
        self._conn.set_listener("worker-listener", _Handler(handler))
        self._conn.subscribe(destination=dest, id="ingestion-service", ack="auto")
        logger.info("activemq: consumer loop running (sleep 1s)")
        while True:
            time.sleep(1.0)
