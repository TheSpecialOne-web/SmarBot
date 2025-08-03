from io import BytesIO

from azure.storage.blob import BlobProperties

from .client import get_blob_container


def list_blobs(folder_name: str) -> list[BlobProperties]:
    client = get_blob_container()
    return list(client.list_blobs(name_starts_with=folder_name))


def download_blob(path: str) -> bytes:
    client = get_blob_container()

    with BytesIO() as bytes_stream:
        client.download_blob(path).readinto(bytes_stream)
        return bytes_stream.getvalue()
