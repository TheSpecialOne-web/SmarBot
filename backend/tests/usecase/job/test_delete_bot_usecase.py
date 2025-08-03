from datetime import datetime
from unittest.mock import MagicMock, Mock
import uuid

import pytest

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.attachment.repository import IAttachmentRepository
from api.domain.models.chat_completion.repository import IChatCompletionRepository
from api.domain.models.conversation.repository import IConversationRepository
from api.domain.models.document_folder.repository import IDocumentFolderRepository
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.question_answer.repository import IQuestionAnswerRepository
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.term.repository import ITermV2Repository
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.infrastructures.blob_storage.blob_storage import IBlobStorageService
from api.usecase.job.delete_bot import DeleteBotUseCase


class TestJobDeleteBotUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = MagicMock(spec=bot_domain.IBotRepository)
        self.document_repo_mock = MagicMock(spec=document_domain.IDocumentRepository)
        self.api_key_repo_mock = MagicMock(spec=api_key_domain.IApiKeyRepository)
        self.attachment_repo_mock = MagicMock(spec=IAttachmentRepository)
        self.conversation_repo_mock = MagicMock(spec=IConversationRepository)
        self.document_folder_repo_mock = MagicMock(spec=IDocumentFolderRepository)
        self.question_answer_repo_mock = MagicMock(spec=IQuestionAnswerRepository)
        self.term_v2_repo_mock = MagicMock(spec=ITermV2Repository)
        self.chat_completion_repo_mock = MagicMock(spec=IChatCompletionRepository)
        self.user_repo_mock = MagicMock(spec=user_domain.IUserRepository)
        self.blob_storage_service_mock = MagicMock(spec=IBlobStorageService)
        self.cognitive_search_service_mock = MagicMock(spec=ICognitiveSearchService)

        self.use_case = DeleteBotUseCase(
            self.tenant_repo_mock,
            self.bot_repo_mock,
            self.api_key_repo_mock,
            self.document_repo_mock,
            self.attachment_repo_mock,
            self.conversation_repo_mock,
            self.document_folder_repo_mock,
            self.question_answer_repo_mock,
            self.term_v2_repo_mock,
            self.chat_completion_repo_mock,
            self.user_repo_mock,
            self.blob_storage_service_mock,
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
            approach=bot_domain.Approach.CUSTOM_GPT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.DELETING,
            icon_url=bot_domain.IconUrl(root="mock_url"),
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
            status=document_domain.Status.DELETING,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=self.root_document_folder.id,
        )
        self.document_folder_context = document_folder_domain.DocumentFolderContext(
            id=self.root_document_folder.id, is_root=self.document.document_folder_id == self.root_document_folder.id
        )

        self.search_service_endpoint = (
            self.tenant.search_service_endpoint
            if self.bot.approach != bot_domain.Approach.URSA
            else self.bot.search_service_endpoint
        )
        self.index_name = (
            self.bot.index_name if self.bot.approach == bot_domain.Approach.URSA else self.tenant.index_name
        )

        self.tenant_repo_mock.find_by_id.return_value = self.tenant
        self.bot_repo_mock.find_by_id_and_tenant_id.return_value = self.bot
        self.document_repo_mock.find_by_bot_id.return_value = [self.document]
        self.document_repo_mock.delete.return_value = None
        self.blob_storage_service_mock.delete_bot_icon.return_value = None
        self.blob_storage_service_mock.delete_blobs_by_bot_id.return_value = None
        self.blob_storage_service_mock.delete_blob_container.return_value = None

        self.cognitive_search_service_mock.delete_index.return_value = None
        self.cognitive_search_service_mock.delete_documents_from_index_by_bot_id.return_value = None
        self.bot_repo_mock.delete.return_value = self.bot
        self.api_key_repo_mock.delete_by_bot_id.return_value = self.bot

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock()
        monkeypatch.setattr("api.usecase.job.delete_bot.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def test_delete_bot_success_without_feature_flag(self, setup, mock_get_feature_flag):
        mock_get_feature_flag.return_value = False
        # Call the method
        self.use_case.delete_bot(self.tenant_id, self.bot_id)
        # Assertions

        self.tenant_repo_mock.find_by_id.assert_called_once_with(self.tenant_id)
        self.bot_repo_mock.find_by_id_and_tenant_id.assert_called_once_with(self.bot_id, self.tenant_id)
        self.document_repo_mock.find_by_bot_id.assert_called_once_with(self.bot.id)

        self.blob_storage_service_mock.delete_bot_icon.assert_called_with(self.tenant.alias, self.bot.icon_url)
        self.cognitive_search_service_mock.delete_documents_from_index_by_bot_id.assert_called_with(
            self.search_service_endpoint, self.index_name, self.bot.id
        )
        self.blob_storage_service_mock.delete_blob_container.assert_called_with(self.bot.container_name)
        self.bot_repo_mock.delete.assert_called_with(self.bot.id)
        self.api_key_repo_mock.delete_by_bot_id(self.bot.id)

    def test_delete_bot_success_with_feature_flag(self, setup, mock_get_feature_flag):
        mock_get_feature_flag.return_value = True
        # Call the method
        self.use_case.delete_bot(self.tenant_id, self.bot_id)

        # Assertions
        self.tenant_repo_mock.find_by_id.assert_called_once_with(self.tenant_id)
        self.bot_repo_mock.find_by_id_and_tenant_id.assert_called_once_with(self.bot_id, self.tenant_id)
        self.document_repo_mock.find_by_bot_id.assert_called_once_with(self.bot.id)

        self.cognitive_search_service_mock.delete_documents_from_index_by_bot_id.assert_called_with(
            self.search_service_endpoint, self.index_name, self.bot.id
        )
        self.blob_storage_service_mock.delete_bot_icon.assert_called_with(self.tenant.alias, self.bot.icon_url)
        self.blob_storage_service_mock.delete_blobs_by_bot_id.assert_called_with(
            self.tenant.container_name, self.bot.id
        )
        self.bot_repo_mock.delete.assert_called_with(self.bot.id)
        self.api_key_repo_mock.delete_by_bot_id(self.bot.id)
