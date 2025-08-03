from msgraph.generated.models.drive_item import DriveItem as BaseDriveItem

from api.domain.models import (
    document as document_domain,
    document_folder as document_folder_domain,
)
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.models.tenant.external_data_connection.external_updated_at import ExternalUpdatedAt


class DriveItem(BaseDriveItem):
    def __init__(self, drive_item: BaseDriveItem):
        self.__dict__.update(drive_item.__dict__)

    def to_external_id(self) -> external_data_connection_domain.ExternalId:
        if self.id is None or self.parent_reference is None or self.parent_reference.drive_id is None:
            raise ValueError("Invalid drive_item")
        return external_data_connection_domain.ExternalId(
            root=f"drive_id:{self.parent_reference.drive_id},drive_item_id:{self.id}"
        )

    def to_domain_to_sync(self) -> document_folder_domain.ExternalDocumentFolderToSync:
        if self.name is None or self.last_modified_date_time is None:
            raise ValueError("Invalid drive_item")
        return document_folder_domain.ExternalDocumentFolderToSync(
            external_id=self.to_external_id(),
            name=document_folder_domain.Name(root=self.name),
        )

    def to_document_folder_domain(self) -> external_document_folder_domain.ExternalDocumentFolder:
        if self.name is None or self.last_modified_date_time is None:
            raise ValueError("Invalid drive_item")
        if self.folder is None:
            raise ValueError("This drive_item is not a folder")
        return external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root=self.name),
            external_id=self.to_external_id(),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=self.last_modified_date_time),
        )

    def to_document_domain(self) -> external_document_domain.ExternalDocument:
        if self.name is None or self.last_modified_date_time is None:
            raise ValueError("Invalid drive_item")
        if self.file is None or self.parent_reference is None or self.parent_reference.path is None:
            raise ValueError("This drive_item is not a document")
        name = document_domain.Name.from_filename(self.name)
        return external_document_domain.ExternalDocument(
            name=name,
            file_extension=document_domain.FileExtension.from_filename(self.name, False),
            external_id=self.to_external_id(),
            external_updated_at=ExternalUpdatedAt(root=self.last_modified_date_time),
            external_full_path=external_document_domain.ExternalFullPath(
                root=self.parent_reference.path.split("root:")[1] + "/" + name.value
            ),
        )
