from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.models.data_point.blob_path import BlobPath
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.cognitive_search.cognitive_search import ICognitiveSearchService
from api.libs.logging import get_logger


class ISyncDocumentNameUseCase(ABC):
    @abstractmethod
    def sync_document_name(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        pass


class SyncDocumentNameUseCase(ISyncDocumentNameUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        document_repo: document_domain.IDocumentRepository,
        cognitive_search_service: ICognitiveSearchService,
        queue_storage_service: IQueueStorageService,
    ):
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.document_folder_repo = document_folder_repo
        self.document_repo = document_repo
        self.cognitive_search_service = cognitive_search_service
        self.queue_storage_service = queue_storage_service
        self.logger = get_logger()

    def _create_blob_path(
        self,
        bot_id: bot_domain.Id,
        document: document_domain.Document,
        root_folder: document_folder_domain.DocumentFolder,
    ) -> BlobPath:
        is_root_folder = document.document_folder_id == root_folder.id
        return BlobPath(
            root=(
                f"{bot_id.value}/{document.name.value}.{document.file_extension.value}"
                if is_root_folder
                else f"{bot_id.value}/{document.document_folder_id.root}/{document.name.value}.{document.file_extension.value}"
            )
        )

    def sync_document_name(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        is_ursa = bot.approach == bot_domain.Approach.URSA

        search_service_endpoint = bot.search_service_endpoint if is_ursa else tenant.search_service_endpoint
        index_name = bot.index_name if is_ursa else tenant.index_name
        if search_service_endpoint is None or index_name is None:
            raise Exception("検索サービスのエンドポイントまたはインデックス名が設定されていません")

        document = self.document_repo.find_with_ancestor_folders_by_id(bot_id, document_id)
        root_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        full_path = document.get_full_path()
        new_document_name = document.name.value
        memo = document.memo.value if document.memo else ""
        new_blob_path = self._create_blob_path(bot_id=bot_id, document=document, root_folder=root_folder)

        def _update_ursa_index_document_names():
            document_chunks = self.cognitive_search_service.find_ursa_index_documents_by_bot_id_and_document_id(
                endpoint=search_service_endpoint,
                index_name=index_name,
                bot_id=bot_id,
                document_id=document_id,
            )
            for _document_chunk in document_chunks:
                # update file_name
                _document_chunk.update_file_name(new_document_name)

                # update full_path
                _document_chunk.update_full_path(memo)

                # update updated_at
                _document_chunk.update_updated_at()

            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint, index_name=index_name, documents=document_chunks
            )

        def _update_index_document_names():
            document_chunks = self.cognitive_search_service.find_index_documents_by_bot_id_and_document_id(
                endpoint=search_service_endpoint,
                index_name=index_name,
                bot_id=bot_id,
                document_id=document_id,
            )
            for document_chunk in document_chunks:
                # update content
                document_chunk.update_full_path_in_content(full_path)

                # update blob_path
                document_chunk.update_blob_path(new_blob_path.root)

                # update file_name
                document_chunk.update_file_name(new_document_name)

                # update updated_at
                document_chunk.update_updated_at()

                # update is_vectorized
                document_chunk.update_is_vectorized_false()

            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint, index_name=index_name, documents=document_chunks
            )

        try:
            if is_ursa:
                _update_ursa_index_document_names()
                # ursaではembeddingsを作らなくなったため、ここでステータスをcompletedに更新
                document.update_status_to_completed()
                self.document_repo.update(document)
            else:
                _update_index_document_names()
                self.queue_storage_service.send_message_to_create_embeddings_queue(
                    tenant_id=tenant_id, bot_id=bot_id, document_id=document_id
                )
            self.logger.info(f"ドキュメント名を更新しました。document_id: {document_id}")
        except Exception as e:
            document.update_status_to_failed()
            self.document_repo.update(document)
            raise e
