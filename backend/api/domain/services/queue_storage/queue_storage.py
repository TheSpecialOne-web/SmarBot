from abc import ABC, abstractmethod
from datetime import datetime

from ...models.bot import Id as BotId
from ...models.chat_completion_export import Id as ChatCompletionExportId
from ...models.conversation_export import Id as ConversationExportId
from ...models.document import Id as DocumentId
from ...models.document_folder import Id as DocumentFolderId
from ...models.question_answer import Id as QuestionAnswerId
from ...models.tenant import Id as TenantId


class IQueueStorageService(ABC):
    @abstractmethod
    def send_message_to_alert_capacity_queue(self, tenant_id: TenantId, datetime: datetime):
        pass

    @abstractmethod
    def send_message_to_sync_document_name_queue(self, tenant_id: TenantId, bot_id: BotId, document_id: DocumentId):
        pass

    @abstractmethod
    def send_messages_to_convert_and_upload_pdf_documents_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_ids: list[DocumentId]
    ):
        pass

    @abstractmethod
    def send_message_to_create_chat_completion_export_queue(
        self,
        tenant_id: TenantId,
        chat_completion_export_id: ChatCompletionExportId,
    ):
        pass

    @abstractmethod
    def send_message_to_create_conversation_export_queue(
        self,
        tenant_id: TenantId,
        conversation_export_id: ConversationExportId,
    ):
        pass

    @abstractmethod
    def send_message_to_delete_attachment_queue(self, tenant_id: TenantId):
        pass

    @abstractmethod
    def send_message_to_delete_bot_queue(self, tenant_id: TenantId, bot_id: BotId):
        pass

    @abstractmethod
    def send_message_to_delete_document_folders_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_folder_ids: list[DocumentFolderId]
    ):
        pass

    @abstractmethod
    def send_message_to_delete_multiple_documents_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_ids: list[DocumentId]
    ):
        pass

    @abstractmethod
    def send_message_to_delete_tenant_queue(self, tenant_id: TenantId):
        pass

    @abstractmethod
    def send_messages_to_documents_process_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_ids: list[DocumentId]
    ):
        pass

    @abstractmethod
    def send_message_to_upload_external_documents_queue(
        self,
        tenant_id: TenantId,
        bot_id: BotId,
        document_folder_id: DocumentFolderId,
        document_ids: list[DocumentId],
    ):
        pass

    @abstractmethod
    def send_message_to_upload_question_answers_queue(
        self, tenant_id: TenantId, bot_id: BotId, question_answer_ids: list[QuestionAnswerId]
    ):
        pass

    @abstractmethod
    def send_message_to_users_import_queue(self, tenant_id: TenantId, filename: str):
        pass

    @abstractmethod
    def send_message_to_calculate_storage_usage_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_id: DocumentId
    ):
        pass

    @abstractmethod
    def send_message_to_create_embeddings_queue(self, tenant_id: TenantId, bot_id: BotId, document_id: DocumentId):
        pass

    @abstractmethod
    def send_message_to_start_external_data_connection_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_folder_id: DocumentFolderId
    ):
        pass

    @abstractmethod
    def send_message_to_sync_document_path_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_folder_id: DocumentFolderId, document_ids: list[DocumentId]
    ):
        pass

    @abstractmethod
    def send_message_to_sync_document_location_queue(
        self, tenant_id: TenantId, bot_id: BotId, document_id: DocumentId
    ):
        pass
