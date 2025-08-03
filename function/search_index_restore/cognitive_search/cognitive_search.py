from .client import get_search_client


def upload_documents(endpoint: str, index_name: str, documents: list[dict]) -> None:
    index_client = get_search_client(endpoint=endpoint, index_name=index_name)

    batch = []
    for d in documents:
        batch.append(d)
        if len(batch) == 250:
            index_client.upload_documents(documents=batch)
            batch = []
    if len(batch) > 0:
        index_client.upload_documents(documents=batch)
