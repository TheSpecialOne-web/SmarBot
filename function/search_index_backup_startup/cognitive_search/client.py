import os

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

AZURE_SEARCH_SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_SERVICE_ENDPOINT_1 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_1")
AZURE_SEARCH_SERVICE_ENDPOINT_2 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_2")
AZURE_SEARCH_SERVICE_ENDPOINT_3 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_3")

azure_credential = DefaultAzureCredential()


def get_search_index_client(endpoint: str) -> SearchIndexClient:
    if endpoint not in [
        AZURE_SEARCH_SERVICE_ENDPOINT,
        AZURE_SEARCH_SERVICE_ENDPOINT_1,
        AZURE_SEARCH_SERVICE_ENDPOINT_2,
        AZURE_SEARCH_SERVICE_ENDPOINT_3,
    ]:
        raise ValueError(f"Invalid endpoint: {endpoint}")
    return SearchIndexClient(
        endpoint=endpoint,
        credential=azure_credential,
    )
