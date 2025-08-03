import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

# インデックスとストレージ周りの設定
AZURE_BLOB_STORAGE_ACCOUNT = os.environ.get("AZURE_BLOB_STORAGE_ACCOUNT")
AZURITE_BLOB_CONNECTION_STRING = (
    os.environ.get("AZURITE_BLOB_CONNECTION_STRING")
    or "DefaultEndpointsProtocol=http;AccountName=stbloblocal;AccountKey=c3RibG9ibG9jYWw=;BlobEndpoint=http://azurite:10000/stbloblocal;"
)

# Azureの認証情報を取得
azure_credential = DefaultAzureCredential()
blob_client = (
    BlobServiceClient(
        account_url=f"https://{AZURE_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=azure_credential,
    )
    if AZURE_BLOB_STORAGE_ACCOUNT is not None
    else BlobServiceClient.from_connection_string(AZURITE_BLOB_CONNECTION_STRING)
)


def get_blob_container(container_name: str) -> ContainerClient:
    return blob_client.get_container_client(container_name)
