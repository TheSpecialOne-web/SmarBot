from abc import ABC, abstractmethod
import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr

from ...models.bot import SearchMethod
from ...models.bot.document_limit import DocumentLimit
from ...models.bot.id import Id as BotId
from ...models.data_point import DataPointWithoutCiteNumber
from ...models.document import ChunksForCreate
from ...models.document.id import Id as DocumentId
from ...models.document_folder import Id as DocumentFolderId
from ...models.query import Queries
from ...models.question_answer import Id as QuestionAnswerId
from ...models.search import DocumentChunk, Endpoint, EndpointsWithPriority, IndexName, StorageUsage, UrsaDocumentChunk

FLOAT_SIZE = 4
INT_SIZE = 4


def _create_uuid() -> str:
    return str(uuid.uuid4())


def _create_datetime_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class IndexQuestionAnswerForCreate(BaseModel):
    id: StrictStr = Field(default_factory=_create_uuid)
    bot_id: StrictInt
    question_answer_id: StrictStr
    content: StrictStr
    created_at: StrictStr = Field(default_factory=_create_datetime_now)
    updated_at: StrictStr = Field(default_factory=_create_datetime_now)
    content_vector: list[StrictFloat]


class IndexQuestionAnswerParamsToUpdate(BaseModel):
    content: StrictStr
    updated_at: StrictStr
    content_vector: list[StrictFloat]


class IndexQuestionAnswerForUpdate(BaseModel):
    question_answer_id: StrictStr
    content: StrictStr
    updated_at: StrictStr = Field(default_factory=_create_datetime_now)
    content_vector: list[StrictFloat]

    def to_update_params(self) -> IndexQuestionAnswerParamsToUpdate:
        return IndexQuestionAnswerParamsToUpdate(
            content=self.content,
            updated_at=self.updated_at,
            content_vector=self.content_vector,
        )

    def to_index_filter(self) -> str:
        return f"question_answer_id eq '{self.question_answer_id}'"


class ICognitiveSearchService(ABC):
    @abstractmethod
    def list_endpoints(self) -> EndpointsWithPriority:
        pass

    @abstractmethod
    def list_index_names(self, endpoint: Endpoint) -> list[IndexName]:
        pass

    @abstractmethod
    def create_bot_index(self, endpoint: Endpoint, index_name: IndexName, search_method: SearchMethod):
        pass

    @abstractmethod
    def create_tenant_index(self, endpoint: Endpoint, index_name: IndexName):
        pass

    @abstractmethod
    def add_question_answer_to_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answer: IndexQuestionAnswerForCreate,
    ):
        pass

    @abstractmethod
    def bulk_create_question_answers_to_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answers: list[IndexQuestionAnswerForCreate],
    ) -> list[QuestionAnswerId]:
        pass

    @abstractmethod
    def update_question_answer_in_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answer_for_update: IndexQuestionAnswerForUpdate,
    ):
        pass

    @abstractmethod
    def bulk_update_question_answers_in_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        index_question_answers_for_update: list[IndexQuestionAnswerForUpdate],
    ) -> list[QuestionAnswerId]:
        pass

    @abstractmethod
    def delete_documents_from_index_by_bot_id(self, endpoint: Endpoint, index_name: IndexName, bot_id: BotId):
        pass

    @abstractmethod
    def delete_documents_from_index_by_document_id(
        self, endpoint: Endpoint, index_name: IndexName, document_id: DocumentId
    ):
        pass

    @abstractmethod
    def delete_documents_from_index_by_document_folder_id(
        self, endpoint: Endpoint, index_name: IndexName, document_folder_id: DocumentFolderId
    ):
        pass

    @abstractmethod
    def delete_question_answer_from_tenant_index(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        question_answer_id: QuestionAnswerId,
    ):
        pass

    @abstractmethod
    def add_chunks_to_index(self, endpoint: Endpoint, index_name: IndexName, chunks: ChunksForCreate):
        pass

    @abstractmethod
    def get_index_storage_usage(self, endpoint: Endpoint, index_name: IndexName) -> StorageUsage:
        pass

    @abstractmethod
    def delete_index(self, endpoint: Endpoint, index_name: IndexName) -> None:
        pass

    @abstractmethod
    def search_documents(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        queries: Queries,
        document_limit: DocumentLimit,
        filter: str = "",
        search_method: SearchMethod = SearchMethod.BM25,
        embeddings: list[float] | None = None,
        additional_kwargs: dict[str, Any] | None = None,
    ) -> list[DataPointWithoutCiteNumber]:
        pass

    @abstractmethod
    def find_index_documents_by_bot_id_and_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: BotId, document_id: DocumentId
    ) -> list[DocumentChunk]:
        pass

    @abstractmethod
    def find_ursa_index_documents_by_bot_id_and_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: BotId, document_id: DocumentId
    ) -> list[UrsaDocumentChunk]:
        pass

    @abstractmethod
    def get_document_count_without_vectors(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: BotId,
        document_id: DocumentId,
    ) -> int:
        pass

    @abstractmethod
    def get_documents_without_vectors(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        bot_id: BotId,
        document_id: DocumentId,
        limit: int,
    ) -> list[DocumentChunk]:
        pass

    @abstractmethod
    def create_or_update_document_chunks(
        self,
        endpoint: Endpoint,
        index_name: IndexName,
        documents: list[DocumentChunk] | list[UrsaDocumentChunk],
    ) -> bool:
        pass

    @abstractmethod
    def get_document_chunk_count_by_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: BotId, document_id: DocumentId
    ) -> int:
        pass

    @abstractmethod
    def get_ursa_document_chunk_count_by_document_id(
        self, endpoint: Endpoint, index_name: IndexName, bot_id: BotId, document_id: DocumentId
    ) -> int:
        pass

    @abstractmethod
    def find_index_documents_by_document_ids(
        self, endpoint: Endpoint, index_name: IndexName, document_ids: list[DocumentId], document_chunk_count: int
    ) -> list[DocumentChunk]:
        pass

    @abstractmethod
    def find_ursa_index_documents_by_document_ids(
        self, endpoint: Endpoint, index_name: IndexName, document_ids: list[DocumentId], document_chunk_count: int
    ) -> list[UrsaDocumentChunk]:
        pass
