from pydantic import BaseModel, computed_field

from ..common_document_template import CommonDocumentTemplate
from ..document_folder import (
    DocumentFolderWithOrder,
    Id as DocumentFolderId,
)
from ..tenant.external_data_connection.external_id import ExternalId
from ..tenant.external_data_connection.external_updated_at import ExternalUpdatedAt
from ..user import Id as UserId
from .created_at import CreatedAt
from .file_extension import FileExtension
from .id import Id
from .memo import Memo
from .name import BlobName, Name
from .status import Status
from .storage_usage import StorageUsage


class DocumentProps(BaseModel):
    name: Name
    memo: Memo | None
    file_extension: FileExtension
    status: Status
    storage_usage: StorageUsage | None
    creator_id: UserId | None

    @computed_field  # type: ignore[misc]
    @property
    def blob_name(self) -> BlobName:
        return self.name.to_blob_name(self.file_extension)

    @computed_field  # type: ignore[misc]
    @property
    def pdf_blob_name(self) -> BlobName:
        return self.name.to_pdf_blob_name()

    @computed_field  # type: ignore[misc]
    @property
    def blob_name_v2(self) -> BlobName:
        return self.name.to_blob_name_v2(self.file_extension)

    @computed_field  # type: ignore[misc]
    @property
    def pdf_blob_name_v2(self) -> BlobName:
        return self.name.to_pdf_blob_name_v2()


class Document(DocumentProps):
    id: Id
    document_folder_id: DocumentFolderId
    created_at: CreatedAt
    external_id: ExternalId | None = None
    external_updated_at: ExternalUpdatedAt | None = None

    def update(self, document: "DocumentForUpdate") -> None:
        if document.basename is not None:
            self.name = document.basename
        self.memo = document.memo

    def update_status_to_pending(self) -> None:
        self.status = Status.PENDING

    def update_status_to_completed(self) -> None:
        self.status = Status.COMPLETED

    def update_status_to_failed(self) -> None:
        self.status = Status.FAILED

    def update_status_to_deleting(self) -> None:
        self.status = Status.DELETING

    def update_storage_usage(self, storage_usage: StorageUsage) -> None:
        self.storage_usage = storage_usage

    def update_document_folder_id(self, document_folder_id: DocumentFolderId) -> None:
        self.document_folder_id = document_folder_id

    def update_memo(self, memo: Memo) -> None:
        self.memo = memo


class DocumentForCreate(DocumentProps):
    data: bytes
    status: Status = Status.PENDING
    storage_usage: StorageUsage | None = None

    @classmethod
    def from_template(
        cls,
        document_template: CommonDocumentTemplate,
        creator_id: UserId | None,
    ) -> "DocumentForCreate":
        return DocumentForCreate(
            name=Name(value=document_template.basename.root),
            memo=Memo(value=document_template.memo.root) if document_template.memo else None,
            file_extension=FileExtension(document_template.file_extension.value),
            status=Status.PENDING,
            data=b"data",
            creator_id=creator_id,
        )


class ExternalDocumentForCreate(DocumentProps):
    status: Status = Status.PENDING
    storage_usage: StorageUsage | None = None
    external_id: ExternalId
    external_updated_at: ExternalUpdatedAt


class DocumentForUpdate(BaseModel):
    basename: Name | None
    memo: Memo | None

    def update_memo(self, memo: Memo) -> None:
        self.memo = memo


class DocumentWithAncestorFolders(Document):
    ancestor_folders: list[DocumentFolderWithOrder]

    def get_full_path(self) -> str:
        # path_length（order）で昇順ソート（浅い順）してからフォルダ名を取得
        sorted_folders = sorted(self.ancestor_folders, key=lambda x: x.order.root)
        folder_names = [folder.name.root for folder in sorted_folders if folder.name is not None]
        return f"{'/'.join(folder_names)}/{self.name.value}"
