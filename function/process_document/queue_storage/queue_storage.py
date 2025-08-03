import base64
import os

from ..types import CalculateStorageUsageQueue, CreateEmbeddingsQueue, SyncDocumentPathQueue
from .client import get_queue_client

CREATE_EMBEDDINGS_QUEUE_NAME = (
    os.environ.get("AZURE_QUEUE_STORAGE_CREATE_EMBEDDINGS_QUEUE_NAME") or "create-embeddings-queue"
)
CALCULATE_STORAGE_USAGE_QUEUE_NAME = (
    os.environ.get("AZURE_QUEUE_STORAGE_CALCULATE_STORAGE_USAGE_QUEUE_NAME") or "calculate-storage-usage-queue"
)
SYNC_DOCUMENT_PATH_QUEUE_NAME = (
    os.environ.get("AZURE_QUEUE_STORAGE_SYNC_DOCUMENT_PATH_QUEUE_NAME") or "sync-document-path-queue"
)


def send_message_to_create_embeddings_queue(
    tenant_id: int,
    bot_id: int,
    document_id: int,
):
    message = CreateEmbeddingsQueue(
        tenant_id=tenant_id,
        bot_id=bot_id,
        document_id=document_id,
    )
    encoded_message = base64.b64encode(message.json().encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(CREATE_EMBEDDINGS_QUEUE_NAME)
    queue_client.send_message(encoded_message)


def send_message_to_calculate_storage_usage_queue(
    tenant_id: int,
    bot_id: int,
    document_id: int,
):
    message = CalculateStorageUsageQueue(
        tenant_id=tenant_id,
        bot_id=bot_id,
        document_id=document_id,
    )
    encoded_message = base64.b64encode(message.json().encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(CALCULATE_STORAGE_USAGE_QUEUE_NAME)
    queue_client.send_message(encoded_message)


def send_message_to_sync_document_path_queue(
    tenant_id: int,
    bot_id: int,
    document_folder_id: str,
    document_ids: list[int],
):
    message = SyncDocumentPathQueue(
        tenant_id=tenant_id,
        bot_id=bot_id,
        document_folder_id=document_folder_id,
        document_ids=document_ids,
    )
    encoded_message = base64.b64encode(message.json().encode("utf-8")).decode("utf-8")
    queue_client = get_queue_client(SYNC_DOCUMENT_PATH_QUEUE_NAME)
    queue_client.send_message(encoded_message)
