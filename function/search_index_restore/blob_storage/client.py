import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

azure_credential = DefaultAzureCredential()

AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT = os.environ.get("AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT") or ""
AZURE_INDEX_BACKUP_BLOB_CONTAINER = os.environ.get("AZURE_INDEX_BACKUP_BLOB_CONTAINER") or ""


def get_blob_container() -> ContainerClient:
    blob_client = BlobServiceClient(
        account_url=f"https://{AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=azure_credential,
    )
    return blob_client.get_container_client(AZURE_INDEX_BACKUP_BLOB_CONTAINER)
