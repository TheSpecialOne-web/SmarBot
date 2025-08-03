from pydantic import BaseModel

from .client import (
    AZURE_SEARCH_SERVICE_ENDPOINT,
    AZURE_SEARCH_SERVICE_ENDPOINT_1,
    AZURE_SEARCH_SERVICE_ENDPOINT_2,
    AZURE_SEARCH_SERVICE_ENDPOINT_3,
    get_search_index_client,
)


class SearchIndex(BaseModel):
    endpoint: str
    name: str


def list_indexes() -> list[SearchIndex]:
    endpoints = [
        AZURE_SEARCH_SERVICE_ENDPOINT,
        AZURE_SEARCH_SERVICE_ENDPOINT_1,
        AZURE_SEARCH_SERVICE_ENDPOINT_2,
        AZURE_SEARCH_SERVICE_ENDPOINT_3,
    ]
    search_indexes = []
    for endpoint in endpoints:
        if not endpoint or endpoint == "":
            continue
        search_index_client = get_search_index_client(endpoint)
        indexes = search_index_client.list_indexes()
        for index in indexes:
            search_indexes.append(SearchIndex(endpoint=endpoint, name=index.name))
    return search_indexes
