from azure.search.documents.indexes.models import SearchIndex

from search_index_backup.types import SortField

from .client import get_search_client, get_search_index_client


def get_index(endpoint: str, index_name: str) -> SearchIndex:
    client = get_search_index_client(endpoint=endpoint)
    return client.get_index(index_name)


def get_documents_count_after_sort_field(
    endpoint: str,
    index_name: str,
    sort_field: SortField,
) -> int:
    index_client = get_search_client(endpoint=endpoint, index_name=index_name)
    filter = ""

    if sort_field.value is not None:
        filter = f"{sort_field.key} ge {sort_field.value}"
    result = index_client.search(
        search_text="*",
        top=0,
        filter=filter,
        include_total_count=True,
        order_by=f"{sort_field.key} asc",  # type: ignore[arg-type]
    )
    return result.get_count()


MAX_LIMIT = 1000


def get_documents_after_sort_field(
    endpoint: str,
    index_name: str,
    top: int,
    sort_field: SortField,
    skip: int,
) -> list[dict]:
    index_client = get_search_client(endpoint=endpoint, index_name=index_name)
    filter = ""

    if sort_field.value is not None:
        filter = f"{sort_field.key} ge {sort_field.value}"
    result = index_client.search(
        search_text="*",
        filter=filter,
        include_total_count=True,
        top=top,
        order_by=f"{sort_field.key} asc",  # type: ignore[arg-type]
        skip=skip,
    )
    return list(result)
