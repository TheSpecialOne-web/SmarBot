from pydantic import BaseModel, Field, StrictBool

from api.libs.exceptions import NotFound

from ..tenant.external_data_connection.external_data_connection_type import ExternalDataConnectionType
from ..tenant.external_data_connection.external_id import ExternalId
from ..tenant.external_data_connection.external_sync_metadata import ExternalSyncMetadata
from ..tenant.external_data_connection.external_updated_at import ExternalUpdatedAt
from ..tenant.external_data_connection.last_synced_at import LastSyncedAt
from ..tenant.external_data_connection.sync_schedule import SyncSchedule
from .created_at import CreatedAt
from .document_processing_stats import DocumentProcessingStats
from .id import Id, create_id
from .name import Name
from .order import Order


class DocumentFolderProps(BaseModel):
    name: Name | None


class DocumentFolderForCreate(DocumentFolderProps):
    id: Id = Field(default_factory=create_id)
    name: Name


class ExternalDocumentFolderForCreate(DocumentFolderForCreate):
    external_id: ExternalId
    external_type: ExternalDataConnectionType
    external_updated_at: ExternalUpdatedAt
    sync_schedule: SyncSchedule | None = None
    external_sync_metadata: ExternalSyncMetadata
    last_synced_at: LastSyncedAt


class DocumentFolderForUpdate(BaseModel):
    name: Name


class DocumentFolder(DocumentFolderProps):
    id: Id
    created_at: CreatedAt
    external_id: ExternalId | None = None
    external_type: ExternalDataConnectionType | None = None
    external_updated_at: ExternalUpdatedAt | None = None
    sync_schedule: SyncSchedule | None = None
    last_synced_at: LastSyncedAt | None = None

    def update(self, document_folder_for_update: DocumentFolderForUpdate):
        self.name = document_folder_for_update.name


class RootDocumentFolderForCreate(DocumentFolderProps):
    id: Id = Field(default_factory=create_id)
    name: Name | None = Field(default=None)


# フォルダの順序を持つ DocumentFolder
# order の値が小さいほど上位のフォルダ(0-indexed)
class DocumentFolderWithOrder(DocumentFolder):
    order: Order


class DocumentFolderWithAncestors(DocumentFolder):
    ancestor_folders: list[DocumentFolderWithOrder]

    def without_root_folder(self) -> "DocumentFolderWithAncestors":
        ancestor_folders = [folder for folder in self.ancestor_folders if folder.order.root != 0]
        return DocumentFolderWithAncestors(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            ancestor_folders=ancestor_folders,
        )

    def get_parent_folder(self) -> DocumentFolder:
        # ancestor_folders のなかで、order.root が最大のものが親フォルダ
        if len(self.ancestor_folders) == 0:
            raise NotFound("親フォルダが存在しません")
        parent_folder = max(self.ancestor_folders, key=lambda folder: folder.order.root)
        return DocumentFolder(
            id=parent_folder.id,
            name=parent_folder.name,
            created_at=parent_folder.created_at,
        )

    def get_absolute_path(self) -> str:
        """フォルダのパスを取得する
        Returns:
            str: フォルダのパス (e.g. "parent_folder/child_folder/")
        """
        ancestors_without_root = [folder for folder in self.ancestor_folders if folder.order.root != 0]
        ancestors_without_root = sorted(ancestors_without_root, key=lambda folder: folder.order.root)

        folder_names = [folder.name.root for folder in ancestors_without_root if folder.name is not None]
        if self.name is not None:
            folder_names.append(self.name.root)
        folder_path = "/".join(folder_names)
        return folder_path + "/"


class DocumentFolderWithDescendants(DocumentFolder):
    descendant_folders: list[DocumentFolder]

    def id_filter_for_search_index(self) -> str:
        ids = [str(self.id.root)]
        ids.extend([str(folder.id.root) for folder in self.descendant_folders])
        return "search.in(document_folder_id, '{}')".format(",".join(ids))


class DocumentFolderWithDocumentProcessingStats(DocumentFolder):
    document_processing_stats: DocumentProcessingStats | None = None


class DocumentFolderContext(BaseModel):
    id: Id
    is_root: StrictBool
    is_external: StrictBool = False


class ExternalDocumentFolderToSync(BaseModel):
    external_id: ExternalId
    name: Name
    is_valid: StrictBool = True

    def update_is_valid(self, is_valid: bool):
        self.is_valid = is_valid
