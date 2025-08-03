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


def add_is_vectorized_field_to_search_index():
    FIELD_NAME = "is_vectorized"
    COMMON_VECTOR_FIELD = "content_vector"
    endpoints = list_endpoints()
    for endpoint in endpoints:
        indexes = list_indexes(endpoint)
        for index in indexes:
            if COMMON_VECTOR_FIELD not in [field.name for field in index.fields]:
                logger.info(f"skipped {FIELD_NAME} field to {index.name} index in {endpoint}")
                continue
            add_field_to_search_index(
                endpoint=endpoint,
                index=index,
                field_name=FIELD_NAME,
                field_type="Edm.Boolean",
                filterable=True,
                facetable=False,
                sortable=False,
            )
            logger.info(f"added {FIELD_NAME} field to {index.name} index in {endpoint}")
        logger.info(f"added {FIELD_NAME} field to all indexes in {endpoint}")
    logger.info(f"added {FIELD_NAME} field to all indexes")
