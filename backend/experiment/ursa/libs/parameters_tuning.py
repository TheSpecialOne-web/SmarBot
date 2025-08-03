import os
import time

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    ScoringProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    TextWeights,
)
from dotenv import load_dotenv

MAX_RETRIES = 5
INDEX_NAME = "ursa-major-hybrid-phase1"
EXPERIMENT_SEMANTIC_CONFIG = "experiment-semantic-config"
EXPERIMENT_SCORING_PROFILE = "experimentScoringProfile"
azure_credential = DefaultAzureCredential()

load_dotenv()
AZURE_SEARCH_SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_SERVICE_ENDPOINT_1 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_1")
AZURE_SEARCH_SERVICE_ENDPOINT_2 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_2")
AZURE_SEARCH_SERVICE_ENDPOINT_3 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_3")


def get_search_index_client(endpoint: str) -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=endpoint,
        credential=azure_credential,
    )


def set_semantic_config(params: dict) -> dict:
    """
    Azure AI Searchのセマンティック設定を行う。
    Args:
        params (dict): セマンティック設定のパラメータ。以下の項目を含む。
            title_field (str): タイトルとして使用するフィールド名、一つのフィールドのみ指定可能。
            content_fields (list): コンテンツとして使用するフィールドのリスト。
            keywords_fields (list): キーワードとして使用するフィールドのリスト。
    例:
        params = {
            "title_field": "file_name",
            "content_fields": ['file_name', 'full_path', 'content'],
            "keywords_fields": []
        }
        または
        params = {
            "semantic_config": {
                "title_field": "file_name",
                "content_fields": ['file_name', 'full_path', 'content'],
                "keywords_fields": []
            }
        }
    """
    params = params.get("semantic_config", params)
    title_field = params.get("title_field", "file_name")
    content_fields = params.get("content_fields", ["file_name", "full_path", "content"])
    keywords_fields = params.get("keywords_fields", [])
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=EXPERIMENT_SEMANTIC_CONFIG,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name=title_field),
                    content_fields=[SemanticField(field_name=field) for field in content_fields],
                    keywords_fields=[SemanticField(field_name=field) for field in keywords_fields],
                ),
            ),
        ]
    )
    semantic_config = {
        "semantic_config": {
            "title_field": title_field,
            "content_fields": content_fields,
            "keywords_fields": keywords_fields,
        }
    }
    for i in range(MAX_RETRIES):
        try:
            if AZURE_SEARCH_SERVICE_ENDPOINT_1 is None:
                raise Exception("AZURE_SEARCH_SERVICE_ENDPOINT_1 is not set.")
            index_client = get_search_index_client(AZURE_SEARCH_SERVICE_ENDPOINT_1)
            index = index_client.get_index(INDEX_NAME)
            index.semantic_search = semantic_search
            index_client.create_or_update_index(index=index, allow_index_downtime=True)
            print(f"Updated semantic configuration for index: {INDEX_NAME}, semantic_parameters: {semantic_config}")
            return semantic_config
        except Exception as e:
            print(f"Failed to update semantic configuration: {e!s}, retry {i + 1}/{MAX_RETRIES}")
            time.sleep(3)
    raise Exception("Failed to update semantic configuration")


def set_bm25_weights(params: dict) -> dict:
    """
    Azure AI Search の BM25 パラメータを設定する。
    Args:
        params (dict): BM25 パラメータを含む辞書。
            - b (float): BM25 の b パラメータ。0 から 1 の範囲で指定。
            - k1 (float): BM25 の k1 パラメータ。通常 0 から 3.0 の範囲で指定。
    例:
        params = {
            "b": 0.75,
            "k1": 1.2
        }
        または
        params = {
            "bm25_weights": {
                "b": 0.75,
                "k1": 1.2
    """
    params = params.get("bm25", params)
    b = params.get("b", 0.75)
    k1 = params.get("k1", 1.2)
    bm25_weights = {"bm25_weights": {"b": b, "k1": k1}}
    for i in range(MAX_RETRIES):
        try:
            if AZURE_SEARCH_SERVICE_ENDPOINT_1 is None:
                raise Exception("AZURE_SEARCH_SERVICE_ENDPOINT_1 is not set.")
            index_client = get_search_index_client(AZURE_SEARCH_SERVICE_ENDPOINT_1)
            index = index_client.get_index(INDEX_NAME)
            index.similarity = {"@odata.type": "#Microsoft.Azure.Search.BM25Similarity", "b": b, "k1": k1}
            index_client.create_or_update_index(index=index, allow_index_downtime=True)
            updated_index = index_client.get_index(INDEX_NAME)
            print(f"updated index bm25 parameters: {updated_index.similarity}, bm25_parameters: {bm25_weights}")
            return bm25_weights
        except Exception as e:
            print(f"Failed to update bm25 parameters: {e!s}, retry {i + 1}/{MAX_RETRIES}")
            time.sleep(3)
    raise Exception("Failed to update bm25 parameters")


def set_scoring_profile(params: dict) -> dict:
    """
    Azure AI SearchのScoring Profileを設定する。
    Args:
        params: Scoring Profileの設定パラメータ
            - file_name_weight (int): ファイル名の重み。
            - construction_name_weight (int): 工事名の重み。
            - interpolation_path_weight (int): 補間パスの重み。
            - content_weight (int): コンテンツの重み。
    例:
        params = {
            "file_name_weight": 2,
            "construction_name_weight": 0.5,
            "interpolation_path_weight": 0.5
        }
        または
        params = {
            "scoring_profile_weights": {
                "file_name_weight": 2,
                "construction_name_weight": 0.5,
                "interpolation_path_weight": 0.5
            }
    """
    params = params.get("scoring_profile", params)
    file_name_weight = params.get("file_name_weight", 2)
    construction_name_weight = params.get("construction_name_weight", 0.5)
    interpolation_path_weight = params.get("interpolation_path_weight", 0.5)
    content_weight = params.get("content_weight", None)

    weights = {}
    if file_name_weight and file_name_weight > 0:
        weights["file_name"] = file_name_weight
    if construction_name_weight and construction_name_weight > 0:
        weights["construction_name"] = construction_name_weight
    if interpolation_path_weight and interpolation_path_weight > 0:
        weights["interpolation_path"] = interpolation_path_weight
    if content_weight and content_weight > 0:
        weights["content"] = content_weight
    text_weights = TextWeights(weights=weights)
    scoring_profile = ScoringProfile(
        name=EXPERIMENT_SCORING_PROFILE, text_weights=text_weights, function_aggregation="sum"
    )
    scoring_profile_weights = {"scoring_profile_weights": weights}
    for i in range(MAX_RETRIES):
        try:
            if AZURE_SEARCH_SERVICE_ENDPOINT_1 is None:
                raise Exception("AZURE_SEARCH_SERVICE_ENDPOINT_1 is not set.")
            index_client = get_search_index_client(AZURE_SEARCH_SERVICE_ENDPOINT_1)
            index = index_client.get_index(INDEX_NAME)
            index.scoring_profiles = [scoring_profile]
            index_client.create_or_update_index(index=index, allow_index_downtime=True)
            print(f"Updated scoring profile for index: {INDEX_NAME}, scoring_parameters: {scoring_profile_weights}")
            return scoring_profile_weights
        except Exception as e:
            print(f"Failed to update scoring profile: {e!s}, retry {i + 1}/{MAX_RETRIES}")
            time.sleep(3)
    raise Exception("Failed to update scoring profile")
