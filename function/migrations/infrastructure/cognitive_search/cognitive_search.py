from logging import getLogger
from typing import Optional, TypedDict

from azure.search.documents.indexes.models import SearchIndex, SimpleField

from migrations.infrastructure.cognitive_search.client import (
    AZURE_SEARCH_SERVICE_ENDPOINT,
    AZURE_SEARCH_SERVICE_ENDPOINT_1,
    AZURE_SEARCH_SERVICE_ENDPOINT_2,
    AZURE_SEARCH_SERVICE_ENDPOINT_3,
    get_search_client,
    get_search_index_client,
)

logger = getLogger(__name__)


class IndexDocument(TypedDict):
    id: str
    bot_id: int
    data_source_id: Optional[str]
    question_answer_id: Optional[str]
    document_id: Optional[int]
    content: str
    blob_path: Optional[str]
    file_name: Optional[str]
    file_extension: Optional[str]
    page_number: Optional[int]
    created_at: str
    updated_at: str
    question: Optional[str]
    title_vector: list[float]
    content_vector: list[float]


class UrsaIndexDocument(TypedDict):
    id: str
    content: str
    file_name: str
    construction_name: str
    author: str
    path: str
    extention: str
    source_file: str
    target_facilities: str
    construction_start_date: str
    construction_end_date: str
    location: str
    year: int
    summary: str
    branch: str
    document_type: str
    parent_folder: str
    cost: int
    sourceid: str
    document_id: int | None


class UrsaSemanticIndexDocument(TypedDict):
    id: str
    content: str
    file_name: str
    construction_name: str
    author: str
    year: int
    branch: str
    full_path: str
    interpolation_path: str
    extension: str
    created_at: str
    updated_at: str
    sourceid: str
    document_id: int | None
    document_type: str
    document_folder_id: str | None


def list_endpoints() -> list[str]:
    endpoints = []
    if AZURE_SEARCH_SERVICE_ENDPOINT is not None and AZURE_SEARCH_SERVICE_ENDPOINT != "":
        endpoints.append(AZURE_SEARCH_SERVICE_ENDPOINT)
    if AZURE_SEARCH_SERVICE_ENDPOINT_1 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_1 != "":
        endpoints.append(AZURE_SEARCH_SERVICE_ENDPOINT_1)
    if AZURE_SEARCH_SERVICE_ENDPOINT_2 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_2 != "":
        endpoints.append(AZURE_SEARCH_SERVICE_ENDPOINT_2)
    if AZURE_SEARCH_SERVICE_ENDPOINT_3 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_3 != "":
        endpoints.append(AZURE_SEARCH_SERVICE_ENDPOINT_3)
    return endpoints


def list_indexes(endpoint: str) -> list[SearchIndex]:
    index_client = get_search_index_client(endpoint)
    return list(index_client.list_indexes())


def update_index(endpoint: str, index: SearchIndex) -> None:
    index_client = get_search_index_client(endpoint)
    index_client.create_or_update_index(index=index)


def get_index_document_count(index_name: str) -> int:
    index_client = get_search_client(index_name=index_name)
    return index_client.get_document_count()


def get_ursa_index_documents_by_file_name(index_name: str, file_name: str) -> list[dict]:
    index_client = get_search_client(index_name=index_name)
    _filter = f"file_name eq '{file_name}'"
    result = index_client.search("*", filter=_filter, top=1000)
    return list(result)


def get_ursa_index_document_count_without_document_id(index_name: str) -> int:
    index_client = get_search_client(index_name=index_name)
    result = index_client.search("*", filter="document_id eq null", top=0, include_total_count=True)
    return result.get_count()


def get_ursa_index_documents(index_name: str) -> list[dict]:
    index_client = get_search_client(index_name=index_name)
    result = index_client.search(
        "*",
        filter="document_id eq null",
        order_by="construction_start_date asc",  # type: ignore[arg-type]
        top=1000,
    )
    return list(result)


MAX_LIMIT = 1000


def get_index_documents(
    index_name: str,
    order_by: str = "createddate asc",
    top: int = MAX_LIMIT,
    skip: int = 0,
) -> list[dict]:
    if top > MAX_LIMIT:
        raise ValueError(f"top must be less than or equal to {MAX_LIMIT}")

    index_client = get_search_client(index_name=index_name)
    result = index_client.search(
        search_text="*",
        skip=skip,
        top=top,
        include_total_count=True,
        order_by=order_by,  # type: ignore[arg-type]
    )
    return list(result)


def upload_documents_to_index_from_batch(
    index_name: str,
    sections: list[IndexDocument] | list[UrsaIndexDocument] | list[UrsaSemanticIndexDocument],
) -> None:
    """
    インデックス化するセクションのリストを検索インデックスにインデックス化します。

    :param index_name: インデックス名
    :type index_name: str

    :param sections: インデックス化するセクションのリスト
    :type sections: list

    :return: None
    :rtype: None
    """

    search_client = get_search_client(index_name)
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 500 == 0:
            results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
            succeeded = sum([1 for r in results if r.succeeded])
            logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []
    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
        succeeded = sum([1 for r in results if r.succeeded])
        logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def add_field_to_search_index(
    endpoint: str,
    index: SearchIndex,
    field_name: str,
    field_type: str,
    filterable: bool,
    facetable: bool,
    sortable: bool,
) -> None:
    index_client = get_search_index_client(endpoint)

    field_exists = any(field.name == field_name for field in index.fields)

    if field_exists:
        logger.info(f"{index.name} already has the field {field_name}")
        return

    new_field = SimpleField(
        name=field_name,
        type=field_type,
        filterable=filterable,
        facetable=facetable,
        sortable=sortable,
    )
    index.fields.append(new_field)

    index_client.create_or_update_index(index=index)
