from abc import ABC, abstractmethod
from typing import Union

from ...models.attachment import (
    AttachmentForCreate,
    BlobName as AttachmentBlobName,
    SignedUrl as AttachmentSignedUrl,
)
from ...models.attachment.content import BlobContent
from ...models.bot import Id as BotId
from ...models.bot.icon_url import IconUrl
from ...models.bot_template import (
    IconUrl as BotTemplateIconUrl,
    Id as BotTemplateId,
)
from ...models.chat_completion_export import (
    BlobPath as ChatCompletionExportBlobPath,
    SignedUrl as ChatCompletionExportSignedUrl,
)
from ...models.common_document_template import (
    BlobName as CommonDocumentTemplateBlobName,
    CommonDocumentTemplateForCreate,
    Url as CommonDocumentTemplateUrl,
)
from ...models.conversation_export import (
    BlobPath as ConversationExportBlobPath,
    SignedUrl as ConversationExportSignedUrl,
)
from ...models.document import (
    BlobName,
    DisplayableBlobName,
    DocumentForCreate,
    Id as DocumentId,
    SignedUrl,
)
from ...models.document_folder import Id as DocumentFolderId
from ...models.document_folder.document_folder import DocumentFolderContext
from ...models.storage import ContainerName
from ...models.tenant import Alias, LogoUrl
from ...models.user import Id as UserId


class IBlobStorageService(ABC):
    @abstractmethod
    def upload_blob(
        self,
        container_name: ContainerName,
        document_folder_context: DocumentFolderContext,
        document_for_create: DocumentForCreate,
    ):
        pass

    @abstractmethod
    def upload_blob_v2(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_context: DocumentFolderContext,
        document_for_create: DocumentForCreate,
    ):
        pass

    @abstractmethod
    def upload_external_blob(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_id: DocumentFolderId,
        document_id: DocumentId,
        blob_name: BlobName,
        data: bytes,
    ):
        pass

    @abstractmethod
    def upload_attachment(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        user_id: UserId,
        attachment_for_create: AttachmentForCreate,
    ):
        pass

    @abstractmethod
    def create_blob_sas_url(
        self,
        container_name: ContainerName,
        document_folder_context: DocumentFolderContext,
        blob_name: Union[BlobName, DisplayableBlobName],
    ) -> SignedUrl:
        pass

    @abstractmethod
    def delete_blob_export(
        self,
        container_name: ContainerName,
        blob_path: Union[ConversationExportBlobPath, ChatCompletionExportBlobPath],
    ) -> None:
        pass

    @abstractmethod
    def create_blob_chat_completion_sas_url(
        self,
        container_name: ContainerName,
        blob_path: ChatCompletionExportBlobPath,
    ) -> ChatCompletionExportSignedUrl:
        pass

    @abstractmethod
    def create_blob_conversation_sas_url(
        self,
        container_name: ContainerName,
        blob_path: ConversationExportBlobPath,
    ) -> ConversationExportSignedUrl:
        pass

    @abstractmethod
    def create_blob_sas_url_v2(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_context: DocumentFolderContext,
        blob_name: DisplayableBlobName,
    ) -> SignedUrl:
        pass

    @abstractmethod
    def create_attachment_blob_sas_url(
        self, container_name: ContainerName, bot_id: BotId, blob_name: AttachmentBlobName
    ) -> AttachmentSignedUrl:
        pass

    @abstractmethod
    def create_external_blob_sas_url(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_id: DocumentId,
        document_folder_context: DocumentFolderContext,
        blob_name: DisplayableBlobName,
    ) -> SignedUrl:
        pass

    @abstractmethod
    def update_document_blob_name(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_context: DocumentFolderContext,
        old_blob_name: BlobName,
        new_blob_name: BlobName,
    ) -> None:
        pass

    @abstractmethod
    def delete_document_blob(
        self,
        container_name: ContainerName,
        document_folder_context: DocumentFolderContext,
        blob_name: BlobName,
    ):
        pass

    @abstractmethod
    def delete_document_blob_v2(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_context: DocumentFolderContext,
        blob_name: BlobName,
    ):
        pass

    @abstractmethod
    def delete_document_blobs_by_document_folder_id(
        self, container_name: ContainerName, bot_id: BotId, document_folder_id: DocumentFolderId
    ) -> None:
        pass

    @abstractmethod
    def delete_attachment_blob(self, container_name: ContainerName, bot_id: BotId, blob_name: AttachmentBlobName):
        pass

    @abstractmethod
    def create_blob_container(self, container_name: ContainerName):
        pass

    @abstractmethod
    def get_attachment_blob_content(
        self, container_name: ContainerName, bot_id: BotId, blob_name: AttachmentBlobName
    ) -> BlobContent:
        pass

    @abstractmethod
    def upload_users_import_csv(self, file: bytes, filename: str):
        pass

    @abstractmethod
    def delete_blob_container(self, container_name: ContainerName) -> None:
        pass

    @abstractmethod
    def upload_image_to_common_container(self, file_name: str, file_content: bytes) -> LogoUrl:
        pass

    @abstractmethod
    def delete_blobs_by_bot_id(self, container_name: ContainerName, bot_id: BotId):
        pass

    @abstractmethod
    def upload_bot_icon(self, file_path: str, file_content: bytes) -> IconUrl:
        pass

    @abstractmethod
    def delete_bot_icon(self, alias: Alias, icon_url: IconUrl) -> None:
        pass

    @abstractmethod
    def upload_bot_template_icon(self, file_path: str, file_content: bytes) -> BotTemplateIconUrl:
        pass

    @abstractmethod
    def delete_bot_template_icon(self, bot_template_id: BotTemplateId, icon_url: BotTemplateIconUrl) -> None:
        pass

    @abstractmethod
    def copy_icon_from_template(self, alias: Alias, template_icon_url: BotTemplateIconUrl) -> IconUrl:
        pass

    @abstractmethod
    def upload_common_document_template_to_common_container(
        self, bot_template_id: BotTemplateId, common_document_template: CommonDocumentTemplateForCreate
    ) -> None:
        pass

    @abstractmethod
    def delete_common_document_template_from_common_container(
        self, bot_template_id: BotTemplateId, blob_name: CommonDocumentTemplateBlobName
    ) -> None:
        pass

    @abstractmethod
    def copy_blob_from_common_container_to_bot_container(
        self,
        bot_id: BotId,
        bot_template_id: BotTemplateId,
        blob_name: CommonDocumentTemplateBlobName,
        container_name: ContainerName,
    ) -> None:
        pass

    @abstractmethod
    def create_common_document_template_url(
        self, bot_template_id: BotTemplateId, blob_name: CommonDocumentTemplateBlobName
    ) -> CommonDocumentTemplateUrl:
        pass

    @abstractmethod
    def get_csv_from_blob_storage(
        self,
        container_name: ContainerName,
        blob_name: BlobName,
    ) -> bytes:
        pass

    @abstractmethod
    def upload_conversation_export_csv(
        self, container_name: ContainerName, blob_path: ConversationExportBlobPath, csv: bytes
    ):
        pass

    @abstractmethod
    def upload_chat_completion_export_csv(
        self, container_name: ContainerName, blob_path: ChatCompletionExportBlobPath, csv: bytes
    ):
        pass

    @abstractmethod
    def upload_guideline(
        self,
        container_name: ContainerName,
        blob_path: str,
        file_content: bytes,
    ) -> None:
        pass

    @abstractmethod
    def delete_guideline(
        self,
        container_name: ContainerName,
        blob_path: str,
    ) -> None:
        pass

    @abstractmethod
    def create_guideline_sas_url(
        self,
        container_name: ContainerName,
        blob_path: str,
    ) -> str:
        pass

    @abstractmethod
    def get_document_blob(
        self,
        container_name: ContainerName,
        document_folder_context: DocumentFolderContext,
        blob_name: BlobName,
    ) -> bytes:
        pass

    @abstractmethod
    def get_document_blob_v2(
        self,
        container_name: ContainerName,
        document_folder_context: DocumentFolderContext,
        blob_name: BlobName,
        bot_id: BotId,
    ) -> bytes:
        pass

    @abstractmethod
    def get_external_document_blob(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_id: DocumentFolderId,
        document_id: DocumentId,
        blob_name: BlobName,
    ) -> bytes:
        pass

    @abstractmethod
    def convert_and_upload_pdf_file(
        self,
        container_name: ContainerName,
        blob_name: BlobName,
        document_folder_context: DocumentFolderContext,
        file_data: bytes,
    ) -> None:
        pass

    @abstractmethod
    def convert_and_upload_pdf_file_v2(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        blob_name: BlobName,
        document_folder_context: DocumentFolderContext,
        file_data: bytes,
    ) -> None:
        pass

    @abstractmethod
    def convert_and_upload_external_pdf_file(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        document_folder_id: DocumentFolderId,
        document_id: DocumentId,
        blob_name: BlobName,
        file_data: bytes,
    ) -> None:
        pass

    @abstractmethod
    def update_document_folder_path(
        self,
        container_name: ContainerName,
        bot_id: BotId,
        old_document_folder_context: DocumentFolderContext,
        new_document_folder_context: DocumentFolderContext,
        blob_name: BlobName,
    ) -> None:
        pass
