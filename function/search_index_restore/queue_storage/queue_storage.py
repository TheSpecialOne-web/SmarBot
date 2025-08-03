import base64
import json
import os

from pydantic import BaseModel

from .client import get_queue_client

INDEX_RESTORE_QUEUE_NAME = os.environ.get("AZURE_QUEUE_STORAGE_INDEX_RESTORE_QUEUE_NAME") or "restore-index-queue"


class RestoreIndexQueue(BaseModel):
    folder_name: str
    endpoint: str
    index_name: str
    last_blob_version_id: str | None = None


def send_message_to_index_restore_queue(
    folder_name: str, endpoint: str, index_name: str, last_blob_version_id: str | None = None
) -> None:
    message = RestoreIndexQueue(
        folder_name=folder_name,
        endpoint=endpoint,
        index_name=index_name,
        last_blob_version_id=last_blob_version_id,
    )

    json_message = json.dumps(message.model_dump())
    encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(INDEX_RESTORE_QUEUE_NAME)
    queue_client.send_message(encoded_message)
