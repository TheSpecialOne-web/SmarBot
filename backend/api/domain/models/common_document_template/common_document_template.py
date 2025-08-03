from pydantic import BaseModel, Field, computed_field

from .basename import Basename
from .blob_name import BlobName
from .created_at import CreatedAt
from .file_extension import FileExtension
from .id import Id, create_id
from .memo import Memo


class CommonDocumentTemplateProps(BaseModel):
    basename: Basename
    memo: Memo | None
    file_extension: FileExtension

    @computed_field  # type: ignore[misc]
    @property
    def blob_name(self) -> BlobName:
        return BlobName(root=f"{self.basename.root}.{self.file_extension.value}")


class CommonDocumentTemplate(CommonDocumentTemplateProps):
    id: Id
    created_at: CreatedAt

    def update(self, common_document_template: "CommonDocumentTemplateForUpdate") -> None:
        self.memo = common_document_template.memo


class CommonDocumentTemplateForCreate(CommonDocumentTemplateProps):
    id: Id = Field(default_factory=create_id)
    data: bytes


class CommonDocumentTemplateForUpdate(BaseModel):
    memo: Memo | None
