from abc import ABC, abstractmethod

from ..bot import Id as BotId
from ..document_folder import Id as DocumentFolderId
from ..user import Id as UserId
from .document import Document, DocumentForCreate, DocumentWithAncestorFolders, ExternalDocumentForCreate
from .feedback import DocumentFeedback
from .id import Id
from .name import Name


class IDocumentRepository(ABC):
    @abstractmethod
    def create(
        self, bot_id: BotId, parent_document_folder_id: DocumentFolderId, document: DocumentForCreate
    ) -> Document:
        pass

    @abstractmethod
    def bulk_create_external_documents(
        self,
        bot_id: BotId,
        parent_document_folder_id: DocumentFolderId,
        external_documents: list[ExternalDocumentForCreate],
    ) -> list[Document]:
        pass

    @abstractmethod
    def find_by_id_and_bot_id(self, id: Id, bot_id: BotId) -> Document:
        pass

    @abstractmethod
    def find_by_bot_id_and_parent_document_folder_id(
        self, bot_id: BotId, parent_document_folder_id: DocumentFolderId
    ) -> list[Document]:
        pass

    @abstractmethod
    def find_by_bot_id(self, bot_id: BotId) -> list[Document]:
        pass

    @abstractmethod
    def find_by_bot_id_and_parent_document_folder_id_and_name(
        self, bot_id: BotId, parent_document_folder_id: DocumentFolderId, name: Name
    ) -> Document:
        pass

    @abstractmethod
    def find_by_parent_document_folder_id(
        self, bot_id: BotId, parent_document_folder_id: DocumentFolderId
    ) -> list[Document]:
        pass

    @abstractmethod
    def update(self, document: Document) -> None:
        pass

    @abstractmethod
    def bulk_update(self, documents: list[Document]) -> None:
        pass

    @abstractmethod
    def delete(self, id: Id) -> None:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_document_folder_ids(self, document_folder_ids: list[DocumentFolderId]) -> None:
        pass

    @abstractmethod
    def hard_delete_by_bot_ids(self, bot_ids: list[BotId]) -> None:
        pass

    @abstractmethod
    def delete_by_folder_ids(self, bot_id: BotId, document_folder_ids: list[DocumentFolderId]) -> None:
        pass

    @abstractmethod
    def find_by_ids_and_bot_id(self, bot_id: BotId, document_ids: list[Id]) -> list[Document]:
        pass

    @abstractmethod
    def find_feedback_by_id_and_user_id(self, id: Id, user_id: UserId) -> DocumentFeedback:
        pass

    @abstractmethod
    def find_feedbacks_by_ids_and_user_id(self, ids: list[Id], user_id: UserId) -> list[DocumentFeedback]:
        pass

    @abstractmethod
    def create_feedback(self, feedback: DocumentFeedback) -> DocumentFeedback:
        pass

    @abstractmethod
    def update_feedback(self, feedback: DocumentFeedback) -> None:
        pass

    @abstractmethod
    def find_all_descendants_documents_by_ancestor_folder_id(
        self, bot_id: BotId, ancestor_folder_id: DocumentFolderId
    ) -> list[Document]:
        pass

    @abstractmethod
    def find_documents_with_ancestor_folders_by_ids(
        self, bot_id: BotId, ids: list[Id]
    ) -> list[DocumentWithAncestorFolders]:
        pass

    @abstractmethod
    def find_with_ancestor_folders_by_id(
        self,
        bot_id: BotId,
        id: Id,
    ) -> DocumentWithAncestorFolders:
        pass
