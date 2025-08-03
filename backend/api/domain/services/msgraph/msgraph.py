from abc import ABC, abstractmethod

from api.domain.models import tenant as tenant_domain
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.document_folder import (
    ExternalDocumentFolderToSync,
    external_data_connection as external_document_folder_domain,
)
from api.domain.models.tenant import (
    external_data_connection as external_data_connection_domain,
    tenant_alert as tenant_alert_domain,
)
from api.domain.models.user.email import Email
from api.domain.models.user.name import Name


class IMsgraphService(ABC):
    @abstractmethod
    def send_alert_email_to_tenant_users(
        self,
        tenant_name: tenant_domain.Name,
        recipients: list[Email],
        bcc_recipients: list[Email],
        alerts: list[tenant_alert_domain.Alert],
    ) -> None:
        pass

    @abstractmethod
    def send_create_user_email(self, name: Name, email: Email) -> None:
        pass

    @abstractmethod
    async def is_authorized_client(
        self, credentials: external_data_connection_domain.SharepointDecryptedCredentials
    ) -> bool:
        pass

    @abstractmethod
    async def get_external_document_folder_to_sync(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        shared_url: str,
    ) -> ExternalDocumentFolderToSync:
        pass

    @abstractmethod
    async def get_document_folder_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_document_folder_domain.ExternalDocumentFolder:
        pass

    @abstractmethod
    async def get_document_folder_delta_token_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalSyncMetadata:
        pass

    @abstractmethod
    async def get_descendant_documents_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> list[external_document_domain.ExternalDocument]:
        pass

    @abstractmethod
    async def get_document_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_document_domain.ExternalDocument:
        pass

    @abstractmethod
    async def download_document(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> bytes:
        pass

    @abstractmethod
    async def get_external_document_folder_url(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        pass

    @abstractmethod
    async def get_external_document_url(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        pass
