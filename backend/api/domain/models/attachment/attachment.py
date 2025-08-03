from pydantic import BaseModel, Field

from .content import Content
from .created_at import CreatedAt
from .file_extension import FileExtension
from .id import Id, create_id
from .is_blob_deleted import IsBlobDeleted
from .name import BlobName, Name


class AttachmentProps(BaseModel):
    id: Id
    name: Name
    file_extension: FileExtension

    @property
    def blob_name(self) -> BlobName:
        return BlobName(root=f"{self.id.root!s}.{self.file_extension.value}")


class Attachment(AttachmentProps):
    id: Id
    created_at: CreatedAt
    is_blob_deleted: IsBlobDeleted


class AttachmentForCreate(AttachmentProps):
    id: Id = Field(default_factory=create_id)
    data: bytes


class AttachmentForConversation(BaseModel):
    name: Name
    content: Content
