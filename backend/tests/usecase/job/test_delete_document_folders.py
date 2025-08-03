from datetime import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.services.blob_storage.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.usecase.job.delete_document_folders import DeleteDocumentFoldersUseCase

BATCH_DELETE_SIZE = 10


class TestJobDeleteDocumentFoldersUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = Mock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = Mock(spec=bot_domain.IBotRepository)
        self.blob_storage_service_mock = Mock(spec=IBlobStorageService)
        self.queue_storage_service_mock = Mock(spec=IQueueStorageService)
        self.cognitive_search_service_mock = Mock(spec=ICognitiveSearchService)

        self.use_case = DeleteDocumentFoldersUseCase(
            self.tenant_repo_mock,
            self.bot_repo_mock,
            self.blob_storage_service_mock,
            self.queue_storage_service_mock,
            self.cognitive_search_service_mock,
        )

        # Mock data
        self.tenant_id = tenant_domain.Id(value=1)
        self.bot_id = bot_domain.Id(value=1)
        self.document_folder_ids1 = [
            document_folder_domain.Id(root=uuid.uuid4()) for _ in range(BATCH_DELETE_SIZE + 1)
        ]
        self.document_folder_ids2 = [
            document_folder_domain.Id(root=uuid.uuid4()) for _ in range(BATCH_DELETE_SIZE - 1)
        ]

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
        self.bot = bot_domain.Bot(
            id=self.bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )
        self.root_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=None,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        self.parent_document_folder_name = document_folder_domain.Name(root="test_parent_document_folder_name")
        self.parent_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=self.parent_document_folder_name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        self.document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            id=self.parent_document_folder.id,
            name=self.parent_document_folder_name,
            created_at=self.parent_document_folder.created_at,
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    **self.root_document_folder.model_dump(), order=document_folder_domain.Order(root=0)
                )
            ],
        )

    def test_delete_document_folders_with_resend(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_folder_ids = self.document_folder_ids1

        _, folder_ids_to_resend = (
            document_folder_ids[:BATCH_DELETE_SIZE],
            document_folder_ids[BATCH_DELETE_SIZE:],
        )

        # Mock
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.bot_repo.find_by_id_and_tenant_id = Mock(return_value=self.bot)

        self.use_case.cognitive_search_service.delete_documents_from_index_by_document_folder_id = Mock()
        self.use_case.blob_storage_service.delete_document_blobs_by_document_folder_id = Mock()

        self.use_case.queue_storage_service.send_message_to_delete_document_folders_queue = Mock()

        # Call the method
        self.use_case.delete_document_folders(tenant_id, bot_id, document_folder_ids)

        # Assertions
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)

        self.use_case.cognitive_search_service.delete_documents_from_index_by_document_folder_id.assert_called()
        self.use_case.blob_storage_service.delete_document_blobs_by_document_folder_id.assert_called()

        self.use_case.queue_storage_service.send_message_to_delete_document_folders_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_folder_ids=folder_ids_to_resend
        )

    def test_delete_document_folders_without_resend(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_folder_ids = self.document_folder_ids2

        # Mock
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.bot_repo.find_by_id_and_tenant_id = Mock(return_value=self.bot)

        self.use_case.cognitive_search_service.delete_documents_from_index_by_document_folder_id = Mock()
        self.use_case.blob_storage_service.delete_document_blobs_by_document_folder_id = Mock()

        self.use_case.queue_storage_service.send_message_to_delete_document_folders_queue = Mock()

        # Call the method
        self.use_case.delete_document_folders(tenant_id, bot_id, document_folder_ids)

        # Assertions
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)

        self.use_case.cognitive_search_service.delete_documents_from_index_by_document_folder_id.assert_called()
        self.use_case.blob_storage_service.delete_document_blobs_by_document_folder_id.assert_called()

        self.use_case.queue_storage_service.send_message_to_delete_document_folders_queue.assert_not_called()
