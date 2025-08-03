import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

azure_credential = DefaultAzureCredential()

AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT = os.environ.get("AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT")
AZURE_INDEX_BACKUP_BLOB_CONTAINER = os.environ.get("AZURE_INDEX_BACKUP_BLOB_CONTAINER")


def get_blob_container() -> ContainerClient:
    if not AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT:
        raise ValueError("AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT is not set")
    if not AZURE_INDEX_BACKUP_BLOB_CONTAINER:
        raise ValueError("AZURE_INDEX_BACKUP_BLOB_CONTAINER is not set")
    blob_client = BlobServiceClient(
        account_url=f"https://{AZURE_INDEX_BACKUP_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=azure_credential,
    )
    return blob_client.get_container_client(AZURE_INDEX_BACKUP_BLOB_CONTAINER)
