from box_sdk_gen.schemas.file_full import (
    FileBaseTypeField,
    FileFull as BaseFileFull,
)

from api.domain.models import document as document_domain
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.models.tenant.external_data_connection.external_updated_at import ExternalUpdatedAt


class FileFull(BaseFileFull):
    def __init__(self, folder_full: BaseFileFull):
        self.__dict__.update(folder_full.__dict__)

    def to_external_id(self) -> external_data_connection_domain.ExternalId:
        return external_data_connection_domain.ExternalId(root=f"id:{self.id}")

    def to_external_full_path(self) -> external_document_domain.ExternalFullPath:
        if self.name is None or self.path_collection is None:
            raise ValueError("無効なドキュメントです")
        path_names = [folder.name for folder in self.path_collection.entries]
        path = ""
        for name in path_names:
            if name is None:
                raise ValueError("パスが無効です。")
            path += "/" + name
        path += self.name
        return external_document_domain.ExternalFullPath(root=path)

    def to_external_document(self) -> external_document_domain.ExternalDocument:
        if self.type != FileBaseTypeField.FILE:
            raise ValueError("ドキュメントではありません")
        if self.name is None or self.modified_at is None:
            raise ValueError("無効なドキュメントです")
        return external_document_domain.ExternalDocument(
            name=document_domain.Name.from_filename(self.name),
            file_extension=document_domain.FileExtension.from_filename(self.name, False),
            external_id=self.to_external_id(),
            external_updated_at=ExternalUpdatedAt(root=self.modified_at),
            external_full_path=self.to_external_full_path(),
        )
