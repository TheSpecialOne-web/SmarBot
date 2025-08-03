from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from pydantic import RootModel, StrictStr


class IndexName(RootModel[StrictStr]):
    root: StrictStr


VECTOR_CONFIG_NAME = "my-vector-config"
VECTOR_PROFILE_NAME = "my-vector-config-profile"
SEMANTIC_CONFIG_NAME = "my-semantic-config"
VECTOR_SEARCH_DIMENSIONS = 1536


def get_index_settings(index_name: IndexName) -> SearchIndex:
    return SearchIndex(
        name=index_name.root,
        fields=[
            SimpleField(name="id", type="Edm.String", key=True),
            SimpleField(name="bot_id", type="Edm.Int64", filterable=True),
            SimpleField(name="data_source_id", type="Edm.String", filterable=True),
            SimpleField(name="document_id", type="Edm.Int64", filterable=True),
            SearchableField(name="content", type="Edm.String", analyzer_name="ja.microsoft"),
            SimpleField(name="blob_path", type="Edm.String", filterable=True),
            SimpleField(name="file_name", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="file_extension", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="page_number", type="Edm.Int64"),
            SimpleField(name="question", type="Edm.String", facetable=True),
            SimpleField(name="created_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="updated_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="question_answer_id", type="Edm.String", filterable=True),
            SimpleField(name="document_folder_id", type="Edm.String", filterable=True, sortable=True),
            SimpleField(name="external_id", type="Edm.String", filterable=True, sortable=True),
            SimpleField(name="parent_external_id", type="Edm.String", filterable=True, sortable=True),
            SearchField(
                name="title_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=VECTOR_SEARCH_DIMENSIONS,
                vector_search_profile_name=VECTOR_PROFILE_NAME,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=VECTOR_SEARCH_DIMENSIONS,
                vector_search_profile_name=VECTOR_PROFILE_NAME,
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name=VECTOR_CONFIG_NAME,
                    kind="hnsw",
                    parameters=HnswParameters(m=4, ef_construction=400, ef_search=500, metric="cosine"),
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name=VECTOR_PROFILE_NAME,
                    algorithm_configuration_name=VECTOR_CONFIG_NAME,
                )
            ],
        ),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name=SEMANTIC_CONFIG_NAME,
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="file_name"),
                        content_fields=[SemanticField(field_name="content")],
                    ),
                )
            ]
        ),
    )
