from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.libs.exceptions import NotFound
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger


class IDeleteMultipleDocumentsUseCase(ABC):
    @abstractmethod
    def delete_multiple_documents(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_ids: list[document_domain.Id]
    ) -> None:
        pass


class DeleteMultipleDocumentsUseCase(IDeleteMultipleDocumentsUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        blob_storage_service: IBlobStorageService,
        cognitive_search_service: ICognitiveSearchService,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.document_repo = document_repo
        self.document_folder_repo = document_folder_repo
        self.blob_storage_service = blob_storage_service
        self.cognitive_search_service = cognitive_search_service

    def delete_multiple_documents(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_ids: list[document_domain.Id]
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id=bot_id)

        FLAG_KEY = "blob-container-renewal"
        feature_flag = get_feature_flag(FLAG_KEY, tenant_id, tenant.name, default=True)

        for document_id in document_ids:
            document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)

            self._delete_from_cognitive_search(tenant, bot, document)

            self._delete_from_blob_storage(tenant, bot, root_document_folder, document, feature_flag)

            self._delete_from_postgres(document_id)

            self.logger.info(f"Deleted document with ID: {document_id}")

    def _delete_from_cognitive_search(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        document: document_domain.Document,
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

        self.cognitive_search_service.delete_documents_from_index_by_document_id(
            endpoint=search_service_endpoint,
            index_name=index_name,
            document_id=document.id,
        )

    def _delete_from_blob_storage(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        root_folder: document_folder_domain.DocumentFolder,
        document: document_domain.Document,
        feature_flag: bool,
    ) -> None:
        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=document.document_folder_id, is_root=document.document_folder_id == root_folder.id
        )

        if feature_flag:
            self._delete_blob_with_feature_flag(tenant, bot, document_folder_context, document)
        else:
            self._delete_blob_without_feature_flag(bot, document_folder_context, document)

    def _delete_blob_with_feature_flag(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        folder_context: document_folder_domain.DocumentFolderContext,
        document: document_domain.Document,
    ) -> None:
        self.blob_storage_service.delete_document_blob_v2(
            container_name=tenant.container_name,
            bot_id=bot.id,
            document_folder_context=folder_context,
            blob_name=document.blob_name_v2,
        )
        if document.file_extension.is_convertible_to_pdf():
            try:
                self.blob_storage_service.delete_document_blob_v2(
                    container_name=tenant.container_name,
                    bot_id=bot.id,
                    document_folder_context=folder_context,
                    blob_name=document.pdf_blob_name_v2,
                )
            except NotFound:
                self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

    def _delete_blob_without_feature_flag(
        self,
        bot: bot_domain.Bot,
        folder_context: document_folder_domain.DocumentFolderContext,
        document: document_domain.Document,
    ) -> None:
        if not bot.container_name:
            raise Exception("Container name is not set")
        self.blob_storage_service.delete_document_blob(
            container_name=bot.container_name,
            document_folder_context=folder_context,
            blob_name=document.blob_name,
        )
        if document.file_extension.is_convertible_to_pdf():
            try:
                self.blob_storage_service.delete_document_blob(
                    container_name=bot.container_name,
                    document_folder_context=folder_context,
                    blob_name=document.pdf_blob_name,
                )
            except NotFound:
                self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

    def _delete_from_postgres(self, document_id: document_domain.Id) -> None:
        self.document_repo.delete(document_id)
