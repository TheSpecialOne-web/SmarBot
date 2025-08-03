from logging import getLogger
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = getLogger(__name__)
logger.setLevel("INFO")

AZURE_BLOB_STORAGE_ACCOUNT = os.environ.get("AZURE_BLOB_STORAGE_ACCOUNT") or "mystorageaccount"


azure_credential = DefaultAzureCredential()

blob_client = BlobServiceClient(
    account_url=f"https://{AZURE_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=azure_credential,
)


def create_container(container_name: str):
    try:
        # container_clientはコンテナの有無に関わらず取得できる
        container_client = blob_client.get_container_client(container_name)
        # これでcontainerが存在するかどうかの確認ができる
        if container_client.exists():
            raise Exception(f"container {container_name} already exists")
    except ResourceNotFoundError:
        pass
    except Exception as e:
        raise e

    try:
        blob_client.create_container(container_name)
    except Exception as e:
        raise e


def list_blob_names(container_name: str, bot_id: int) -> list[str]:
    container_client = blob_client.get_container_client(container_name)
    if not container_client.exists():
        logger.warning(f"container {container_name} does not exist")
        return []

    blob_names = []
    prefix = f"{bot_id}/"
    for blob in container_client.list_blobs(name_starts_with=prefix):
        blob_names.append(blob.name)

    return blob_names


def copy_blobs_between_containers(
    source_container_name: str,
    source_blob_name: str,
    target_container_name: str,
    target_blob_name: str,
):
    source_container_client = blob_client.get_container_client(source_container_name)
    if not source_container_client.exists():
        logger.warning(f"source container {source_container_name} does not exist")
        return

    target_container_client = blob_client.get_container_client(target_container_name)
    if not target_container_client.exists():
        logger.warning(f"target container {target_container_name} does not exist")
        return

    source_blob_url = (
        f"https://{AZURE_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net/{source_container_name}/{source_blob_name}"
    )

    target_blob = target_container_client.get_blob_client(target_blob_name)
    target_blob.start_copy_from_url(source_blob_url)
