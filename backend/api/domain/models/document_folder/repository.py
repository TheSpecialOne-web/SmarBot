from abc import ABC, abstractmethod

from ..bot.id import Id as BotId
from ..document_folder.external_data_connection import ExternalDocumentFolder
from .document_folder import (
    DocumentFolder,
    DocumentFolderForCreate,
    DocumentFolderWithAncestors,
    DocumentFolderWithDescendants,
    ExternalDocumentFolderForCreate,
    Id,
    Name,
    RootDocumentFolderForCreate,
)


class IDocumentFolderRepository(ABC):
    @abstractmethod
    def find_root_document_folder_by_bot_id(self, bot_id: BotId) -> DocumentFolder:
        pass

    @abstractmethod
    def find_by_id_and_bot_id(self, id: Id, bot_id: BotId) -> DocumentFolder:
        pass

    @abstractmethod
    def find_by_bot_ids(self, bot_ids: list[BotId], include_deleted: bool = False) -> list[DocumentFolder]:
        pass

    @abstractmethod
    def find_by_parent_document_folder_id(self, bot_id: BotId, parent_document_folder_id: Id) -> list[DocumentFolder]:
        pass

    @abstractmethod
    def find_descendants_by_id(self, bot_id: BotId, id: Id) -> list[DocumentFolder]:
        pass

    @abstractmethod
    def find_by_parent_document_folder_id_and_name(
        self, parent_document_folder_id: Id, name: Name
    ) -> list[DocumentFolder]:
        pass

    @abstractmethod
    def find_with_ancestors_by_id_and_bot_id(self, id: Id, bot_id: BotId) -> DocumentFolderWithAncestors:
        pass

    @abstractmethod
    def find_with_descendants_by_id_and_bot_id(self, id: Id, bot_id: BotId) -> DocumentFolderWithDescendants:
        pass

    @abstractmethod
    def find_external_document_folder_by_id_and_bot_id(self, id: Id, bot_id: BotId) -> ExternalDocumentFolder:
        pass

    @abstractmethod
    def create(
        self, bot_id: BotId, parent_document_folder_id: Id, document_folder: DocumentFolderForCreate
    ) -> DocumentFolder:
        pass

    @abstractmethod
    def create_external_document_folder(
        self, bot_id: BotId, parent_document_folder_id: Id, external_document_folder: ExternalDocumentFolderForCreate
    ) -> DocumentFolder:
        pass

    @abstractmethod
    def update(self, bot_id: BotId, document_folder: DocumentFolder) -> DocumentFolder:
        pass

    @abstractmethod
    def delete_by_ids(self, bot_id: BotId, document_folder_ids: list[Id]) -> None:
        pass

    @abstractmethod
    def create_root_document_folder(
        self, bot_id: BotId, root_document_folder_for_create: RootDocumentFolderForCreate
    ) -> DocumentFolder:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_bot_ids(self, bot_ids: list[BotId]) -> None:
        pass

    @abstractmethod
    def move_document_folder(self, bot_id: BotId, document_folder_id: Id, new_parent_document_folder_id: Id) -> None:
        pass
