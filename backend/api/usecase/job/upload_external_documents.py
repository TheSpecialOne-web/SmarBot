from abc import ABC, abstractmethod
import asyncio

from injector import inject
from timeout_decorator import timeout
from timeout_decorator.timeout_decorator import TimeoutError

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.box.box import IBoxService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.cognitive_search.cognitive_search import ICognitiveSearchService
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.libs.exceptions import BadRequest
from api.libs.logging import get_logger


class IUploadExternalDocumentsUseCase(ABC):
    @abstractmethod
    def upload_external_documents(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        pass


class UploadExternalDocumentsUseCase(IUploadExternalDocumentsUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        document_repo: document_domain.IDocumentRepository,
        blob_storage_service: IBlobStorageService,
        cognitive_search_service: ICognitiveSearchService,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
        box_service: IBoxService,
    ):
        self.tenant_repo = tenant_repo
        self.document_folder_repo = document_folder_repo
        self.document_repo = document_repo
        self.blob_storage_service = blob_storage_service
        self.cognitive_search_service = cognitive_search_service
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service
        self.box_service = box_service
        self.logger = get_logger()

    @timeout(60 * 20)
    def _upload_external_documents_for_sharepoint(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder: document_folder_domain.DocumentFolder,
        document_ids: list[document_domain.Id],
        external_data_connection: external_data_connection_domain.ExternalDataConnection,
    ) -> list[document_domain.Id]:
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
        )
        credentials = decrypted_credentials.to_sharepoint_credentials()

        uploaded_document_ids = []

        try:
            for document_id in document_ids:
                document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)
                if document.external_id is None:
                    self.logger.warning(f"Document does not have external_id. id:{document_id}")
                    continue

                # download document
                sharepoint_external_id = external_data_connection_domain.SharepointExternalId.from_external_id(
                    document.external_id
                )
                data = asyncio.run(self.msgraph_service.download_document(credentials, sharepoint_external_id))

                # blob storage
                self.blob_storage_service.upload_external_blob(
                    container_name=tenant.container_name,
                    bot_id=bot_id,
                    document_folder_id=document_folder.id,
                    document_id=document_id,
                    blob_name=document.blob_name_v2,
                    data=data,
                )

                # ai search
                if document.file_extension.is_indexing_supported():
                    self.queue_storage_service.send_messages_to_documents_process_queue(
                        tenant.id, bot_id, [document_id]
                    )
                if document.file_extension.is_convertible_to_pdf():
                    self.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue(
                        tenant.id, bot_id, [document_id]
                    )

                uploaded_document_ids.append(document_id)

            return uploaded_document_ids
        except TimeoutError:
            return uploaded_document_ids

    @timeout(60 * 20)
    def _upload_external_documents_for_box(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder: document_folder_domain.DocumentFolder,
        document_ids: list[document_domain.Id],
        external_data_connection: external_data_connection_domain.ExternalDataConnection,
    ) -> list[document_domain.Id]:
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
        )
        credentials = decrypted_credentials.to_box_credentials()

        uploaded_document_ids = []

        try:
            for document_id in document_ids:
                document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)
                if document.external_id is None:
                    self.logger.warning(f"Document does not have external_id. id:{document_id}")
                    continue

                # download document
                box_external_id = external_data_connection_domain.BoxExternalId.from_external_id(document.external_id)
                data = self.box_service.download_document(credentials, box_external_id)

                # blob storage
                self.blob_storage_service.upload_external_blob(
                    container_name=tenant.container_name,
                    bot_id=bot_id,
                    document_folder_id=document_folder.id,
                    document_id=document_id,
                    blob_name=document.blob_name_v2,
                    data=data,
                )

                # ai search
                if document.file_extension.is_indexing_supported():
                    self.queue_storage_service.send_messages_to_documents_process_queue(
                        tenant.id, bot_id, [document_id]
                    )
                if document.file_extension.is_convertible_to_pdf():
                    self.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue(
                        tenant.id, bot_id, [document_id]
                    )

                uploaded_document_ids.append(document_id)

            return uploaded_document_ids
        except TimeoutError:
            return uploaded_document_ids

    def upload_external_documents(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        document_folder = self.document_folder_repo.find_by_id_and_bot_id(document_folder_id, bot_id)
        if document_folder.external_id is None or document_folder.external_type is None:
            raise BadRequest(f"DocumentFolder does not have external_id or external_type. id:{document_folder_id}")

        tenant = self.tenant_repo.find_by_id(tenant_id)
        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, document_folder.external_type
        )

        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                uploaded_document_ids = self._upload_external_documents_for_sharepoint(
                    tenant, bot_id, document_folder, document_ids, external_data_connection
                )
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                uploaded_document_ids = self._upload_external_documents_for_box(
                    tenant, bot_id, document_folder, document_ids, external_data_connection
                )
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        self.logger.info(f"uploaded documents: {uploaded_document_ids}")

        # resend message to self queue
        document_ids_to_resend = []
        for document_id in document_ids:
            if document_id not in uploaded_document_ids:
                document_ids_to_resend.append(document_id)
        if not document_ids_to_resend:
            self.logger.info(f"All documents have been uploaded for document_folder: {document_folder_id}")
            return

        self.queue_storage_service.send_message_to_upload_external_documents_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder_id,
            document_ids=document_ids_to_resend,
        )
