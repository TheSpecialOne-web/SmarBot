import base64
import json
import os
from typing import TypedDict

from libs.retry import retry_azure_auth_error

from .client import get_queue_client

INDEX_BACKUP_QUEUE_NAME = os.environ.get("AZURE_QUEUE_STORAGE_INDEX_BACKUP_QUEUE_NAME") or "backup-index-queue"


class IndexBackupQueueMessage(TypedDict):
    datetime: str
    endpoint: str
    index_name: str


@retry_azure_auth_error
def send_message_to_index_backup_queue(queue_message: IndexBackupQueueMessage) -> None:
    json_message = json.dumps(queue_message)
    encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(INDEX_BACKUP_QUEUE_NAME)
    queue_client.send_message(encoded_message)
