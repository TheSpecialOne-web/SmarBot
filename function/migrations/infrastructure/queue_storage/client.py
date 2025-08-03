import os

from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueClient, QueueServiceClient

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


def get_queue_client(queue_name: str) -> QueueClient:
    return queue_client.get_queue_client(queue_name)
