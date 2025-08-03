from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    ScoringProfile,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    TextWeights,
    VectorSearch,
    VectorSearchProfile,
)

from api.domain.models.bot import SearchMethod
from api.domain.models.search import IndexName
from api.libs.exceptions import BadRequest

URSA_FIELDS = [
    SimpleField(name="id", type="Edm.String", key=True),
    SearchableField(name="content", type="Edm.String", analyzer_name="ja.microsoft"),
    SimpleField(name="file_name", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True),
    SearchableField(
        name="construction_name",
        type="Edm.String",
        analyzer_name="ja.microsoft",
        filterable=True,
        facetable=True,
    ),
    SearchableField(name="author", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="year", type="Edm.Int32", filterable=True, sortable=True, facetable=True),
    SearchableField(name="branch", type="Edm.String", filterable=True, sortable=True, facetable=True),
    SearchableField(name="summary", type="Edm.String", filterable=True, facetable=True),
    SearchableField(name="document_type", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="parent_folder", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="cost", type="Edm.Int32", filterable=True, sortable=True, facetable=True),
    SearchableField(name="path", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True),
    SimpleField(name="extention", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True),
    SimpleField(name="source_file", type="Edm.String", filterable=True, facetable=True),
    SearchableField(name="instruments", type="Collection(Edm.String)", filterable=True, facetable=True),
    SearchableField(name="target_facilities", type="Collection(Edm.String)", filterable=True, facetable=True),
    SimpleField(
        name="construction_start_date", type="Edm.DateTimeOffset", filterable=True, sortable=True, facetable=True
    ),
    SimpleField(
        name="construction_end_date", type="Edm.DateTimeOffset", filterable=True, sortable=True, facetable=True
    ),
    SearchableField(name="location", type="Collection(Edm.String)", filterable=True, facetable=True),
    SimpleField(name="sourceid", type="Edm.String", filterable=True, sortable=True, facetable=True),
    SimpleField(name="document_id", type="Edm.Int64", filterable=True),
    SimpleField(name="document_folder_id", type="Edm.String", filterable=True, sortable=True),
    SimpleField(name="external_id", type="Edm.String", filterable=True, sortable=True),
    SimpleField(name="parent_external_id", type="Edm.String", filterable=True, sortable=True),
]

VECTOR_CONFIG_NAME = "my-vector-config"
VECTOR_PROFILE_NAME = "my-vector-config-profile"
SEMANTIC_CONFIG_NAME = "my-semantic-config"
MY_SCORING_PROFILE = "my-scoring-profile"


URSA_SEMANTIC_FIELDS = [
    SimpleField(name="id", type="Edm.String", key=True),
    SearchableField(name="content", type="Edm.String", analyzer_name="ja.microsoft"),
    SearchableField(
        name="file_name", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True
    ),
    SearchableField(
        name="construction_name",
        type="Edm.String",
        analyzer_name="ja.microsoft",
        filterable=True,
        facetable=True,
    ),
    SearchableField(name="author", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="year", type="Edm.Int32", filterable=True, sortable=True, facetable=True),
    SearchableField(name="branch", type="Edm.String", filterable=True, sortable=True, facetable=True),
    SearchableField(name="document_type", type="Edm.String", filterable=True, facetable=True),
    SearchableField(
        name="interpolation_path", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True
    ),
    SimpleField(name="full_path", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True),
    SimpleField(name="extension", type="Edm.String", analyzer_name="ja.microsoft", filterable=True, facetable=True),
    SimpleField(name="source_file", type="Edm.String", filterable=True, facetable=True),
    SimpleField(name="created_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
    SimpleField(name="updated_at", type="Edm.DateTimeOffset", filterable=True, sortable=True),
    SimpleField(name="sourceid", type="Edm.String", filterable=True, sortable=True, facetable=True),
    SimpleField(name="document_id", type="Edm.Int64", filterable=True),
    SimpleField(name="document_folder_id", type="Edm.String", filterable=True, sortable=True),
    SimpleField(name="external_id", type="Edm.String", filterable=True, sortable=True),
    SimpleField(name="parent_external_id", type="Edm.String", filterable=True, sortable=True),
]


def get_bot_index_settings(index_name: IndexName, search_method: SearchMethod) -> SearchIndex:
    if search_method == SearchMethod.URSA:  # 2024/08までのURSAのindex設定
        return SearchIndex(
            name=index_name.root,
            fields=URSA_FIELDS,
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=None,
                            content_fields=[
                                SemanticField(field_name="content"),
                            ],
                        ),
                    )
                ]
            ),
        )
    if search_method == SearchMethod.URSA_SEMANTIC:  # 2024/08に追加されたURSAのindex設定
        return SearchIndex(
            name=index_name.root,
            fields=URSA_SEMANTIC_FIELDS,
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name=SEMANTIC_CONFIG_NAME,
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="file_name"),
                            content_fields=[
                                SemanticField(field_name="file_name"),
                                SemanticField(field_name="full_path"),
                                SemanticField(field_name="content"),
                            ],
                        ),
                    )
                ]
            ),
            scoring_profiles=[
                ScoringProfile(
                    name=MY_SCORING_PROFILE,
                    text_weights=TextWeights(
                        weights={
                            "file_name": 2,
                            "construction_name": 0.5,
                            "interpolation_path": 0.5,
                        },
                    ),
                ),
            ],
        )

    raise BadRequest(f"不正な検索方法です: {search_method}")


def get_tenant_index_settings(index_name: IndexName) -> SearchIndex:
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
            SimpleField(name="is_vectorized", type="Edm.Boolean", filterable=True),
            SimpleField(name="external_id", type="Edm.String", filterable=True, sortable=True),
            SimpleField(name="parent_external_id", type="Edm.String", filterable=True, sortable=True),
            SearchField(
                name="title_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name=VECTOR_PROFILE_NAME,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
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
