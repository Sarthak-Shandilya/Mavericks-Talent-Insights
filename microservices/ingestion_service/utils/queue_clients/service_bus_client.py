from __future__ import annotations

import json
from collections.abc import Callable

from azure.servicebus import ServiceBusClient, ServiceBusMessage

from utils.queue_clients.base import QueueClient


class ServiceBusQueueClient(QueueClient):
    def __init__(self, *, connection_string: str) -> None:
        if not connection_string:
            raise ValueError("SERVICE_BUS_CONNECTION_STRING is required")
        self._client = ServiceBusClient.from_connection_string(connection_string)

    def publish(self, *, queue_name: str, message: dict, message_id: str) -> None:
        with self._client:
            with self._client.get_queue_sender(queue_name=queue_name) as sender:
                sender.send_messages(ServiceBusMessage(json.dumps(message), message_id=message_id))

    def consume(self, *, queue_name: str, handler: Callable[[dict], None]) -> None:
        with self._client:
            with self._client.get_queue_receiver(queue_name=queue_name, max_wait_time=5) as receiver:
                while True:
                    for msg in receiver.receive_messages(max_message_count=10, max_wait_time=5):
                        raw = b"".join(bytes(part) for part in msg.body)
                        handler(json.loads(raw.decode("utf-8")))
                        receiver.complete_message(msg)
