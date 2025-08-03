from datetime import datetime
from unittest.mock import MagicMock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.usecase.job.calculate_storage_usage import CalculateStorageUsageUseCase


class TestJobCalculateStorageUsageUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = MagicMock(spec=bot_domain.IBotRepository)
        self.document_repo_mock = MagicMock(spec=document_domain.IDocumentRepository)
        self.cognitive_search_service_mock = MagicMock(spec=ICognitiveSearchService)

        self.use_case = CalculateStorageUsageUseCase(
            self.tenant_repo_mock,
            self.bot_repo_mock,
            self.document_repo_mock,
            self.cognitive_search_service_mock,
        )

        # Mock data
        self.tenant_id = tenant_domain.Id(value=1)
        self.bot_id = bot_domain.Id(value=1)
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
        self.bot = bot_domain.Bot(
            id=self.bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=None,
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
            name=document_folder_domain.Name(root="test_root_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        self.document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=self.root_document_folder.id,
        )

        self.tenant_repo_mock.find_by_id.return_value = self.tenant
        self.bot_repo_mock.find_by_id_and_tenant_id.return_value = self.bot
        self.document_repo_mock.find_by_id_and_bot_id.return_value = self.document
        self.document_repo_mock.update.return_value = None
        self.cognitive_search_service_mock.find_index_documents_by_bot_id_and_document_id.return_value = []

    def test_calculate_storage_usage_sucess(self, setup):
        # Call the method
        self.use_case.calculate_storage_usage(self.tenant_id, self.bot_id, self.document_id)
        # Assertions

        self.tenant_repo_mock.find_by_id.assert_called_once_with(self.tenant_id)
        self.bot_repo_mock.find_by_id_and_tenant_id.assert_called_once_with(self.bot_id, self.tenant_id)
        self.cognitive_search_service_mock.find_index_documents_by_bot_id_and_document_id.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            bot_id=self.bot_id,
            document_id=self.document.id,
        )
        self.document_repo_mock.update.assert_called_once_with(self.document)
