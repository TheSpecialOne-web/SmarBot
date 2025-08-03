from abc import ABC, abstractmethod

from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.document_folder import (
    document_folder as document_folder_domain,
    external_data_connection as external_document_folder_domain,
)
from api.domain.models.tenant import external_data_connection as external_data_connection_domain


class IBoxService(ABC):
    @abstractmethod
    def is_authorized_client(self, credentials: external_data_connection_domain.BoxDecryptedCredentials) -> bool:
        pass

    @abstractmethod
    def get_external_document_folder_to_sync(
        self, credentials: external_data_connection_domain.BoxDecryptedCredentials, shared_url: str
    ) -> document_folder_domain.ExternalDocumentFolderToSync:
        pass

    @abstractmethod
    def get_document_folder_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_document_folder_domain.ExternalDocumentFolder:
        pass

    @abstractmethod
    def get_document_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_document_domain.ExternalDocument:
        pass

    @abstractmethod
    def get_descendant_documents_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> list[external_document_domain.ExternalDocument]:
        pass

    @abstractmethod
    def download_document(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> bytes:
        pass

    @abstractmethod
    def get_external_document_folder_url(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        pass
