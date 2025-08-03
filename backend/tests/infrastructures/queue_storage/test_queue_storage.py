import base64
from contextlib import suppress
import json
import time

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueMessage
import pytest

from api.domain.models import (
    bot as bot_domain,
    conversation_export as conversation_export_domain,
    document as document_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
)
from api.infrastructures.queue_storage.queue_storage import (
    CONVERT_AND_UPLOAD_PDF_DOCUMENT_QUEUE_NAME,
    CREATE_CONVERSATION_EXPORT_QUEUE_NAME,
    DELETE_ATTACHMENTS_QUEUE_NAME,
    DELETE_BOT_QUEUE_NAME,
    DELETE_MULTIPLE_DOCUMENTS_QUEUE_NAME,
    DOCUMENT_PROCESS_QUEUE_NAME,
    SYNC_DOCUMENT_NAME_QUEUE_NAME,
    UPLOAD_QUESTION_ANSWERS_QUEUE_NAME,
    USERS_IMPORT_QUEUE_NAME,
    QueueStorageService,
)


class TestQueueStorageService:
    @pytest.fixture
    def dummy_blob_storage(self):
        self.tenant_id = tenant_domain.Id(value=100)
        self.bot_id = bot_domain.Id(value=100)
        self.document_id = document_domain.Id(value=100)
        self.document_ids = [document_domain.Id(value=100)]
        self.conversation_export_id = conversation_export_domain.Id(root="fc3a0038-dfa2-4a3d-a98a-155330364cdd")
        self.question_answer_ids = [question_answer_domain.Id(root="fc3b0038-dfa2-4a3d-a98a-155330364cdf")]
        self.filename = "test.pdf"
        self.conversation_export_id = conversation_export_domain.Id(root="fc3a0038-dfa2-4a3d-a98a-155330364cdd")

    @pytest.fixture
    def setup(self, dummy_blob_storage):
        self.credential = DefaultAzureCredential()
        self.queue_storage_service = QueueStorageService(self.credential)
        self.interval = 1
        self.max_messages = 32
        self.retries = 5

    def _create_queue(self, queue_name: str):
        with suppress(ResourceExistsError):
            self.queue_storage_service.queue_service_client.get_queue_client(queue_name).create_queue()

    def _check_found_message(self, queue_name: str, encoded_message: str) -> bool:
        messages_to_delete: list[QueueMessage] = []
        found_message = False
        queue_client = self.queue_storage_service.queue_service_client.get_queue_client(queue_name)
        retry = 0
        while True:
            # Retrieve messages from the queue
            received_messages = list(queue_client.receive_messages(max_messages=self.max_messages))
            if not received_messages:
                if retry > self.retries:
                    break
                retry = retry + 1
                time.sleep(self.interval)
                continue

            # Check if the expected message is in the received messages
            for msg in received_messages:
                if msg.content == encoded_message:
                    found_message = True
                    messages_to_delete.append(msg)
            if found_message:
                break

            time.sleep(self.interval)

        # Delete all collected messages
        if messages_to_delete:
            for message in messages_to_delete:
                queue_client.delete_message(message.id, message.pop_receipt)
        return found_message

    def test_send_messages_to_documents_process_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_id = self.document_id
        document_ids = self.document_ids
        self._create_queue(DOCUMENT_PROCESS_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_messages_to_documents_process_queue(tenant_id, bot_id, document_ids)

        # Assertions
        expected_message = {"tenant_id": tenant_id.value, "bot_id": bot_id.value, "document_id": document_id.value}
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(DOCUMENT_PROCESS_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_sync_document_name_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_id = self.document_id
        self._create_queue(SYNC_DOCUMENT_NAME_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_sync_document_name_queue(tenant_id, bot_id, document_id)

        # Assertions
        expected_message = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_id": document_id.value,
        }
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(SYNC_DOCUMENT_NAME_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_create_conversation_export_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        conversation_export_id = self.conversation_export_id
        self._create_queue(CREATE_CONVERSATION_EXPORT_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_create_conversation_export_queue(tenant_id, conversation_export_id)

        # Assertions
        expected_message = {"tenant_id": tenant_id.value, "conversation_export_id": str(conversation_export_id.root)}
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(CREATE_CONVERSATION_EXPORT_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_messages_to_convert_and_upload_pdf_documents_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_ids = self.document_ids
        self._create_queue(CONVERT_AND_UPLOAD_PDF_DOCUMENT_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue(
            tenant_id, bot_id, document_ids
        )

        # Assertions
        expected_message = {
            "tenant_id": self.tenant_id.value,
            "bot_id": self.bot_id.value,
            "document_id": self.document_id.value,
        }
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(CONVERT_AND_UPLOAD_PDF_DOCUMENT_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_users_import_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        filename = self.filename
        self._create_queue(USERS_IMPORT_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_users_import_queue(tenant_id, filename)

        # Assertions
        expected_message = {"tenant_id": tenant_id.value, "filename": filename}
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(USERS_IMPORT_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_delete_multiple_documents_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_ids = self.document_ids
        self._create_queue(DELETE_MULTIPLE_DOCUMENTS_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_delete_multiple_documents_queue(tenant_id, bot_id, document_ids)

        # Assertions
        expected_message = {
            "tenant_id": tenant_id.value,
            "bot_id": bot_id.value,
            "document_ids": [document_id.value for document_id in document_ids],
        }
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(DELETE_MULTIPLE_DOCUMENTS_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_delete_bot_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        self._create_queue(DELETE_BOT_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_delete_bot_queue(tenant_id, bot_id)

        # Assertions
        expected_message = {"tenant_id": tenant_id.value, "bot_id": bot_id.value}
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(DELETE_BOT_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_delete_attachment_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        self._create_queue(DELETE_ATTACHMENTS_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_delete_attachment_queue(tenant_id)

        # Assertions
        expected_message = {
            "tenant_id": tenant_id.value,
        }
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(DELETE_ATTACHMENTS_QUEUE_NAME, encoded_message)

        assert found_message is True

    def test_send_message_to_upload_question_answers_queue(self, setup):
        # Given
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        question_answer_ids = self.question_answer_ids
        self._create_queue(UPLOAD_QUESTION_ANSWERS_QUEUE_NAME)

        # Call the method
        self.queue_storage_service.send_message_to_upload_question_answers_queue(
            tenant_id, bot_id, question_answer_ids
        )

        # Assertions
        expected_message = {
            "bot_id": bot_id.value,
            "tenant_id": tenant_id.value,
            "question_answer_ids": [str(question_answer_id.root) for question_answer_id in question_answer_ids],
        }
        json_message = json.dumps(expected_message)
        encoded_message = base64.b64encode(json_message.encode("utf-8")).decode("utf-8")
        found_message = self._check_found_message(UPLOAD_QUESTION_ANSWERS_QUEUE_NAME, encoded_message)

        assert found_message is True
