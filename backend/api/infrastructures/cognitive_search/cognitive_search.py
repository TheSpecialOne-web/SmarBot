import math
import ntpath
import os
import time
from typing import Any
import unicodedata
from uuid import UUID

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType, VectorizedQuery
from tenacity import retry, stop_after_attempt, wait_exponential

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    question_answer as question_answer_domain,
)
from api.domain.models.bot import DocumentLimit, SearchMethod
from api.domain.models.data_point import (
    AdditionalInfo,
    BlobPath,
    ChunkName,
    Content,
    DataPointWithoutCiteNumber,
    PageNumber,
    Type as DataPointType,
    Url,
)
from api.domain.models.document_folder import Id as DocumentFolderId
from api.domain.models.query import Queries
from api.domain.models.question_answer import Id as QuestionAnswerId
from api.domain.models.search import (
    DocumentChunk,
    Endpoint,
    EndpointsWithPriority,
    EndpointWithPriority,
    IndexName,
    Priority,
    StorageUsage,
    UrsaDocumentChunk,
)
from api.domain.services.cognitive_search import (
    ICognitiveSearchService,
    IndexQuestionAnswerForCreate,
    IndexQuestionAnswerForUpdate,
)
from api.libs.exceptions import Conflict
from api.libs.logging import get_logger
from api.libs.retry import retry_azure_service_error

from .index_settings import MY_SCORING_PROFILE, SEMANTIC_CONFIG_NAME, get_bot_index_settings, get_tenant_index_settings

AZURE_SEARCH_SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_SERVICE_ENDPOINT_1 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_1")
AZURE_SEARCH_SERVICE_ENDPOINT_2 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_2")
AZURE_SEARCH_SERVICE_ENDPOINT_3 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_3")

MAX_TOP = 1000


class CognitiveSearchService(ICognitiveSearchService):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential
        self.logger = get_logger()

    def _get_search_client(self, endpoint: Endpoint, index_name: IndexName):
        if endpoint.root not in [
            AZURE_SEARCH_SERVICE_ENDPOINT,
            AZURE_SEARCH_SERVICE_ENDPOINT_1,
            AZURE_SEARCH_SERVICE_ENDPOINT_2,
            AZURE_SEARCH_SERVICE_ENDPOINT_3,
        ]:
            raise ValueError(f"Invalid endpoint: {endpoint}")
        return SearchClient(
            endpoint=endpoint.root,
            index_name=index_name.root,
            credential=self.azure_credential,
        )

    def _get_search_index_client(self, endpoint: Endpoint):
        if endpoint.root not in [
            AZURE_SEARCH_SERVICE_ENDPOINT,
            AZURE_SEARCH_SERVICE_ENDPOINT_1,
            AZURE_SEARCH_SERVICE_ENDPOINT_2,
            AZURE_SEARCH_SERVICE_ENDPOINT_3,
        ]:
            raise ValueError(f"Invalid endpoint: {endpoint}")
        return SearchIndexClient(
            endpoint=endpoint.root,
            credential=self.azure_credential,
        )

    def _create_filter_from_bot_id_and_document_id(
        self, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> str:
        return f"{bot_id.to_index_filter()} and {document_id.to_index_filter()}"

    def list_endpoints(self) -> EndpointsWithPriority:
        endpoints = []
        if AZURE_SEARCH_SERVICE_ENDPOINT is not None and AZURE_SEARCH_SERVICE_ENDPOINT != "":
            endpoints.append(
                EndpointWithPriority(
                    endpoint=Endpoint(root=AZURE_SEARCH_SERVICE_ENDPOINT),
                    priority=Priority(root=50),
                )
            )
        if AZURE_SEARCH_SERVICE_ENDPOINT_1 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_1 != "":
            endpoints.append(
                EndpointWithPriority(
                    endpoint=Endpoint(root=AZURE_SEARCH_SERVICE_ENDPOINT_1),
                    priority=Priority(root=100),
                )
            )
        if AZURE_SEARCH_SERVICE_ENDPOINT_2 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_2 != "":
            endpoints.append(
                EndpointWithPriority(
                    endpoint=Endpoint(root=AZURE_SEARCH_SERVICE_ENDPOINT_2),
                    priority=Priority(root=150),
                )
            )
        if AZURE_SEARCH_SERVICE_ENDPOINT_3 is not None and AZURE_SEARCH_SERVICE_ENDPOINT_3 != "":
            endpoints.append(
                EndpointWithPriority(
                    endpoint=Endpoint(root=AZURE_SEARCH_SERVICE_ENDPOINT_3),
                    priority=Priority(root=200),
                )
            )
        return EndpointsWithPriority(root=endpoints)

    def list_index_names(self, endpoint: Endpoint) -> list[IndexName]:
        index_client = self._get_search_index_client(endpoint=endpoint)
        indexes = index_client.list_indexes()
        return [IndexName(root=index.name) for index in indexes]

    def create_bot_index(self, endpoint: Endpoint, index_name: IndexName, search_method: SearchMethod):
        index_client = self._get_search_index_client(endpoint=endpoint)

        try:
            existing_index = index_client.get_index(index_name.root)
            if existing_index:
                raise Conflict(f"インデックス {index_name} が既に存在します")
        except ResourceNotFoundError:
            pass

        index = get_bot_index_settings(index_name, search_method)
        index_client.create_index(index)

    def create_tenant_index(self, endpoint: Endpoint, index_name: IndexName):
        index_client = self._get_search_index_client(endpoint=endpoint)

        try:
            existing_index = index_client.get_index(index_name.root)
            if existing_index:
                raise Conflict(f"インデックス {index_name} が既に存在します")
        except ResourceNotFoundError:
            pass

        index = get_tenant_index_settings(index_name)
        index_client.create_index(index)

    def add_question_answer_to_tenant_index(
        self, endpoint: Endpoint, index_name: IndexName, index_question_answer: IndexQuestionAnswerForCreate
    ):
        index_question_answer_dict = index_question_answer.model_dump()
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        result = search_client.upload_documents(documents=[index_question_answer_dict])
        if not result[0].succeeded:
            raise Exception(
                f"""failed to upload question answer to index. index_name: {index_name.root} content:{index_question_answer_dict["content"]}"""
            )

    def bulk_create_question_answers_to_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answers: list[IndexQuestionAnswerForCreate],
    ) -> list[QuestionAnswerId]:
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        question_answers = [index_question_answer.model_dump() for index_question_answer in index_question_answers]
        results = search_client.upload_documents(documents=question_answers)

        successed_question_answer_ids = [
            QuestionAnswerId(root=UUID(qa.question_answer_id))
            for result in results
            for qa in index_question_answers
            if result.succeeded and qa.id == result.key
        ]
        return successed_question_answer_ids

    def _update_question_answer_in_tenant_index(
        self, search_client: SearchClient, index_question_answer_for_update: IndexQuestionAnswerForUpdate
    ):
        # パラメーターの取得
        search_results = search_client.search(
            "*",
            filter=index_question_answer_for_update.to_index_filter(),
            top=1,
            include_total_count=True,
        )
        index_question_answer = next(iter(search_results))

        # パラメーターの更新
        update_question_answer_params = index_question_answer_for_update.to_update_params()
        for key, value in update_question_answer_params.model_dump().items():
            index_question_answer[key] = value

        upload_result = search_client.upload_documents(documents=[index_question_answer])
        if not upload_result[0].succeeded:
            raise Exception(
                f"""failed to update question answer to index. question_answer_id: {index_question_answer_for_update.question_answer_id} content:{index_question_answer["content"]}"""
            )

    def update_question_answer_in_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answer_for_update: IndexQuestionAnswerForUpdate,
    ):
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        self._update_question_answer_in_tenant_index(
            search_client=search_client, index_question_answer_for_update=index_question_answer_for_update
        )

    def bulk_update_question_answers_in_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answers_for_update: list[IndexQuestionAnswerForUpdate],
    ) -> list[QuestionAnswerId]:
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        successed_question_answer_ids: list[QuestionAnswerId] = []
        for index_question_answer_for_update in index_question_answers_for_update:
            try:
                self._update_question_answer_in_tenant_index(
                    search_client=search_client, index_question_answer_for_update=index_question_answer_for_update
                )
                successed_question_answer_ids.append(
                    QuestionAnswerId(root=UUID(index_question_answer_for_update.question_answer_id))
                )
            except Exception:
                self.logger.error(
                    f"failed to update question answer to index: {index_question_answer_for_update.question_answer_id}"
                )
                continue
        return successed_question_answer_ids

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_documents_from_index_by_bot_id(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: bot_domain.Id,
    ):
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        while True:
            results = search_client.search(
                "*",
                filter=bot_id.to_index_filter(),
                top=1000,
                include_total_count=True,
            )
            if results.get_count() == 0:
                break
            search_client.delete_documents(documents=[{"id": d["id"]} for d in results])
            time.sleep(2)

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_documents_from_index_by_document_id(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        document_id: document_domain.Id,
    ):
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        while True:
            results = search_client.search(
                "*",
                filter=document_id.to_index_filter(),
                top=1000,
                include_total_count=True,
            )
            if results.get_count() == 0:
                break
            search_client.delete_documents(documents=[{"id": d["id"]} for d in results])
            time.sleep(2)

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_documents_from_index_by_document_folder_id(
        self, endpoint: Endpoint, index_name: IndexName, document_folder_id: DocumentFolderId
    ):
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        while True:
            results = search_client.search(
                "*",
                filter=document_folder_id.to_index_filter(),
                top=1000,
                include_total_count=True,
            )
            if results.get_count() == 0:
                break
            search_client.delete_documents(documents=[{"id": d["id"]} for d in results])
            time.sleep(2)

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_question_answer_from_tenant_index(
        self, endpoint: Endpoint, index_name: IndexName, question_answer_id: QuestionAnswerId
    ):
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        while True:
            results = search_client.search(
                "*",
                filter=question_answer_id.to_index_filter(),
                top=1000,
                include_total_count=True,
            )
            if results.get_count() == 0:
                break
            search_client.delete_documents(documents=[{"id": d["id"]} for d in results])
            time.sleep(2)

    def _search_raw_document(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        search_text: str,
        document_limit: int,
        embeddings: list[float],
        filter: str = "",
        search_method: str = SearchMethod.BM25,
    ):
        # 検索で取得するフィールド
        search_fields = [
            "file_name",
            "file_extension",
            "page_number",
            "blob_path",
            "content",
            "question",
            "document_id",
            "question_answer_id",
        ]

        if search_method == SearchMethod.BM25:
            search_client = self._get_search_client(endpoint, index_name)
            return search_client.search(
                search_text=search_text,
                filter=filter,
                top=document_limit,
            )

        # これ以降はembeddings必須
        if len(embeddings) == 0:
            raise ValueError("embeddings must be set")

        search_client = self._get_search_client(endpoint, index_name)
        # ベクトル検索
        if search_method == SearchMethod.VECTOR:
            vector = VectorizedQuery(
                vector=embeddings,
                k_nearest_neighbors=5,
                fields="content_vector",
            )
            return search_client.search(
                search_text="",
                vector_queries=[vector],
                select=search_fields,
                filter=filter,
                top=document_limit,
            )

        # ハイブリッド検索
        if search_method == SearchMethod.HYBRID:
            vector = VectorizedQuery(
                vector=embeddings,
                k_nearest_neighbors=3,
                fields="content_vector",
            )
            return search_client.search(
                search_text=search_text,
                vector_queries=[vector],
                select=search_fields,
                filter=filter,
                top=document_limit,
            )

        # セマンティックハイブリッド検索
        if search_method == SearchMethod.SEMANTIC_HYBRID:
            vector = VectorizedQuery(
                vector=embeddings,
                k_nearest_neighbors=3,
                fields="content_vector",
            )
            search_results = search_client.search(
                search_text=search_text,
                vector_queries=[vector],
                select=search_fields,
                filter=filter,
                top=document_limit,
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name=SEMANTIC_CONFIG_NAME,
                query_caption=QueryCaptionType.EXTRACTIVE,
                query_answer=QueryAnswerType.EXTRACTIVE,
            )
            return search_results
        raise ValueError("search_method must be default, vector, cross_field, multi_field, hybrid or semantic_hybrid")

    def _search_document_for_ursa(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        query: list[str],
        filter: str,
        document_limit: int,
        search_method: str,
        additional_kwargs: dict,
    ):
        search_client = self._get_search_client(endpoint, index_name)
        # Azure AI Searchに渡す際に、空白区切りのクエリにする
        filters = ["document_id ne null"]
        if filter != "":
            filters.append(filter)
        additional_filter = additional_kwargs.get("filter")
        if additional_filter is not None:
            filters.append(additional_filter)
        filter_ = " and ".join(filters)

        if search_method == SearchMethod.URSA:
            raw_document = search_client.search(
                top=document_limit,
                search_text=" ".join(query),
                filter=filter_,
            )
        elif search_method == SearchMethod.URSA_SEMANTIC:
            # 以前のindexと現在のindexではextensionのスペルが違うため
            filter_ = filter_.replace("extention", "extension")
            raw_document = search_client.search(
                search_text=" ".join(query),
                top=document_limit,
                filter=filter_,
                query_type="semantic",
                semantic_configuration_name=SEMANTIC_CONFIG_NAME,
                scoring_profile=MY_SCORING_PROFILE,
            )

        data_points: list[DataPointWithoutCiteNumber] = []

        # 実際のセマンティック検索でのクエリはユーザ入力のままなので、表示用のためのクエリを取得
        query_for_display = additional_kwargs.get("query_for_display")
        if not isinstance(query_for_display, list):
            query_for_display = []

        for doc in raw_document:
            # query内の単語が資料内に何回出現したかを数える {"query_word1": 1, "query_word2": 5, "query_word3": 7}
            word_count_dict = self.count_query_words_in_document(query_for_display, doc, search_method)
            # 数えた回数を文字列に変換して回数を付け足す
            word_count_dict_str = {key: f"{value}回" for key, value in word_count_dict.items()}

            path = ""
            if search_method == SearchMethod.URSA:
                path = f"Z:\\{doc['branch']}\\{doc['document_type']}\\{doc['year']}年度\\{doc['construction_name']}\\{doc['path']}"
            elif search_method == SearchMethod.URSA_SEMANTIC:
                path = doc["full_path"]
            else:
                raise Exception("invalid search_method specified")

            # Windowsパス形式（\）が含まれているかチェック
            if "\\" in path:
                # Windows形式のパスからフォルダパスとファイル名を取得
                folder_path = ntpath.dirname(path)
                chunk_name = ntpath.basename(path)
            else:
                # iOS形式（/）のパスからフォルダパスとファイル名を取得
                folder_path = os.path.dirname(path)
                chunk_name = os.path.basename(path)

            # ユーザーに表形式で見せる要素
            additional_info = {
                "工事名": doc["construction_name"],
                "支社名": doc["branch"],
                "年度": doc["year"],
                "作成者": doc["author"],
                "フォルダ": folder_path,
                **word_count_dict_str,
            }

            # 安全関連の検索の場合は表示要素を変更
            if filter and "document_type eq '安全関連'" in filter:
                additional_info = {
                    "支社名": doc["branch"],
                    "年度": doc["year"],
                    **word_count_dict,
                }

            data_points.append(
                DataPointWithoutCiteNumber(
                    chunk_name=ChunkName(root=chunk_name),
                    blob_path=BlobPath(root=path),
                    content=Content(root=doc["content"]),
                    page_number=PageNumber(root=0),
                    type=DataPointType.INTERNAL,
                    url=Url(root=""),
                    document_id=document_domain.Id(value=doc["document_id"]),
                    additional_info=AdditionalInfo(root=additional_info),
                )
            )
        return data_points

    @retry_azure_service_error
    def search_documents(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        queries: Queries,
        document_limit: DocumentLimit,
        filter: str = "",
        search_method: str = SearchMethod.BM25,
        embeddings: list[float] | None = None,
        additional_kwargs: dict[str, Any] | None = None,
    ) -> list[DataPointWithoutCiteNumber]:
        if search_method in [SearchMethod.URSA, SearchMethod.URSA_SEMANTIC]:
            return self._search_document_for_ursa(
                endpoint=endpoint,
                index_name=index_name,
                query=queries.to_string_list(),
                filter=filter,
                document_limit=document_limit.root,
                search_method=search_method,
                additional_kwargs=additional_kwargs if additional_kwargs is not None else {},
            )

        raw_document = self._search_raw_document(
            endpoint=endpoint,
            index_name=index_name,
            search_text=queries.to_string(delimiter=" "),
            document_limit=document_limit.root,
            embeddings=embeddings if embeddings is not None else [],
            filter=filter,
            search_method=search_method,
        )

        data_points: list[DataPointWithoutCiteNumber] = []
        for doc in raw_document:
            question_answer_id = doc.get("question_answer_id", "")
            document_id = doc.get("document_id", "")
            # QA取得
            if question_answer_id:
                data_points.append(
                    DataPointWithoutCiteNumber(
                        chunk_name=ChunkName(root=doc["content"][:20]),
                        blob_path=BlobPath(root=""),
                        content=Content(root=doc["content"]),
                        page_number=PageNumber(root=0),
                        type=DataPointType.QUESTION_ANSWER,
                        url=Url(root=""),
                        question_answer_id=question_answer_domain.Id(root=UUID(question_answer_id)),
                    )
                )
                continue
            # ドキュメント取得
            if document_id:
                file_name = doc.get("file_name", "")
                extension = doc.get("file_extension", "")
                page_number = str(doc.get("page_number", "1"))
                if extension == "pdf":
                    chunkname = file_name + "_p" + page_number
                elif extension == "pptx":
                    chunkname = file_name + "_slide" + page_number
                elif extension == "xlsx":
                    chunkname = file_name + "_sheetnumber" + page_number
                elif extension == "docx":
                    chunkname = file_name + "_paragraph" + page_number
                else:
                    chunkname = file_name + "_chunk" + page_number

                data_points.append(
                    DataPointWithoutCiteNumber(
                        chunk_name=ChunkName(root=chunkname),
                        blob_path=BlobPath(root=doc["blob_path"]),
                        content=Content(root=doc["content"]),
                        page_number=PageNumber(root=int(page_number)),
                        type=DataPointType.INTERNAL,
                        url=Url(root=""),
                        document_id=document_domain.Id(value=document_id),
                    )
                )
                continue
        return data_points

    def count_query_words_in_document(
        self, query: list[str], doc: dict[str, Any], search_method: str
    ) -> dict[str, int]:
        """contentに含まれる単語の出現回数をカウントする

        Args:
            content (str): content

        Returns:
            dict: 単語の出現回数をカウントしたdict
        """
        if search_method == SearchMethod.URSA:
            keys = ["construction_name", "extention", "branch", "year", "author", "path", "content"]
        elif search_method == SearchMethod.URSA_SEMANTIC:
            keys = ["full_path", "content"]
        document_str = " ".join([str(doc[key]) for key in keys])  # カウント対象の文字列を作成
        normalized_document_str = unicodedata.normalize("NFKC", document_str)  # 全角半角を統一
        word_count_dict = {
            query_word: normalized_document_str.count(unicodedata.normalize("NFKC", query_word))
            for query_word in query
        }
        return word_count_dict

    def add_chunks_to_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        chunks: document_domain.ChunksForCreate,
    ):
        search_client = self._get_search_client(endpoint, index_name)
        search_client.upload_documents(documents=[chunk.value for chunk in chunks.chunks])

    def get_index_storage_usage(self, endpoint: Endpoint, index_name: IndexName) -> StorageUsage:
        index_client = self._get_search_index_client(endpoint=endpoint)
        index_statistics = index_client.get_index_statistics(index_name.root)
        return StorageUsage(
            root=index_statistics["storage_size"],
        )

    def delete_index(self, endpoint: Endpoint, index_name: IndexName) -> None:
        index_client = self._get_search_index_client(endpoint=endpoint)
        index_client.delete_index(index_name.root)

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def find_index_documents_by_bot_id_and_document_id(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> list[DocumentChunk]:
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        results: list[DocumentChunk] = []
        filter_ = f"{bot_id.to_index_filter()} and {document_id.to_index_filter()}"

        res = search_client.search(
            search_text="*",
            filter=filter_,
            top=0,
            include_total_count=True,
        )

        total_count = res.get_count()

        if total_count == 0:
            return results

        num_iterations = math.ceil(total_count / MAX_TOP)
        for i in range(num_iterations):
            result = search_client.search(
                search_text="*",
                filter=filter_,
                order_by="created_at asc",  # type: ignore[arg-type]
                top=MAX_TOP,
                skip=i * MAX_TOP,
            )
            for doc in result:
                results.append(DocumentChunk(**doc))

        return results

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def find_ursa_index_documents_by_bot_id_and_document_id(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> list[UrsaDocumentChunk]:
        try:
            search_client = self._get_search_client(endpoint, index_name)
        except ResourceNotFoundError:
            raise Exception(f"index not found. index_name: {index_name.root}")

        results: list[UrsaDocumentChunk] = []
        filter_ = document_id.to_index_filter()  # Ursaのindex構造にはbot_idは存在しないためbot_idのfilterは不要

        res = search_client.search(
            search_text="*",
            filter=filter_,
            top=0,
            include_total_count=True,
        )

        total_count = res.get_count()

        if total_count == 0:
            return results

        num_iterations = math.ceil(total_count / MAX_TOP)
        for i in range(num_iterations):
            result = search_client.search(
                search_text="*",
                filter=filter_,
                order_by="created_at asc",  # type: ignore[arg-type]
                top=MAX_TOP,
                skip=i * MAX_TOP,
            )
            for doc in result:
                results.append(UrsaDocumentChunk(**doc))

        return results

    def get_document_count_without_vectors(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> int:
        search_client = self._get_search_client(endpoint, index_name)
        filter_ = self._create_filter_from_bot_id_and_document_id(bot_id, document_id)
        res = search_client.search(
            search_text="*",
            filter=f"is_vectorized eq false and {filter_}",
            top=0,
            include_total_count=True,
        )
        return res.get_count()

    def get_documents_without_vectors(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        limit: int,
    ) -> list[DocumentChunk]:
        if limit > MAX_TOP:
            raise ValueError(f"limit must be less than or equal to {MAX_TOP}")
        index_client = self._get_search_client(endpoint=endpoint, index_name=index_name)

        filter_ = self._create_filter_from_bot_id_and_document_id(bot_id, document_id)
        result = index_client.search(
            search_text="*",
            filter=f"is_vectorized eq false and {filter_}",
            top=limit,
            include_total_count=True,
        )

        total_count = result.get_count()
        if total_count == 0:
            return []

        return [DocumentChunk(**doc) for doc in result]

    def create_or_update_document_chunks(
        self, endpoint: Endpoint, index_name: IndexName, documents: list[DocumentChunk] | list[UrsaDocumentChunk]
    ) -> bool:
        search_client = self._get_search_client(
            endpoint=endpoint,
            index_name=index_name,
        )
        results = search_client.upload_documents(
            documents=[doc.model_dump() for doc in documents],
        )
        return all(result.succeeded for result in results)

    def get_document_chunk_count_by_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> int:
        search_client = self._get_search_client(endpoint, index_name)
        filter_ = self._create_filter_from_bot_id_and_document_id(bot_id, document_id)
        res = search_client.search(
            search_text="*",
            filter=filter_,
            top=0,
            include_total_count=True,
        )
        return res.get_count()

    def get_ursa_document_chunk_count_by_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> int:
        search_client = self._get_search_client(endpoint, index_name)
        filter_ = f"{document_id.to_index_filter()}"
        res = search_client.search(
            search_text="*",
            filter=filter_,
            top=0,
            include_total_count=True,
        )
        return res.get_count()

    def find_index_documents_by_document_ids(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        document_ids: list[document_domain.Id],
        document_chunk_count: int,
    ) -> list[DocumentChunk]:
        search_client = self._get_search_client(endpoint, index_name)
        filter_ = " or ".join([document_id.to_index_filter() for document_id in document_ids])
        batch_count = math.ceil(document_chunk_count / MAX_TOP)
        all_documents: list[DocumentChunk] = []

        for offset in range(batch_count):
            batch_results = search_client.search(
                search_text="*",
                filter=filter_,
                top=MAX_TOP,
                skip=offset * MAX_TOP,
                include_total_count=True,
            )
            batch_documents = [DocumentChunk(**doc) for doc in batch_results]
            all_documents.extend(batch_documents)

        return all_documents

    def find_ursa_index_documents_by_document_ids(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        document_ids: list[document_domain.Id],
        document_chunk_count: int,
    ) -> list[UrsaDocumentChunk]:
        search_client = self._get_search_client(endpoint, index_name)
        filter_ = " or ".join([document_id.to_index_filter() for document_id in document_ids])
        batch_count = math.ceil(document_chunk_count / MAX_TOP)
        all_documents: list[UrsaDocumentChunk] = []

        for offset in range(batch_count):
            batch_results = search_client.search(
                search_text="*",
                filter=filter_,
                top=MAX_TOP,
                skip=offset * MAX_TOP,
                include_total_count=True,
            )
            batch_documents = [UrsaDocumentChunk(**doc) for doc in batch_results]
            all_documents.extend(batch_documents)

        return all_documents
