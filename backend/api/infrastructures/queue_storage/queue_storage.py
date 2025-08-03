import base64
from datetime import datetime
import json
from logging import getLogger
import os
from typing import TypedDict

from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueServiceClient

from api.domain.models import (
    bot as bot_domain,
    chat_completion_export as chat_completion_export_domain,
    conversation_export as conversation_export_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
)
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.app_env import app_env

# TODO: JOB_NAMES_TO_QUEUE_NAMESから取得
ALERT_CAPACITY_QUEUE_NAME = "alert-capacity-queue"
CALCULATE_STORAGE_USAGE_QUEUE_NAME = "calculate-storage-usage-queue"
CONVERT_AND_UPLOAD_PDF_DOCUMENT_QUEUE_NAME = "convert-and-upload-pdf-document-queue"
CREATE_CHAT_COMPLETION_EXPORT_QUEUE_NAME = "create-chat-completion-export-queue"
CREATE_CONVERSATION_EXPORT_QUEUE_NAME = "create-conversation-export-queue"
CREATE_EMBEDDINGS_QUEUE_NAME = "create-embeddings-queue"
DELETE_ATTACHMENTS_QUEUE_NAME = "delete-attachments-queue"
DELETE_BOT_QUEUE_NAME = "delete-bot-queue"
DELETE_DOCUMENT_FOLDERS_QUEUE_NAME = "delete-document-folders-queue"
DELETE_MULTIPLE_DOCUMENTS_QUEUE_NAME = "delete-multiple-documents-queue"
DELETE_TENANT_QUEUE_NAME = "delete-tenant-queue"
DOCUMENT_PROCESS_QUEUE_NAME = "documents-process-queue"
SYNC_DOCUMENT_NAME_QUEUE_NAME = "sync-document-name-queue"
UPLOAD_QUESTION_ANSWERS_QUEUE_NAME = "upload-question-answers-queue"
USERS_IMPORT_QUEUE_NAME = "users-import-queue"
START_EXTERNAL_DATA_CONNECTION_QUEUE_NAME = "start-external-data-connection-queue"
SYNC_DOCUMENT_PATH_QUEUE_NAME = "sync-document-path-queue"
SYNC_DOCUMENT_LOCATION_QUEUE_NAME = "sync-document-location-queue"
UPLOAD_EXTERNAL_DOCUMENTS_QUEUE_NAME = "upload-external-documents-queue"


class AlertCapacityQueueMessage(TypedDict):
    tenant_id: int
    datetime: str


class CalculateStorageUsageQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class SyncDocumentNameQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class ConvertAndUploadPdfDocumentQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class CreateChatCompletionExportQueueMessage(TypedDict):
    tenant_id: int
    chat_completion_export_id: str


class CreateConversationExportQueueMessage(TypedDict):
    tenant_id: int
    conversation_export_id: str


class DeleteAttachmentsQueueMessage(TypedDict):
    tenant_id: int


class DeleteDocumentFoldersQueue(TypedDict):
    tenant_id: int
    bot_id: int
    document_folder_ids: list[str]


class CreateEmbeddingsQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class DeleteBotQueue(TypedDict):
    tenant_id: int
    bot_id: int


class DeleteMultipleDocumentsQueue(TypedDict):
    tenant_id: int
    bot_id: int
    document_ids: list[int]


class DeleteTenantQueueMessage(TypedDict):
    tenant_id: int


class DocumentProcessQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class UploadQuestionAnswersQueue(TypedDict):
    bot_id: int
    tenant_id: int
    question_answer_ids: list[str]


class UsersImportQueueMessage(TypedDict):
    tenant_id: int
    filename: str


class StartExternalDataConnectionQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_folder_id: str


class SyncDocumentPathQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_folder_id: str
    document_ids: list[int]


class SyncDocumentLocationQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_id: int


class UploadExternalDocumentsQueueMessage(TypedDict):
    tenant_id: int
    bot_id: int
    document_folder_id: str
    document_ids: list[int]


QueueMessage = (
    AlertCapacityQueueMessage
    | CalculateStorageUsageQueueMessage
    | ConvertAndUploadPdfDocumentQueueMessage
    | CreateEmbeddingsQueueMessage
    | DeleteAttachmentsQueueMessage
    | DeleteBotQueue
    | DeleteDocumentFoldersQueue
    | DeleteMultipleDocumentsQueue
    | DocumentProcessQueueMessage
    | SyncDocumentNameQueueMessage
    | UploadQuestionAnswersQueue
    | UsersImportQueueMessage
    | StartExternalDataConnectionQueueMessage
    | SyncDocumentPathQueueMessage
    | SyncDocumentLocationQueueMessage
    | UploadExternalDocumentsQueueMessage
)


AZURE_BATCH_STORAGE_ACCOUNT = os.environ.get("AZURE_BATCH_STORAGE_ACCOUNT") or ""
AZURE_BATCH_STORAGE_QUEUE_CONNECTION_STRING = (
    os.environ.get("AZURE_BATCH_STORAGE_QUEUE_CONNECTION_STRING")
    or "DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;QueueEndpoint=http://azurite:10001/stbatchlocal;"
)


class QueueStorageService(IQueueStorageService):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.logger = getLogger(__name__)
        self.queue_service_client = (
            QueueServiceClient(
                account_url=f"https://{AZURE_BATCH_STORAGE_ACCOUNT}.queue.core.windows.net",
                credential=azure_credential,
            )
            if not app_env.is_localhost()
            else QueueServiceClient.from_connection_string(AZURE_BATCH_STORAGE_QUEUE_CONNECTION_STRING)
        )

    def _encode_queue_message(self, message: QueueMessage) -> str:
        json_message = json.dumps(message)
        return base64.b64encode(json_message.encode("utf-8")).decode("utf-8")

    def send_message_to_alert_capacity_queue(self, tenant_id: tenant_domain.Id, datetime: datetime):
        message: AlertCapacityQueueMessage = {
            "tenant_id": tenant_id.value,
            "datetime": datetime.isoformat(),
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(ALERT_CAPACITY_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_sync_document_name_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: SyncDocumentNameQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(SYNC_DOCUMENT_NAME_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_document_process_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: DocumentProcessQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DOCUMENT_PROCESS_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_messages_to_documents_process_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        for document_id in document_ids:
            self.send_message_to_document_process_queue(tenant_id, bot_id, document_id)

    def send_message_to_convert_and_upload_pdf_document_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: ConvertAndUploadPdfDocumentQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(CONVERT_AND_UPLOAD_PDF_DOCUMENT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_create_conversation_export_queue(
        self,
        tenant_id: tenant_domain.Id,
        conversation_export_id: conversation_export_domain.Id,
    ):
        message: CreateConversationExportQueueMessage = {
            "tenant_id": tenant_id.value,
            "conversation_export_id": str(conversation_export_id.root),
        }

        json_message = json.dumps(message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        queue_client = self.queue_service_client.get_queue_client(CREATE_CONVERSATION_EXPORT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_create_chat_completion_export_queue(
        self,
        tenant_id: tenant_domain.Id,
        chat_completion_export_id: chat_completion_export_domain.Id,
    ):
        message: CreateChatCompletionExportQueueMessage = {
            "tenant_id": tenant_id.value,
            "chat_completion_export_id": str(chat_completion_export_id.root),
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(CREATE_CHAT_COMPLETION_EXPORT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_messages_to_convert_and_upload_pdf_documents_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        for document_id in document_ids:
            self.send_message_to_convert_and_upload_pdf_document_queue(tenant_id, bot_id, document_id)

    def send_message_to_users_import_queue(self, tenant_id: tenant_domain.Id, filename: str):
        message: UsersImportQueueMessage = {
            "tenant_id": tenant_id.value,
            "filename": filename,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(USERS_IMPORT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_delete_multiple_documents_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        message: DeleteMultipleDocumentsQueue = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_ids": [document_id.value for document_id in document_ids],
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DELETE_MULTIPLE_DOCUMENTS_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_delete_bot_queue(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id):
        message: DeleteBotQueue = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DELETE_BOT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_delete_attachment_queue(self, tenant_id: tenant_domain.Id):
        message: DeleteAttachmentsQueueMessage = {
            "tenant_id": tenant_id.value,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DELETE_ATTACHMENTS_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_delete_tenant_queue(self, tenant_id: tenant_domain.Id):
        message: DeleteTenantQueueMessage = {
            "tenant_id": tenant_id.value,
        }
        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DELETE_TENANT_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_delete_document_folders_queue(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_ids: list[document_folder_domain.Id]
    ):
        message: DeleteDocumentFoldersQueue = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_folder_ids": [str(document_folder_id.root) for document_folder_id in document_folder_ids],
        }
        encode_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(DELETE_DOCUMENT_FOLDERS_QUEUE_NAME)
        queue_client.send_message(encode_message)

    def send_message_to_upload_question_answers_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        question_answer_ids: list[question_answer_domain.Id],
    ):
        message: UploadQuestionAnswersQueue = {
            "bot_id": bot_id.value,
            "tenant_id": tenant_id.value,
            "question_answer_ids": [str(question_answer_id.root) for question_answer_id in question_answer_ids],
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(UPLOAD_QUESTION_ANSWERS_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_calculate_storage_usage_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: CalculateStorageUsageQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(CALCULATE_STORAGE_USAGE_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_create_embeddings_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: CreateEmbeddingsQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(CREATE_EMBEDDINGS_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_start_external_data_connection_queue(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ):
        message: StartExternalDataConnectionQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_folder_id": str(document_folder_id.root),
        }
        encode_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(START_EXTERNAL_DATA_CONNECTION_QUEUE_NAME)
        queue_client.send_message(encode_message)

    def send_message_to_sync_document_path_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        message: SyncDocumentPathQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_folder_id": str(document_folder_id.root),
            "document_ids": [document_id.value for document_id in document_ids],
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(SYNC_DOCUMENT_PATH_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_sync_document_location_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ):
        message: SyncDocumentLocationQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(SYNC_DOCUMENT_LOCATION_QUEUE_NAME)
        queue_client.send_message(encoded_message)

    def send_message_to_upload_external_documents_queue(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        message: UploadExternalDocumentsQueueMessage = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_folder_id": str(document_folder_id.root),
            "document_ids": [external_document_id.value for external_document_id in document_ids],
        }

        encoded_message = self._encode_queue_message(message)
        queue_client = self.queue_service_client.get_queue_client(UPLOAD_EXTERNAL_DOCUMENTS_QUEUE_NAME)
        queue_client.send_message(encoded_message)
