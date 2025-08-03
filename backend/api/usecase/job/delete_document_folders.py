from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.libs.logging import get_logger


class IDeleteDocumentFoldersUseCase(ABC):
    @abstractmethod
    def delete_document_folders(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_ids: list[document_folder_domain.Id]
    ) -> None:
        pass


class DeleteDocumentFoldersUseCase(IDeleteDocumentFoldersUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        blob_storage_service: IBlobStorageService,
        queue_storage_service: IQueueStorageService,
        cognitive_search_service: ICognitiveSearchService,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.blob_storage_service = blob_storage_service
        self.queue_storage_service = queue_storage_service
        self.cognitive_search_service = cognitive_search_service

    def _delete_documents_from_cognitive_search(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        document_folder_id: document_folder_domain.Id,
    ) -> None:
        search_service_endpoint = (
            tenant.search_service_endpoint
            if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
            else bot.search_service_endpoint
        )
        if search_service_endpoint is None:
            raise Exception("Search service endpoint is None")

        index_name = (
            tenant.index_name
            if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
            else bot.index_name
        )
        if index_name is None:
            raise Exception("index_name is not set")

        self.cognitive_search_service.delete_documents_from_index_by_document_folder_id(
            endpoint=search_service_endpoint,
            index_name=index_name,
            document_folder_id=document_folder_id,
        )

    def _delete_documents_from_blob_storage(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        document_folder_id: document_folder_domain.Id,
    ) -> None:
        self.blob_storage_service.delete_document_blobs_by_document_folder_id(
            container_name=tenant.container_name,
            bot_id=bot.id,
            document_folder_id=document_folder_id,
        )

    def _delete_documents_by_folder_id(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        document_folder_id: document_folder_domain.Id,
    ) -> None:
        self._delete_documents_from_cognitive_search(tenant, bot, document_folder_id)

        self._delete_documents_from_blob_storage(tenant, bot, document_folder_id)

    def delete_document_folders(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_ids: list[document_folder_domain.Id]
    ) -> None:
        BATCH_DELETE_SIZE = 10
        folder_ids_to_delete, folder_ids_to_resend = (
            document_folder_ids[:BATCH_DELETE_SIZE],
            document_folder_ids[BATCH_DELETE_SIZE:],
        )

        # delete documents
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        for document_folder_id in folder_ids_to_delete:
            self._delete_documents_by_folder_id(tenant, bot, document_folder_id)

        # resend message to delete document folders queue
        if not folder_ids_to_resend:
            return

        self.queue_storage_service.send_message_to_delete_document_folders_queue(
            tenant_id=tenant_id, bot_id=bot_id, document_folder_ids=folder_ids_to_resend
        )
