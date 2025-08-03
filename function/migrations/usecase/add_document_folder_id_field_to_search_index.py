import logging

from migrations.infrastructure.cognitive_search import (
    add_field_to_search_index,
    list_endpoints,
    list_indexes,
)

azure_http_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_http_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def add_document_folder_id_field_to_search_index():
    FIELD_NAME = "document_folder_id"
    endpoints = list_endpoints()
    for endpoint in endpoints:
        indexes = list_indexes(endpoint)
        for index in indexes:
            add_field_to_search_index(
                endpoint=endpoint,
                index=index,
                field_name=FIELD_NAME,
                field_type="Edm.String",
                filterable=True,
                facetable=False,
                sortable=True,
            )
            logger.info(f"added {FIELD_NAME} field to {index.name} index in {endpoint}")
        logger.info(f"added {FIELD_NAME} field to all indexes in {endpoint}")
    logger.info(f"added {FIELD_NAME} field to all indexes")
