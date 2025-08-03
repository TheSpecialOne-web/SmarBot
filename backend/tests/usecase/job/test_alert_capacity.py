from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion as chat_completion_domain,
    conversation as conversation_domain,
    llm as llm_domain,
    metering as metering_domain,
    search as search_domain,
    statistics as statistics_domain,
    tenant as tenant_domain,
    token as token_domain,
    user as user_domain,
    workflow_thread as workflow_thread_domain,
)
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import tenant_alert as tenant_alert_domain
from api.domain.models.user import administrator as administrator_domain
from api.infrastructures.cognitive_search.cognitive_search import ICognitiveSearchService
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.infrastructures.queue_storage.queue_storage import IQueueStorageService
from api.usecase.job.alert_capacity import AlertCapacityUseCase


class TestJobAlertCapacityUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = MagicMock(spec=bot_domain.IBotRepository)
        self.api_key_repo_mock = MagicMock(spec=api_key_domain.IApiKeyRepository)
        self.user_repo_mock = MagicMock(spec=user_domain.IUserRepository)
        self.tenant_alert_repo_mock = MagicMock(spec=tenant_alert_domain.ITenantAlertRepository)
        self.metering_repo_mock = MagicMock(spec=tenant_alert_domain.ITenantAlertRepository)
        self.statistic_repo_mock = MagicMock(spec=metering_domain.IMeteringRepository)
        self.queue_storage_service_mock = MagicMock(spec=IQueueStorageService)
        self.cognitive_search_service_mock = MagicMock(spec=ICognitiveSearchService)
        self.msgraph_service_mock = MagicMock(spec=IMsgraphService)
        self.conversation_repo_mock = MagicMock(spec=conversation_domain.IConversationRepository)
        self.chat_completion_repo_mock = MagicMock(spec=chat_completion_domain.IChatCompletionRepository)
        self.workflow_thread_repo_mock = MagicMock(spec=workflow_thread_domain.IWorkflowThreadRepository)

        self.tenant_alert_usecase = AlertCapacityUseCase(
            tenant_repo=self.tenant_repo_mock,
            bot_repo=self.bot_repo_mock,
            api_key_repo=self.api_key_repo_mock,
            user_repo=self.user_repo_mock,
            tenant_alert_repo=self.tenant_alert_repo_mock,
            metering_repo=self.metering_repo_mock,
            statistic_repo=self.statistic_repo_mock,
            queue_storage_service=self.queue_storage_service_mock,
            cognitive_search_service=self.cognitive_search_service_mock,
            msgraph_service=self.msgraph_service_mock,
            conversation_repo=self.conversation_repo_mock,
            chat_completion_repo=self.chat_completion_repo_mock,
            workflow_thread_repo=self.workflow_thread_repo_mock,
        )

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock()
        monkeypatch.setattr("api.usecase.job.alert_capacity.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def test_get_alerts(self, setup, mock_get_feature_flag):
        # Input
        tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=search_domain.Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=search_domain.IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=llm_domain.AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit(
                free_user_seat=50,
                additional_user_seat=0,
                free_token=100,
                additional_token=0,
                free_storage=100,
                additional_storage=0,
                document_intelligence_page=100,
            ),
            container_name=ContainerName(root="test"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[llm_domain.ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )
        tenant_alert = tenant_alert_domain.TenantAlert(
            tenant_id=tenant.id,
        )
        # # storage
        storage_limit = tenant_alert_domain.Limit(root=100)
        storage_usage = search_domain.StorageUsage(root=90)
        # # token
        token_limit = tenant_alert_domain.Limit(root=100)
        conversation_token_count = token_domain.TokenCount(root=100)
        chat_completion_token_count = token_domain.TokenCount(root=100)
        pdf_parser_token_count = token_domain.TokenCount(root=0)
        workflow_thread_token_count = token_domain.TokenCount(root=0)

        token_usage = statistics_domain.TokenCountBreakdown(
            conversation_token_count=conversation_token_count,
            chat_completion_token_count=chat_completion_token_count,
            pdf_parser_token_count=pdf_parser_token_count,
            workflow_thread_token_count=workflow_thread_token_count,
        )

        # Expected
        expected_alerts = [
            tenant_alert_domain.Alert(
                limit=storage_limit,
                usage=storage_usage,
                type=tenant_alert_domain.AlertType.STORAGE,
            ),
            tenant_alert_domain.Alert(
                limit=token_limit,
                usage=token_usage.total_token_count,
                type=tenant_alert_domain.AlertType.TOKEN,
            ),
        ]

        # Mock
        self.tenant_alert_usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.tenant_alert_usecase.tenant_alert_repo.find_by_tenant_id = Mock(return_value=tenant_alert)
        # # storage
        self.tenant_alert_usecase.cognitive_search_service.get_index_storage_usage = Mock(return_value=storage_usage)
        # # token

        self.tenant_alert_usecase.conversation_repo.get_conversation_token_count_by_tenant_id = Mock(
            return_value=conversation_token_count
        )
        self.tenant_alert_usecase.chat_completion_repo.get_chat_completion_token_count_by_tenant_id = Mock(
            return_value=chat_completion_token_count
        )
        self.tenant_alert_usecase.workflow_thread_repo.get_workflow_thread_token_count_by_tenant_id = Mock(
            return_value=workflow_thread_token_count
        )
        self.tenant_alert_usecase.metering_repo.get_pdf_parser_token_count_by_tenant_id = Mock(
            return_value=pdf_parser_token_count
        )

        # Call
        alerts = self.tenant_alert_usecase._get_alerts(tenant_id=tenant.id)

        # Test
        assert alerts == expected_alerts

    def test_alert_capacity(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        mock_past_datetime = datetime(2024, 1, 1, 0, 0, 0)
        mock_datetime = datetime(2024, 1, 2, 0, 0, 0)
        tenant_alert = tenant_alert_domain.TenantAlert(
            tenant_id=tenant_id,
            last_token_alerted_at=tenant_alert_domain.LastTokenAlertedAt(root=mock_past_datetime),
            last_token_alerted_threshold=tenant_alert_domain.LastTokenAlertedThreshold(root=80),
        )
        alerts = [
            tenant_alert_domain.Alert(
                limit=tenant_alert_domain.Limit(root=100),
                usage=search_domain.StorageUsage(root=90),
                type=tenant_alert_domain.AlertType.STORAGE,
            )
        ]

        # Mock
        self.tenant_alert_usecase._get_alerts = Mock(return_value=alerts)
        self.tenant_alert_usecase._send_alert_to_admins = Mock()
        self.tenant_alert_usecase.tenant_alert_repo.find_by_tenant_id = Mock(return_value=tenant_alert)

        # Call
        self.tenant_alert_usecase.alert_capacity(tenant_id=tenant_id, datetime=mock_datetime)

        # Test
        self.tenant_alert_usecase._get_alerts.assert_called_once_with(tenant_id)
        self.tenant_alert_usecase._send_alert_to_admins.assert_called_once_with(tenant_id, alerts)
        tenant_alert.update_by_alerts(alerts, mock_datetime)
        self.tenant_alert_usecase.tenant_alert_repo.update.assert_called_once_with(tenant_alert)

    def test_send_alert_to_admins(self, setup):
        # Input
        tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=search_domain.Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=search_domain.IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=llm_domain.AllowForeignRegion(root=False),
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
            allowed_model_families=[llm_domain.ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )
        alerts = [
            tenant_alert_domain.Alert(
                limit=tenant_alert_domain.Limit(root=100),
                usage=search_domain.StorageUsage(root=90),
                type=tenant_alert_domain.AlertType.STORAGE,
            )
        ]
        admins: list[user_domain.User] = [
            user_domain.User(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
                policies=[],
            ),
        ]
        administrators: list[user_domain.Administrator] = [
            user_domain.Administrator(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@neoai.jp"),
                created_at=administrator_domain.CreatedAt(value=datetime.now()),
            ),
        ]

        # Mock
        self.tenant_alert_usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.tenant_alert_usecase.user_repo.find_admins_by_tenant_id = Mock(return_value=admins)
        self.tenant_alert_usecase.user_repo.find_administrators = Mock(return_value=administrators)

        # Call
        self.tenant_alert_usecase._send_alert_to_admins(tenant_id=tenant.id, alerts=alerts)

        # Test
        self.tenant_alert_usecase.tenant_repo.find_by_id.aserrt_called_once_with(tenant.id)
        self.tenant_alert_usecase.user_repo.find_admins_by_tenant_id.assert_called_once_with(tenant.id)
        self.tenant_alert_usecase.user_repo.find_administrators.assert_called_once_with()
        self.tenant_alert_usecase.msgraph_service.send_alert_email_to_tenant_users.assert_called_once_with(
            tenant_name=tenant.name,
            alerts=alerts,
            recipients=[admin.email for admin in admins],
            bcc_recipients=[administrator.email for administrator in administrators],
        )
