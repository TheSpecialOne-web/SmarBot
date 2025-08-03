from .client import get_blob_container


def upload_to_blob(path: str, data: str) -> None:
    client = get_blob_container()
    client.upload_blob(
        name=path,
        data=data,
        overwrite=True,
    )
