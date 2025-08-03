import base64
import json
import os

from search_index_backup.types import IndexBackupQueue

from .client import get_queue_client

INDEX_BACKUP_QUEUE_NAME = os.environ.get("AZURE_QUEUE_STORAGE_INDEX_BACKUP_QUEUE_NAME") or "backup-index-queue"


def send_message_to_index_backup_queue(datetime: str, endpoint: str, index_name: str, sort_field_value: str) -> None:
    message = IndexBackupQueue(
        datetime=datetime,
        endpoint=endpoint,
        index_name=index_name,
        sort_field_value=sort_field_value,
    )

    json_message = json.dumps(message.model_dump())
    encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(INDEX_BACKUP_QUEUE_NAME)
    queue_client.send_message(encoded_message)
