from __future__ import annotations

import json
import logging

from configs.settings import get_settings
from processors import process_upload
from utils.queue_clients import get_queue_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ingestion-service")


def _handler(message: dict) -> None:
    logger.info("Received upload message: %s", json.dumps(message))
    process_upload(message)
    logger.info("Completed upload_id=%s", message.get("upload_id"))


def main() -> None:
    settings = get_settings()
    logger.info("Starting ingestion worker with queue_type=%s", settings.queue_type)
    queue = get_queue_client()
    queue.consume(queue_name=settings.queue_name_ingestion, handler=_handler)


if __name__ == "__main__":
    main()
