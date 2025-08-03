from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.blob_storage.blob_storage import IBlobStorageService
from api.domain.services.box.box import IBoxService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.msgraph.msgraph import IMsgraphService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.usecase.job.upload_external_documents import UploadExternalDocumentsUseCase


class TestJobUploadExternalDocumentsUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = Mock(spec=tenant_domain.ITenantRepository)
        self.document_folder_repo_mock = Mock(spec=document_folder_domain.IDocumentFolderRepository)
        self.document_repo_mock = Mock(spec=document_domain.IDocumentRepository)
        self.blob_storage_service_mock = Mock(spec=IBlobStorageService)
        self.cognitive_search_service_mock = Mock(spec=ICognitiveSearchService)
        self.queue_storage_service_mock = Mock(spec=IQueueStorageService)
        self.msgraph_service_mock = Mock(spec=IMsgraphService)
        self.box_service_mock = Mock(spec=IBoxService)

        self.use_case = UploadExternalDocumentsUseCase(
            self.tenant_repo_mock,
            self.document_folder_repo_mock,
            self.document_repo_mock,
            self.blob_storage_service_mock,
            self.cognitive_search_service_mock,
            self.queue_storage_service_mock,
            self.msgraph_service_mock,
            self.box_service_mock,
        )

        # Mock data
        self.tenant_id = tenant_domain.Id(value=1)
        self.bot_id = bot_domain.Id(value=1)
        self.document_folder_id = document_folder_domain.Id(root=uuid4())
        self.document_id = document_domain.Id(value=1)

        self.tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        # Sharepoint
        self.document_for_sharepoint = document_domain.Document(
            id=self.document_id,
            name=document_domain.Name(value="name"),
            memo=None,
            file_extension=document_domain.FileExtension.XLSX,
            status=document_domain.Status.PENDING,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=None,
            creator_id=None,
            document_folder_id=self.document_folder_id,
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:test_drive_id,drive_item_id:test_drive_item_id"
            ),
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        self.document_folder_for_sharepoint = document_folder_domain.DocumentFolder(
            id=self.document_folder_id,
            name=document_folder_domain.Name(root="test"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:test_drive_id,drive_item_id:test_drive_item_id"
            ),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
            sync_schedule=external_data_connection_domain.SyncSchedule(root="* * * * *"),
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now()),
        )
        decrypted_credentials_for_sharepoint = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            raw={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "tenant_id": "test_tenant_id",
            },
        )
        self.credentials_for_sharepoint = decrypted_credentials_for_sharepoint.to_sharepoint_credentials()
        self.external_data_connection_for_sharepoint = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid4()),
            tenant_id=self.tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            encrypted_credentials=decrypted_credentials_for_sharepoint.encrypt(),
        )
        self.descendant_documents_for_sharepoint = [
            external_document_domain.ExternalDocument(
                name=document_domain.Name(value="test_external_name"),
                file_extension=document_domain.FileExtension.PDF,
                external_id=external_data_connection_domain.ExternalId(
                    root="drive_id:test_drive_id,drive_item_id:test_drive_item_id"
                ),
                external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
                external_full_path=external_document_domain.ExternalFullPath(
                    root="/test_external_full_path/test_external_name.pdf"
                ),
            )
        ]

        # Box
        self.document_for_box = document_domain.Document(
            id=self.document_id,
            name=document_domain.Name(value="name"),
            memo=None,
            file_extension=document_domain.FileExtension.XLSX,
            status=document_domain.Status.PENDING,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=None,
            creator_id=None,
            document_folder_id=self.document_folder_id,
            external_id=external_data_connection_domain.ExternalId(root="id:test_id"),
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        self.document_folder_for_box = document_folder_domain.DocumentFolder(
            id=self.document_folder_id,
            name=document_folder_domain.Name(root="test"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            external_id=external_data_connection_domain.ExternalId(root="id:test123"),
            external_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
            sync_schedule=external_data_connection_domain.SyncSchedule(root="* * * * *"),
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now()),
        )
        decrypted_credentials_for_box = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            raw={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "enterprise_id": "test_enterprise_id",
            },
        )
        self.credentials_for_box = decrypted_credentials_for_box.to_box_credentials()
        self.external_data_connection_for_box = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid4()),
            tenant_id=self.tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            encrypted_credentials=decrypted_credentials_for_box.encrypt(),
        )
        self.descendant_documents_for_box = [
            external_document_domain.ExternalDocument(
                name=document_domain.Name(value="test_external_name"),
                file_extension=document_domain.FileExtension.PDF,
                external_id=external_data_connection_domain.ExternalId(root="id:test123"),
                external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
                external_full_path=external_document_domain.ExternalFullPath(
                    root="/test_external_full_path/test_external_name.pdf"
                ),
            )
        ]

    def test_upload_external_documents_for_sharepoint(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_folder_id = self.document_folder_id
        document_ids = [self.document_id]

        # Mock
        self.use_case.document_folder_repo.find_by_id_and_bot_id = Mock(
            return_value=self.document_folder_for_sharepoint
        )
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=self.external_data_connection_for_sharepoint
        )
        self.use_case.document_repo.find_by_id_and_bot_id = Mock(return_value=self.document_for_sharepoint)

        async def mock_download_document(*args, **kwargs):
            return b"mock_file_response"

        self.use_case.msgraph_service.download_document = Mock(side_effect=mock_download_document)
        self.use_case.blob_storage_service.upload_external_blob = Mock()
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue = Mock()
        self.use_case.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue = Mock()

        # Call the method
        self.use_case.upload_external_documents(tenant_id, bot_id, document_folder_id, document_ids)

        # Assertions
        self.use_case.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(document_folder_id, bot_id)
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id, external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT
        )
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue.assert_called_once_with(
            tenant_id,
            bot_id,
            [self.document_id],
        )
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue.assert_called_once_with(
            tenant_id,
            bot_id,
            [self.document_id],
        )

    def test_upload_external_documents_for_box(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_folder_id = self.document_folder_id
        document_ids = [self.document_id]

        # Mock
        self.use_case.document_folder_repo.find_by_id_and_bot_id = Mock(return_value=self.document_folder_for_box)
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=self.external_data_connection_for_box
        )
        self.use_case.document_repo.find_by_id_and_bot_id = Mock(return_value=self.document_for_box)
        self.use_case.box_service.download_document = Mock(return_value=b"mock_file_response")
        self.use_case.blob_storage_service.upload_external_blob = Mock()
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue = Mock()
        self.use_case.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue = Mock()

        # Call the method
        self.use_case.upload_external_documents(tenant_id, bot_id, document_folder_id, document_ids)

        # Assertions
        self.use_case.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(document_folder_id, bot_id)
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id, external_data_connection_domain.ExternalDataConnectionType.BOX
        )
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue.assert_called_once_with(
            tenant_id,
            bot_id,
            [self.document_id],
        )
        self.use_case.queue_storage_service.send_messages_to_documents_process_queue.assert_called_once_with(
            tenant_id,
            bot_id,
            [self.document_id],
        )
