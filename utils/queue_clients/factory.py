from configs.settings import get_settings
from utils.queue_clients.base import QueueClient
from utils.queue_clients.in_memory_client import InMemoryQueueClient


def get_queue_client() -> QueueClient:
    settings = get_settings()
    if settings.queue_type == "in_memory":
        return InMemoryQueueClient()
    if settings.queue_type == "activemq":
        from utils.queue_clients.activemq_client import ActiveMqQueueClient

        return ActiveMqQueueClient(
            host=settings.activemq_host,
            port=settings.activemq_port,
            user=settings.activemq_user,
            password=settings.activemq_password,
            destination_prefix=settings.activemq_destination_prefix,
        )
    if settings.queue_type == "service_bus":
        from utils.queue_clients.service_bus_client import ServiceBusQueueClient

        return ServiceBusQueueClient(connection_string=settings.service_bus_connection_string)
    raise ValueError(f"Unsupported QUEUE_TYPE: {settings.queue_type}")
