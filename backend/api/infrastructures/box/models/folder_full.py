from box_sdk_gen.schemas.folder_full import (
    FolderBaseTypeField,
    FolderFull as BaseFolderFull,
)

from api.domain.models import document_folder as document_folder_domain
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.libs.exceptions import BadRequest

""" e.g.
{
    "id": "298005577421",
    "etag": "0",
    "type": "folder",
    "sequence_id": "0",
    "name": "neoAI_データ連係用フォルダ",
    "created_at": "2024-12-11T22:32:25-08:00",
    "modified_at": "2025-01-21T21:56:13-08:00",
    "description": "",
    "size": 1565548076,
    "path_collection": {"total_count": 1, "entries": [{"id": "0", "type": "folder", "name": "すべてのファイル"}]},
    "created_by": {
        "id": "38570425629",
        "type": "user",
        "name": "BOX検証環境用管理アカウント",
        "login": "box_admin@365t.kyuden.co.jp",
    },
    "modified_by": {
        "id": "38602814146",
        "type": "user",
        "name": "neoAI検証01",
        "login": "neoAI_01@365t.kyuden.co.jp",
    },
    "content_created_at": "2024-12-11T22:32:25-08:00",
    "content_modified_at": "2025-01-21T21:56:13-08:00",
    "owned_by": {
        "id": "38570425629",
        "type": "user",
        "name": "BOX検証環境用管理アカウント",
        "login": "box_admin@365t.kyuden.co.jp",
    },
    "shared_link": {
        "url": "https://365tkyuden.box.com/s/q84vmop59rtsz2zlhudqrnf8209rq3ax",
        "effective_access": "company",
        "effective_permission": "can_download",
        "is_password_enabled": False,
        "download_count": 0,
        "preview_count": 0,
        "access": "company",
        "unshared_at": "2025-02-02T21:25:04-08:00",
        "permissions": {"can_download": True, "can_preview": True, "can_edit": False},
    },
    "item_status": "active",
}
"""


class FolderFull(BaseFolderFull):
    def __init__(self, folder_full: BaseFolderFull):
        self.__dict__.update(folder_full.__dict__)

    def to_external_id(self) -> external_data_connection_domain.ExternalId:
        return external_data_connection_domain.ExternalId(root=f"id:{self.id}")

    def to_domain_to_sync(self) -> document_folder_domain.ExternalDocumentFolderToSync:
        if self.name is None:
            raise ValueError("Invalid folder_full")
        if self.type != FolderBaseTypeField.FOLDER:
            raise BadRequest("指定したアイテムはフォルダではありません。")
        return document_folder_domain.ExternalDocumentFolderToSync(
            external_id=self.to_external_id(),
            name=document_folder_domain.Name(root=self.name),
        )

    def to_document_folder_domain(self) -> external_document_folder_domain.ExternalDocumentFolder:
        if self.name is None or self.modified_at is None:
            raise ValueError("Invalid folder_full")
        if self.type != FolderBaseTypeField.FOLDER:
            raise ValueError("指定したアイテムはフォルダではありません。")
        return external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root=self.name),
            external_id=self.to_external_id(),
            external_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=self.modified_at),
        )
