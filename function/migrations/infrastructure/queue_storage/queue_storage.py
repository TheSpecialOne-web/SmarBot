import base64
import json
from typing import Any

from .client import get_queue_client

MIGRATION_QUEUE_NAME = "migration-queue"


def send_message_to_migration_queue(message: dict[str, Any]) -> None:
    json_message = json.dumps(message)
    encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(MIGRATION_QUEUE_NAME)
    queue_client.send_message(encoded_message)
