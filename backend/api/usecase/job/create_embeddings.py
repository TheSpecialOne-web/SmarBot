from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    tenant as tenant_domain,
)
from api.domain.models.job import MAX_DEQUEUE_COUNT
from api.domain.models.search import DocumentChunk
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.llm import ILLMService
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger

logger = get_logger()


class ICreateEmbeddingsUseCase(ABC):
    @abstractmethod
    def create_embeddings(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        dequeue_count: int,
    ) -> None:
        pass


class CreateEmbeddingsUseCase(ICreateEmbeddingsUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        cognitive_search_service: ICognitiveSearchService,
        llm_service: ILLMService,
        queue_storage_service: IQueueStorageService,
    ) -> None:
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.document_repo = document_repo
        self.cognitive_search_service = cognitive_search_service
        self.llm_service = llm_service
        self.queue_storage_service = queue_storage_service

    def create_embeddings(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        dequeue_count: int,
    ) -> None:
        try:
            self._create_embeddings(tenant_id=tenant_id, bot_id=bot_id, document_id=document_id)
        except Exception as e:
            if dequeue_count >= MAX_DEQUEUE_COUNT:
                document = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)
                document.update_status_to_failed()
                self.document_repo.update(document)
            raise e

    def _create_embeddings(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> None:
        # Get tenant
        tenant = self.tenant_repo.find_by_id(id=tenant_id)
        logger.info(f"tenant: {tenant.model_dump_json()}")

        # Get bot
        bot = self.bot_repo.find_by_id_and_tenant_id(id=bot_id, tenant_id=tenant_id)
        logger.info(f"bot: {bot.model_dump_json()}")

        if not bot.search_method:
            raise ValueError("search_method is not set")
        if not bot.search_method.should_create_embeddings():
            raise ValueError(f"Invalid search method: {bot.search_method}")

        # Get document
        document = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)
        logger.info(f"document: {document.model_dump_json()}")

        # Get documents without vectors
        index_document_count = self.cognitive_search_service.get_document_count_without_vectors(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )

        # If there are no documents without vectors, update the status of the document to completed
        if index_document_count == 0:
            document.update_status_to_completed()
            self.document_repo.update(document)
            logger.info("No documents without vectors")
            return
        logger.info(f"remaining documents: {index_document_count}")

        # Get documents without vectors
        MAX_DOCUMENTS_TO_PROCESS = 100
        index_documents = self.cognitive_search_service.get_documents_without_vectors(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
            limit=MAX_DOCUMENTS_TO_PROCESS,
        )

        FLAG_KEY = "create-embeddings-in-foreign-regions"
        use_foreign_region = get_feature_flag(
            flag_key=FLAG_KEY,
            tenant_id=tenant.id,
            tenant_name=tenant.name,
        )

        # Add embeddings to index documents
        index_documents_with_vectors, is_error = self._create_or_update_embeddings_to_index_documents(
            index_documents=index_documents,
            search_method=bot.search_method,
            use_foreign_region=use_foreign_region,
        )

        # Upload documents with vectors
        if len(index_documents_with_vectors) > 0:
            is_all_uploaded = self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=tenant.search_service_endpoint,
                index_name=tenant.index_name,
                documents=index_documents_with_vectors,
            )
            if not is_all_uploaded:
                is_error = True
            logger.info(f"uploaded {len(index_documents_with_vectors)} documents")

        # Update the status of the document to completed if there are no errors and all documents have been processed
        if is_error is False and index_document_count <= MAX_DOCUMENTS_TO_PROCESS:
            document.update_status_to_completed()
            self.document_repo.update(document)
            logger.info("created embeddings for all documents")

            if document.external_id is not None:
                self.queue_storage_service.send_message_to_sync_document_path_queue(
                    tenant_id=tenant_id,
                    bot_id=bot_id,
                    document_folder_id=document.document_folder_id,
                    document_ids=[document_id],
                )
                logger.info("sent message to sync document path queue")

            self.queue_storage_service.send_message_to_calculate_storage_usage_queue(
                tenant_id=tenant_id,
                bot_id=bot_id,
                document_id=document_id,
            )
            logger.info("sent message to calculate storage usage")
            return

        # If there are errors or there are still documents to process, send a message to the create embeddings queue
        self.queue_storage_service.send_message_to_create_embeddings_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_id=document_id,
        )
        logger.info(
            f"sent message to create embeddings queue. Remaining {index_document_count - len(index_documents_with_vectors)} documents"
        )

    def _create_or_update_embeddings_to_index_documents(
        self,
        index_documents: list[DocumentChunk],
        search_method: bot_domain.SearchMethod,
        use_foreign_region: bool,
    ) -> tuple[list[DocumentChunk], bool]:
        is_error = False
        index_documents_with_vectors: list[DocumentChunk] = []
        for index_document in index_documents:
            try:
                content_vector = self.llm_service.generate_embeddings(
                    text=index_document.content_without_folder_path,
                    use_foreign_region=use_foreign_region,
                )
                index_document.add_content_vector(content_vector)
            except Exception as e:
                # 失敗した場合はループを抜けて、エンべディングを作成できたところまでアップロードする
                logger.warning(f"failed to generate embeddings: {e}")
                is_error = True
                break

            # semantic_hybrid以外の場合はタイトルもベクトル化
            if search_method != bot_domain.SearchMethod.SEMANTIC_HYBRID:
                try:
                    title_vector = self.llm_service.generate_embeddings(
                        text=index_document.file_name or "",
                        use_foreign_region=use_foreign_region,
                    )
                    index_document.add_title_vector(title_vector)
                except Exception as e:
                    # 失敗した場合はループを抜けて、エンべディングを作成できたところまでアップロードする
                    logger.warning(f"failed to generate embeddings: {e}")
                    is_error = True
                    break

            # ベクトル化が完了したドキュメントはis_vectorizedをTrueにする
            index_document.update_is_vectorized_true()
            index_documents_with_vectors.append(index_document)
        return index_documents_with_vectors, is_error
