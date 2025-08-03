import base64
from contextlib import suppress
import json
import os
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueClient, QueueMessage, QueueServiceClient

from libs.logging import get_logger
from libs.retry import retry_azure_auth_error

AZURE_BATCH_STORAGE_ACCOUNT = os.environ.get("AZURE_BATCH_STORAGE_ACCOUNT") or ""

# AZURE_BATCH_STORAGE_ACCOUNTが空の場合はローカルのAzuriteに接続する
if AZURE_BATCH_STORAGE_ACCOUNT == "":
    queue_client = QueueServiceClient.from_connection_string(
        "DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;QueueEndpoint=http://azurite:10001/stbatchlocal;"
    )
else:
    queue_client = QueueServiceClient(
        account_url=f"https://{AZURE_BATCH_STORAGE_ACCOUNT}.queue.core.windows.net",
        credential=DefaultAzureCredential(),
    )

logger = get_logger(__name__)


def get_queue_client(queue_name: str) -> QueueClient:
    return queue_client.get_queue_client(queue_name)


@retry_azure_auth_error
def get_message(queue_name: str, visibility_timeout: int) -> QueueMessage | None:
    queue_client = get_queue_client(queue_name)
    message = queue_client.receive_message(
        visibility_timeout=visibility_timeout,
    )
    return message


def peek_messages(queue_name: str) -> list[QueueMessage]:
    queue_client = get_queue_client(queue_name)
    messages = queue_client.peek_messages()
    return messages


def read_message(message: QueueMessage) -> dict[str, Any]:
    decoded_message = base64.b64decode(message.content).decode("utf-8")
    return json.loads(decoded_message)


def reset_message_visibility(queue_name: str, message: QueueMessage) -> None:
    queue_client = get_queue_client(queue_name)
    queue_client.update_message(message.id, message.pop_receipt, visibility_timeout=0)


def delete_message(queue_name: str, message: QueueMessage) -> None:
    queue_client = get_queue_client(queue_name)
    queue_client.delete_message(message.id, message.pop_receipt)


def send_message_to_poison_queue(queue_name: str, message: QueueMessage) -> None:
    queue_client = get_queue_client(queue_name)
    with suppress(ResourceExistsError):
        queue_client.create_queue()
    queue_client.send_message(message.content)
