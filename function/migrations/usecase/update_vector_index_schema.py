from logging import getLogger

from azure.search.documents.indexes.models import SearchIndex

from migrations.infrastructure.cognitive_search import (
    get_index_settings,
    list_endpoints,
    list_indexes,
    update_index,
)
from migrations.infrastructure.cognitive_search.index_settings import IndexName

logger = getLogger(__name__)
logger.setLevel("INFO")


TITLE_VECTOR_FIELD_NAME = "title_vector"
CONTENT_VECTOR_FIELD_NAME = "content_vector"


def update_vector_index_schema():
    endpoints = list_endpoints()
    for endpoint in endpoints:
        indexes = list_indexes(endpoint)
        for index in indexes:
            logger.info(f"index: {index.name}")
            if TITLE_VECTOR_FIELD_NAME not in [field.name for field in index.fields]:
                logger.info(f"index: {index.name} does not have {TITLE_VECTOR_FIELD_NAME} field")
                continue
            if CONTENT_VECTOR_FIELD_NAME not in [field.name for field in index.fields]:
                logger.info(f"index: {index.name} does not have {CONTENT_VECTOR_FIELD_NAME} field")
                continue
            index_settings = get_index_settings(IndexName(root=index.name))
            new_fields = []
            for field in index.fields:
                if field.name == TITLE_VECTOR_FIELD_NAME:
                    title_vector_field = next(
                        (f for f in index_settings.fields if f.name == TITLE_VECTOR_FIELD_NAME),
                        None,
                    )
                    new_fields.append(title_vector_field)
                elif field.name == CONTENT_VECTOR_FIELD_NAME:
                    content_vector_field = next(
                        (f for f in index_settings.fields if f.name == CONTENT_VECTOR_FIELD_NAME),
                        None,
                    )
                    new_fields.append(content_vector_field)
                else:
                    new_fields.append(field)
            new_index = SearchIndex(
                name=index.name,
                fields=new_fields,
                vector_search=index_settings.vector_search,
                semantic_search=index_settings.semantic_search,
            )
            try:
                update_index(endpoint, new_index)
            except Exception as e:
                logger.error(f"failed to update index: {e}")
                raise Exception(f"failed to update index: {e}")

            logger.info(f"index schema updated: {index.name}")

        logger.info(f"all indexes updated for endpoint: {endpoint}")

    logger.info("all indexes updated")
