from abc import ABC, abstractmethod
import asyncio

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.box.box import IBoxService
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.libs.exceptions import BadRequest
from api.libs.logging import get_logger

WINDOWS_PATH_PREFIX = "Z:"


class IStartExternalDataConnectionUseCase(ABC):
    @abstractmethod
    def start_external_data_connection(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> None:
        pass


class StartExternalDataConnectionUseCase(IStartExternalDataConnectionUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        document_repo: document_domain.IDocumentRepository,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
        box_service: IBoxService,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.document_folder_repo = document_folder_repo
        self.document_repo = document_repo
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service
        self.box_service = box_service

    def _get_external_documents_for_sharepoint(
        self,
        document_folder_external_id: external_data_connection_domain.ExternalId,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
    ) -> list[external_document_domain.ExternalDocument]:
        sharepoint_external_id = external_data_connection_domain.SharepointExternalId.from_external_id(
            document_folder_external_id
        )

        return asyncio.run(self.msgraph_service.get_descendant_documents_by_id(credentials, sharepoint_external_id))

    def _get_external_documents_for_box(
        self,
        document_folder_external_id: external_data_connection_domain.ExternalId,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
    ) -> list[external_document_domain.ExternalDocument]:
        box_external_id = external_data_connection_domain.BoxExternalId.from_external_id(document_folder_external_id)

        return self.box_service.get_descendant_documents_by_id(credentials, box_external_id)

    def start_external_data_connection(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> None:
        document_folder = self.document_folder_repo.find_by_id_and_bot_id(document_folder_id, bot_id)
        if document_folder.external_id is None or document_folder.external_type is None:
            raise BadRequest(f"DocumentFolder does not have external_id or external_type. id:{document_folder_id}")

        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, document_folder.external_type
        )
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
        )
        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                sharepoint_credentials = decrypted_credentials.to_sharepoint_credentials()
                external_documents = self._get_external_documents_for_sharepoint(
                    document_folder.external_id, sharepoint_credentials
                )

            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                box_credentials = decrypted_credentials.to_box_credentials()
                external_documents = self._get_external_documents_for_box(document_folder.external_id, box_credentials)
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        def _create_memo_for_ursa(
            external_document: external_document_domain.ExternalDocument,
        ) -> document_domain.Memo:
            full_path = external_document.external_full_path.root.replace("/", "\\")
            win_path = WINDOWS_PATH_PREFIX + full_path
            return document_domain.Memo(value=win_path)

        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        is_ursa = bot.search_method in [
            bot_domain.SearchMethod.URSA,
            bot_domain.SearchMethod.URSA_SEMANTIC,
        ]

        external_documents_for_create = [
            document_domain.ExternalDocumentForCreate(
                name=external_document.name,
                memo=_create_memo_for_ursa(external_document) if is_ursa else None,
                file_extension=external_document.file_extension,
                storage_usage=None,
                creator_id=None,
                external_id=external_document.external_id,
                external_updated_at=external_document.external_updated_at,
            )
            for external_document in external_documents
        ]

        # DB
        created_documents = self.document_repo.bulk_create_external_documents(
            bot_id,
            document_folder_id,
            external_documents_for_create,
        )

        # Blob storage & Ai search
        self.queue_storage_service.send_message_to_upload_external_documents_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder_id,
            document_ids=[created_document.id for created_document in created_documents],
        )
