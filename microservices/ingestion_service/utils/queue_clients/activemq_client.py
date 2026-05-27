"""STOMP client for Apache ActiveMQ — used when settings.queue_type == \"generic\"."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable

import stomp

from utils.queue_clients.base import QueueClient

logger = logging.getLogger(__name__)

_SUBSCRIPTION_ID = "ingestion-service"


class _Handler(stomp.ConnectionListener):
    def __init__(self, conn: stomp.Connection, callback: Callable[[dict], None]) -> None:
        self._conn = conn
        self._callback = callback

    def on_error(self, frame: stomp.utils.Frame) -> None:
        logger.error("activemq: ERROR frame headers=%s body=%s", frame.headers, frame.body)

    def on_disconnected(self) -> None:
        logger.warning("activemq: disconnected")

    def on_message(self, frame: stomp.utils.Frame) -> None:
        logger.info("activemq: MESSAGE frame received body_len=%s", len(frame.body or ""))
        payload = json.loads(frame.body)
        self._callback(payload)
        ack_id = frame.headers.get("ack") or frame.headers.get("message-id")
        if ack_id:
            self._conn.ack(id=ack_id, subscription=_SUBSCRIPTION_ID)


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
        self._host = host
        self._port = port
        self._conn = stomp.Connection([(host, port)])
        self._user = user
        self._password = password
        self._prefix = destination_prefix
        self._connected = False
        self._handler: _Handler | None = None

    def _connect(self) -> None:
        if self._connected and self._conn.is_connected():
            return
        logger.info("activemq: STOMP connect host=%s port=%s…", self._host, self._port)
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
        dest = f"{self._prefix}{queue_name}"
        logger.info("activemq: consumer loop destination=%s ack=client-individual", dest)
        while True:
            try:
                self._connect()
                self._handler = _Handler(self._conn, handler)
                self._conn.set_listener("worker-listener", self._handler)
                self._conn.subscribe(
                    destination=dest,
                    id=_SUBSCRIPTION_ID,
                    ack="client-individual",
                )
                logger.info("activemq: subscribed destination=%s", dest)
                while self._conn.is_connected():
                    time.sleep(1.0)
            except Exception:
                logger.exception("activemq: consumer loop error — reconnecting in 5s")
                self._connected = False
                time.sleep(5.0)
