from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger


class IConvertAndUploadPdfDocumentUseCase(ABC):
    @abstractmethod
    def convert_and_upload_pdf_document(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> None:
        pass


class ConvertAndUploadPdfDocumentUseCase(IConvertAndUploadPdfDocumentUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        blob_storage_service: IBlobStorageService,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.document_repo = document_repo
        self.document_folder_repo = document_folder_repo
        self.blob_storage_service = blob_storage_service

    def convert_and_upload_pdf_document(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> None:
        document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)

        if not document.file_extension.is_convertible_to_pdf():
            self.logger.warning("Exception ignored during PDF conversion")
            return

        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id(bot_id)

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)

        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=document.document_folder_id,
            is_root=document.document_folder_id == root_document_folder.id,
            is_external=document.external_id is not None,
        )

        # ファイルから文字抽出 ----------------------------------------
        FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag(FLAG_KEY, tenant_id, tenant.name, default=True)

        container_name = tenant.container_name if flag else bot.container_name
        if not container_name:
            raise Exception("container_name must not be None")

        if flag:
            if document_folder_context.is_external:
                file_data = self.blob_storage_service.get_external_document_blob(
                    container_name=container_name,
                    bot_id=bot.id,
                    document_folder_id=document_folder_context.id,
                    document_id=document.id,
                    blob_name=document.blob_name_v2,
                )
                self.blob_storage_service.convert_and_upload_external_pdf_file(
                    container_name=container_name,
                    bot_id=bot.id,
                    document_folder_id=document_folder_context.id,
                    document_id=document.id,
                    blob_name=document.blob_name_v2,
                    file_data=file_data,
                )
            else:
                file_data = self.blob_storage_service.get_document_blob_v2(
                    container_name=container_name,
                    bot_id=bot.id,
                    document_folder_context=document_folder_context,
                    blob_name=document.blob_name_v2,
                )
                self.blob_storage_service.convert_and_upload_pdf_file_v2(
                    container_name=container_name,
                    bot_id=bot.id,
                    blob_name=document.blob_name_v2,
                    document_folder_context=document_folder_context,
                    file_data=file_data,
                )
        else:
            file_data = self.blob_storage_service.get_document_blob(
                container_name=container_name,
                document_folder_context=document_folder_context,
                blob_name=document.blob_name,
            )

            self.blob_storage_service.convert_and_upload_pdf_file(
                container_name=container_name,
                blob_name=document.blob_name,
                document_folder_context=document_folder_context,
                file_data=file_data,
            )

        self.logger.info("finished convert document to pdf file")
