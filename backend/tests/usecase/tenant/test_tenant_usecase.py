import datetime
from typing import Optional
from unittest.mock import Mock, call
import uuid
from uuid import UUID

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    prompt_template as pt_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion, Platform
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, EndpointsWithPriority, EndpointWithPriority, IndexName, Priority
from api.domain.models.search.storage_usage import StorageUsage
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.models.tenant.statistics import UserCount
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.libs.exceptions import BadRequest
from api.usecase.tenant import TenantUseCase
from api.usecase.tenant.tenant import (
    UpdateTenantAllowedModelFamilyInput,
    UpdateTenantBasicAiInput,
    UpdateTenantLogoInput,
)


class TestTenantUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.metering_repo = Mock()
        self.user_repo = Mock()
        self.bot_repo = Mock()
        self.prompt_template_repo = Mock()
        self.group_repo = Mock()
        self.user_repo = Mock()
        self.auth0_service = Mock()
        self.cognitive_search_service = Mock()
        self.blob_storage_service = Mock()
        self.queue_storage_service = Mock()
        self.msgraph_service = Mock()
        self.box_service = Mock()
        self.tenant_usecase = TenantUseCase(
            tenant_repo=self.tenant_repo,
            group_repo=self.group_repo,
            metering_repo=self.metering_repo,
            prompt_template_repo=self.prompt_template_repo,
            bot_repo=self.bot_repo,
            user_repo=self.user_repo,
            auth0_service=self.auth0_service,
            cognitive_search_service=self.cognitive_search_service,
            blob_storage_service=self.blob_storage_service,
            queue_storage_service=self.queue_storage_service,
            msgraph_service=self.msgraph_service,
            box_service=self.box_service,
        )

    @pytest.fixture
    def mock_get_feature_flag_with_anonymous_context(self, monkeypatch):
        mock_get_feature_flag_with_anonymous_context = Mock()
        monkeypatch.setattr(
            "api.usecase.tenant.tenant.get_feature_flag_with_anonymous_context",
            mock_get_feature_flag_with_anonymous_context,
        )
        return mock_get_feature_flag_with_anonymous_context

    @pytest.fixture
    def mock_get_available_search_service_endpoint(self, monkeypatch):
        mock_get_available_search_service_endpoint = Mock(
            return_value=Endpoint(root="https://test-search-service-endpoint.com")
        )
        monkeypatch.setattr(
            "api.usecase.tenant.tenant.TenantUseCase._get_available_search_service_endpoint",
            mock_get_available_search_service_endpoint,
        )
        return mock_get_available_search_service_endpoint

    @pytest.fixture
    def mock_create_endpoint_id(self, monkeypatch):
        mock_create_endpoint_id = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440000"))
        monkeypatch.setattr("api.domain.models.bot.endpoint_id.uuid4", mock_create_endpoint_id)
        return mock_create_endpoint_id

    @pytest.fixture
    def mock_container_name(self, monkeypatch):
        mock_container_name = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440000"))
        monkeypatch.setattr("api.domain.models.bot.bot.uuid.uuid4", mock_container_name)
        return mock_container_name

    def dummy_bot(
        self,
        bot_id: bot_domain.Id,
        approach: bot_domain.Approach = bot_domain.Approach.CHAT_GPT_DEFAULT,
        search_method: Optional[bot_domain.SearchMethod] = None,
        status: bot_domain.Status = bot_domain.Status.ACTIVE,
    ):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=approach,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=search_method,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=status,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#000000"),
            endpoint_id=bot_domain.EndpointId(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_tenant(
        self,
        tenant_id: tenant_domain.Id,
        allow_foreign_region: AllowForeignRegion | None = None,
        additional_platforms: tenant_domain.AdditionalPlatformList | None = None,
        allowed_model_families: list[ModelFamily | Text2ImageModelFamily] | None = None,
        enable_external_data_integrations: tenant_domain.EnableExternalDataIntegrations | None = None,
    ):
        return tenant_domain.Tenant(
            id=tenant_id,
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=allow_foreign_region
            if allow_foreign_region is not None
            else AllowForeignRegion(root=True),
            additional_platforms=additional_platforms
            if additional_platforms is not None
            else tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=allowed_model_families
            if allowed_model_families is not None
            else [ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=enable_external_data_integrations
            if enable_external_data_integrations is not None
            else tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_group(
        self,
        group_id: group_domain.Id,
    ):
        return group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=True),
            created_at=group_domain.CreatedAt(value=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )

    def test_get_available_search_service_endpoint(self, setup):
        """インデックス名バリデーションテスト"""
        index_name = IndexName(root="test")
        endpoints_with_priority = EndpointsWithPriority(
            root=[
                EndpointWithPriority(
                    endpoint=Endpoint(root="https://test-search-service-endpoint-1.com"),
                    priority=Priority(root=1),
                ),
                EndpointWithPriority(
                    endpoint=Endpoint(root="https://test-search-service-endpoint-2.com"),
                    priority=Priority(root=2),
                ),
            ]
        )

        self.tenant_usecase.cognitive_search_service.list_endpoints = Mock(return_value=endpoints_with_priority)
        self.tenant_usecase.cognitive_search_service.list_index_names = Mock(return_value=[IndexName(root="test1")])

        got = self.tenant_usecase._get_available_search_service_endpoint(index_name)
        assert got == Endpoint(root="https://test-search-service-endpoint-2.com")

    def test_create_tenant(
        self,
        setup,
        mock_get_feature_flag_with_anonymous_context,
        mock_get_available_search_service_endpoint,
        mock_create_endpoint_id,
        mock_container_name,
    ):
        """テナント作成テスト"""

        mock_get_feature_flag_with_anonymous_context.return_value = True

        tenant_for_create = tenant_domain.TenantForCreate(
            name=tenant_domain.Name(value="test_tenant_name"),
            alias=tenant_domain.Alias(root="test-tenant-alias"),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
        )
        admin_user = user_domain.UserForCreate(
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
        )
        tenant_id = tenant_domain.Id(value=1)
        created_tenant = tenant_domain.Tenant(
            id=tenant_id,
            name=tenant_domain.Name(value="test_tenant_name"),
            alias=tenant_domain.Alias(root="test-tenant-alias"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-tenant-alias"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=True),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(
                free_storage=5 * 2**30,
                document_intelligence_page=8000,
            ),
            container_name=ContainerName(root="test-tenant-alias"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[
                ModelFamily.GPT_35_TURBO,
                ModelFamily.GPT_4,
                ModelFamily.GPT_4O,
                ModelFamily.GPT_4O_MINI,
            ],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )
        group_id = group_domain.Id(value=1)
        group_name = group_domain.Name(value=f"{created_tenant.name.value} All")
        created_group = group_domain.Group(
            id=group_id,
            name=group_name,
            created_at=group_domain.CreatedAt(value=datetime.datetime.strptime("20240101", "%Y%m%d")),
            is_general=group_domain.IsGeneral(root=True),
        )

        self.tenant_usecase.cognitive_search_service.list_index_names.return_value = []
        self.tenant_usecase.auth0_service.find_by_emails.return_value = []
        self.tenant_usecase.user_repo.find_by_email.return_value = None
        self.tenant_usecase.tenant_repo.create.return_value = created_tenant
        self.tenant_usecase.auth0_service.create_user.return_value = "test_auth0_user_id"
        self.tenant_usecase.user_repo.create.return_value = user_domain.Id(value=1)
        self.tenant_usecase.bot_repo.create.return_value = None
        self.tenant_usecase.group_repo.create_group.return_value = created_group
        self.tenant_usecase.prompt_template_repo.bulk_create.return_value = None
        self.tenant_usecase.cognitive_search_service.create_tenant_index.return_value = None
        self.tenant_usecase.blob_storage_service.create_blob_container.return_value = None

        self.tenant_usecase.create_tenant(tenant_for_create, admin_user)

        self.tenant_usecase.tenant_repo.create.assert_called_once_with(tenant_for_create)
        self.tenant_usecase.auth0_service.create_user.assert_called_once_with(admin_user.email)
        self.tenant_usecase.user_repo.create.assert_called_once_with(
            tenant_id=tenant_id,
            user=user_domain.UserForCreate(
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
            ),
            auth0_id="test_auth0_user_id",
        )
        self.tenant_usecase.group_repo.create_group.assert_called_once_with(
            tenant_id=tenant_id,
            name=group_name,
            is_general=group_domain.IsGeneral(root=True),
        )
        bots_for_create = [
            bot_domain.BasicAiForCreate(
                tenant=created_tenant,
                model_family=ModelFamily.GPT_35_TURBO,
            ),
            bot_domain.BasicAiForCreate(
                tenant=created_tenant,
                model_family=ModelFamily.GPT_4,
            ),
        ]
        bot_repo_create_calls = [
            call(tenant_id=tenant_id, group_id=group_id, bot=bot_for_create) for bot_for_create in bots_for_create
        ]
        self.tenant_usecase.bot_repo.create.assert_has_calls(bot_repo_create_calls)
        self.tenant_usecase.prompt_template_repo.bulk_create.assert_called_once_with(
            tenant_id=tenant_id,
            prompt_templates=pt_domain.DefaultPromptTemplates().prompt_templates,
        )
        self.tenant_usecase.cognitive_search_service.create_tenant_index.assert_called_once_with(
            endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-tenant-alias"),
        )
        if mock_get_feature_flag_with_anonymous_context.return_value:
            self.tenant_usecase.blob_storage_service.create_blob_container.assert_called_once_with(
                ContainerName(root="test-tenant-alias")
            )

    def test_get_tenants(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント取得テスト"""
        self.tenant_usecase.tenant_repo.find_all.return_value = []

        self.tenant_usecase.get_tenants()

        self.tenant_usecase.tenant_repo.find_all.assert_called_once()

    def test_get_tenant_by_id(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナントIDによるテナント取得テスト"""
        tenant_id = tenant_domain.Id(value=1)

        self.tenant_usecase.tenant_repo.find_by_id.return_value = None

        self.tenant_usecase.get_tenant_by_id(tenant_id)

        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)

    def test_get_tenant_storage_usage(self, setup):
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        self.tenant_usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.tenant_usecase.cognitive_search_service.get_index_storage_usage = Mock(
            return_value=StorageUsage(root=100)
        )

        got = self.tenant_usecase.get_tenant_storage_usage(tenant.id)

        self.tenant_usecase.cognitive_search_service.get_index_storage_usage.assert_called_once_with(
            endpoint=tenant.search_service_endpoint, index_name=tenant.index_name
        )
        assert got == StorageUsage(root=100)

    def test_update_tenant(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント更新テスト"""
        tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            alias=tenant_domain.Alias(root="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
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

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.tenant_repo.update.return_value = None

        self.tenant_usecase.update_tenant(
            tenant_domain.Id(value=1),
            tenant_domain.TenantForUpdate(
                name=tenant_domain.Name(value="update"),
                status=tenant_domain.Status.SUBSCRIBED,
                allowed_ips=tenant_domain.AllowedIPs(root=[]),
                is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
                allow_foreign_region=AllowForeignRegion(root=False),
                additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
                enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
                enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
                enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
                usage_limit=tenant_domain.UsageLimit(
                    free_user_seat=50,
                    additional_user_seat=10,
                    free_token=10000000,
                    additional_token=0,
                    free_storage=1000000000,
                    additional_storage=0,
                    document_intelligence_page=8000,
                ),
                enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
                enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
                basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
                max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
                enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
            ),
        )

        self.tenant_usecase.tenant_repo.update.assert_called_once_with(
            tenant_domain.Tenant(
                id=tenant.id,
                name=tenant_domain.Name(value="update"),
                alias=tenant_domain.Alias(root="test"),
                status=tenant_domain.Status.SUBSCRIBED,
                allowed_ips=tenant_domain.AllowedIPs(root=[]),
                search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
                index_name=IndexName(root="test"),
                is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
                allow_foreign_region=AllowForeignRegion(root=False),
                additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
                enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
                enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
                enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
                usage_limit=tenant_domain.UsageLimit(
                    free_user_seat=50,
                    additional_user_seat=10,
                    free_token=10000000,
                    additional_token=0,
                    free_storage=1000000000,
                    additional_storage=0,
                    document_intelligence_page=8000,
                ),
                container_name=ContainerName(root="test"),
                enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
                enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
                basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
                max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
                allowed_model_families=[ModelFamily.GPT_35_TURBO],
                basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
                enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
            )
        )

    def test_update_tenant_with_invalid_additional_platforms(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント更新テスト(プラットフォームが追加されていない場合)"""
        tenant = self.dummy_tenant(
            tenant_id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList(
                root=[tenant_domain.AdditionalPlatform(root=Platform.GCP)]
            ),
            allowed_model_families=[ModelFamily.GEMINI_15_PRO],
        )
        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        with pytest.raises(BadRequest):
            tenant.update(
                tenant_domain.TenantForUpdate(
                    name=tenant_domain.Name(value="update"),
                    status=tenant_domain.Status.SUBSCRIBED,
                    allowed_ips=tenant_domain.AllowedIPs(root=[]),
                    is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
                    allow_foreign_region=AllowForeignRegion(root=False),
                    # ここだけupdateしている
                    additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
                    enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
                    enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
                    enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
                    usage_limit=tenant_domain.UsageLimit(
                        free_user_seat=50,
                        additional_user_seat=10,
                        free_token=10000000,
                        additional_token=0,
                        free_storage=1000000000,
                        additional_storage=0,
                        document_intelligence_page=8000,
                    ),
                    enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
                    enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
                    max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
                    enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
                )
            )

    def test_update_tenant_with_invalid_allow_foreign_region(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント更新テスト(海外リージョンが許可されていない場合)"""
        tenant = self.dummy_tenant(
            tenant_id=tenant_domain.Id(value=1),
            allow_foreign_region=AllowForeignRegion(root=True),
            allowed_model_families=[ModelFamily.GPT_4O],
        )
        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        with pytest.raises(BadRequest):
            tenant.update(
                tenant_domain.TenantForUpdate(
                    name=tenant_domain.Name(value="update"),
                    status=tenant_domain.Status.SUBSCRIBED,
                    allowed_ips=tenant_domain.AllowedIPs(root=[]),
                    is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
                    # ここだけupdateしている
                    allow_foreign_region=AllowForeignRegion(root=False),
                    additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
                    enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
                    enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
                    enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
                    usage_limit=tenant_domain.UsageLimit(
                        free_user_seat=50,
                        additional_user_seat=10,
                        free_token=10000000,
                        additional_token=0,
                        free_storage=1000000000,
                        additional_storage=0,
                        document_intelligence_page=8000,
                    ),
                    enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
                    enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
                    max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
                    enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
                )
            )

    def test_delete_tenant(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント削除テスト"""
        tenant_id = tenant_domain.Id(value=1)

        self.tenant_usecase.bot_repo.find_all_by_tenant_id.return_value = []
        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant_domain.Tenant(
            id=tenant_id,
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
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
        self.tenant_usecase.user_repo.find_by_tenant_id.return_value = []

        self.tenant_usecase.group_repo.delete_by_tenant_id.return_value = None
        self.tenant_usecase.user_repo.delete_by_tenant_id.return_value = None
        self.tenant_usecase.prompt_template_repo.delete_by_tenant_id.return_value = None
        self.tenant_usecase.metering_repo.delete_by_tenant_id.return_value = None
        self.tenant_usecase.tenant_repo.delete.return_value = None
        self.tenant_usecase.auth0_service.delete_user.return_value = None
        self.tenant_usecase.cognitive_search_service.delete_index.return_value = None

        self.tenant_usecase.delete_tenant(tenant_id)

        self.tenant_usecase.bot_repo.find_all_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.user_repo.find_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.group_repo.delete_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.user_repo.delete_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.prompt_template_repo.delete_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.metering_repo.delete_by_tenant_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.tenant_repo.delete.assert_called_once_with(tenant_id)
        self.tenant_usecase.auth0_service.delete_users.assert_called_once_with([])
        self.tenant_usecase.cognitive_search_service.delete_index.assert_called_once_with(
            endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
        )

    def test_update_masked(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナントマスク更新テスト"""
        self.tenant_usecase.tenant_repo.update_masked.return_value = None

        self.tenant_usecase.update_tenant_masked(
            tenant_domain.Id(value=1),
            tenant_domain.IsSensitiveMasked(root=False),
        )

        self.tenant_usecase.tenant_repo.update_masked.assert_called_once_with(
            tenant_domain.Id(value=1), tenant_domain.IsSensitiveMasked(root=False)
        )

    def test_get_tenant_user_count(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナントユーザ数取得テスト"""

        self.tenant_usecase.tenant_repo.get_user_count.return_value = UserCount(root=10)

        got = self.tenant_usecase.get_tenant_user_count(tenant_domain.Id(value=1))

        self.tenant_usecase.tenant_repo.get_user_count.assert_called_once_with(tenant_domain.Id(value=1))
        assert got == UserCount(root=10)

    def test_upload_logo(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナントロゴアップロードテスト"""

        self.tenant_usecase.blob_storage_service.upload_image_to_common_container.return_value = (
            "https://example.com/logo.png"
        )

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant_domain.Tenant(
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
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
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

        input = UpdateTenantLogoInput(
            tenant_id=tenant_domain.Id(value=1),
            file_name="logo.png",
            logo_file=b"test",
        )

        self.tenant_usecase.upload_logo(input)

        self.tenant_usecase.blob_storage_service.upload_image_to_common_container.assert_called_once_with(
            "logo.png",
            b"test",
        )

    def test_update_tenant_basic_ai_to_disable(self, setup, mock_create_endpoint_id):
        """基盤モデル無効化テスト"""
        tenant = self.dummy_tenant(
            tenant_id=tenant_domain.Id(value=1),
            allowed_model_families=[ModelFamily.GPT_4],
        )
        group = self.dummy_group(group_id=group_domain.Id(value=1))
        bot = self.dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            status=bot_domain.Status.ACTIVE,
        )
        archived_bot = self.dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            status=bot_domain.Status.BASIC_AI_DELETED,
        )
        archived_bot.created_at = bot.created_at

        self.tenant_usecase.group_repo.find_general_group_by_tenant_id.return_value = group
        self.tenant_usecase.bot_repo.find_basic_ai_by_response_generator_model_family.return_value = bot

        self.tenant_usecase.update_tenant_basic_ai(
            UpdateTenantBasicAiInput(
                tenant=tenant,
                model_family=ModelFamily.GPT_4,
                enabled=False,
            )
        )

        self.tenant_usecase.group_repo.find_general_group_by_tenant_id.assert_called_once_with(
            tenant_domain.Id(value=1)
        )
        self.tenant_usecase.bot_repo.find_basic_ai_by_response_generator_model_family.assert_called_once_with(
            tenant_id=tenant_domain.Id(value=1),
            group_id=group_domain.Id(value=1),
            model_family=ModelFamily.GPT_4,
            statuses=[bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED, bot_domain.Status.BASIC_AI_DELETED],
        )
        self.tenant_usecase.bot_repo.update.assert_called_once_with(archived_bot)

    def test_update_tenant_basic_ai_to_create(self, setup, mock_create_endpoint_id, mock_container_name):
        """基盤モデル作成テスト"""
        tenant = tenant_domain.Tenant(
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
        group = self.dummy_group(group_id=group_domain.Id(value=1))

        self.tenant_usecase.group_repo.find_general_group_by_tenant_id.return_value = group
        self.tenant_usecase.bot_repo.find_basic_ai_by_response_generator_model_family.return_value = None

        self.tenant_usecase.update_tenant_basic_ai(
            UpdateTenantBasicAiInput(
                tenant=tenant,
                model_family=ModelFamily.GPT_4,
                enabled=True,
            )
        )

        self.tenant_usecase.group_repo.find_general_group_by_tenant_id.assert_called_once_with(
            tenant_domain.Id(value=1)
        )
        self.tenant_usecase.bot_repo.create.assert_called_once_with(
            tenant_id=tenant_domain.Id(value=1),
            group_id=group_domain.Id(value=1),
            bot=bot_domain.BasicAiForCreate(
                tenant=tenant,
                model_family=ModelFamily.GPT_4,
            ),
        )

    def test_update_tenant_basic_ai_pdf_parser(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント基本AIドキュメント読み取りオプション更新テスト"""

        tenant = tenant_domain.Tenant(
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

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant

        self.tenant_usecase.tenant_repo.update.return_value = None

        self.tenant_usecase.update_tenant_basic_ai_pdf_parser(
            tenant_domain.Id(value=1),
            llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE),
        )

        tenant.update_basic_ai_pdf_parser(llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE)

    def test_update_tenant_basic_ai_pdf_parser_with_invalid_value(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント基本AIドキュメント読み取りオプション更新テスト"""
        tenant = tenant_domain.Tenant(
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
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
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

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant

        with pytest.raises(BadRequest):
            tenant.update_basic_ai_pdf_parser(llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE)

    def test_update_tenant_basic_ai_web_browsing(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント基本AIWebブラウジング更新テスト"""

        tenant = tenant_domain.Tenant(
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

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant

        tenant.update_basic_ai_web_browsing(tenant_domain.EnableBasicAiWebBrowsing(root=False))

        self.tenant_usecase.tenant_repo.update.return_value = None

        self.tenant_usecase.update_tenant_basic_ai_web_browsing(
            tenant_domain.Id(value=1),
            tenant_domain.EnableBasicAiWebBrowsing(root=False),
        )

    def test_update_tenant_max_attachment_token(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント最大アタッチメントトークン数更新テスト"""

        tenant = tenant_domain.Tenant(
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
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant

        self.tenant_usecase.tenant_repo.update.return_value = None

        max_attachment_token = tenant_domain.MaxAttachmentToken(root=10000)
        self.tenant_usecase.update_tenant_max_attachment_token(
            tenant_domain.Id(value=1),
            max_attachment_token,
        )

        tenant_dict = tenant.model_dump()
        tenant_dict["max_attachment_token"] = max_attachment_token
        want = tenant_domain.Tenant(**tenant_dict)

        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant.id)
        self.tenant_usecase.tenant_repo.update.assert_called_once_with(want)

    def test_update_tenant_allowed_model_family(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント許可モデルファミリー更新テスト"""
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))

        bots = [
            self.dummy_bot(
                bot_id=bot_domain.Id(value=i + 1),
            )
            for i in range(4)
        ]

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.bot_repo.find_by_tenant_id.return_value = bots
        self.tenant_usecase.tenant_repo.update.return_value = None

        self.tenant_usecase.update_tenant_allowed_model_family(
            UpdateTenantAllowedModelFamilyInput(
                tenant_id=tenant_domain.Id(value=1),
                model_family=ModelFamily.GPT_4,
                is_allowed=True,
            )
        )
        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant.id)
        self.tenant_usecase.tenant_repo.update.assert_called_once_with(tenant)

    def test_update_tenant_allowed_model_family_with_invalid_allow_foreign_region(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント許可モデルファミリー更新テスト（海外リージョンが許可されていない場合）"""
        tenant = self.dummy_tenant(
            tenant_id=tenant_domain.Id(value=1),
            allowed_model_families=[ModelFamily.GPT_4_TURBO],
            allow_foreign_region=AllowForeignRegion(root=False),
        )
        bots = [
            self.dummy_bot(
                bot_id=bot_domain.Id(value=i + 1),
            )
            for i in range(4)
        ]

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.bot_repo.find_by_tenant_id.return_value = bots
        self.tenant_usecase.tenant_repo.update.return_value = None

        with pytest.raises(BadRequest):
            self.tenant_usecase.update_tenant_allowed_model_family(
                UpdateTenantAllowedModelFamilyInput(
                    tenant_id=tenant_domain.Id(value=1),
                    # 海外リージョンが必須のモデルファミリー
                    model_family=ModelFamily.GPT_4_TURBO,
                    is_allowed=True,
                )
            )

    def test_update_tenant_allowed_model_family_with_invalid_additional_platforms(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント許可モデルファミリー更新テスト（必要な追加プラットフォームがない場合）"""
        tenant = self.dummy_tenant(
            tenant_id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
        )

        bots = [
            self.dummy_bot(
                bot_id=bot_domain.Id(value=i + 1),
            )
            for i in range(4)
        ]

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.bot_repo.find_by_tenant_id.return_value = bots
        self.tenant_usecase.tenant_repo.update.return_value = None

        with pytest.raises(BadRequest):
            self.tenant_usecase.update_tenant_allowed_model_family(
                UpdateTenantAllowedModelFamilyInput(
                    tenant_id=tenant_domain.Id(value=1),
                    model_family=ModelFamily.GEMINI_15_PRO,
                    is_allowed=True,
                )
            )

    def test_update_tenant_allowed_model_family_with_bot_using_model_family(
        self, setup, mock_get_feature_flag_with_anonymous_context
    ):
        """テナント許可モデルファミリー更新テスト(ボットが使用しているモデルファミリーを削除しようしている場合)"""
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        bots = [self.dummy_bot(bot_id=bot_domain.Id(value=i + 1)) for i in range(4)]

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.bot_repo.find_by_tenant_id.return_value = bots
        self.tenant_usecase.tenant_repo.update.return_value = None

        with pytest.raises(BadRequest):
            self.tenant_usecase.update_tenant_allowed_model_family(
                UpdateTenantAllowedModelFamilyInput(
                    tenant_id=tenant_domain.Id(value=1),
                    model_family=bots[0].response_generator_model_family,
                    is_allowed=False,
                )
            )

    def test_update_tenant_basic_ai_max_conversation_turns(self, setup, mock_get_feature_flag_with_anonymous_context):
        """テナント基本AI最大会話ターン数更新テスト"""
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))

        self.tenant_usecase.tenant_repo.find_by_id.return_value = tenant
        self.tenant_usecase.tenant_repo.update.return_value = None

        self.tenant_usecase.update_tenant_basic_ai_max_conversation_turns(
            tenant_domain.Id(value=1),
            tenant_domain.BasicAiMaxConversationTurns(root=10),
        )

        tenant.update_basic_ai_max_conversation_turns(tenant_domain.BasicAiMaxConversationTurns(root=10))

        self.tenant_usecase.tenant_repo.update.assert_called_once_with(tenant)

    def test_get_external_data_connections(self, setup):
        """外部データ連携情報取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        external_data_connections = [
            external_data_connection_domain.ExternalDataConnection(
                id=external_data_connection_domain.Id(root=uuid.uuid4()),
                tenant_id=tenant_id,
                external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                    type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                    raw={
                        "client_id": "test_client_id",
                        "client_secret": "test_client_secret",
                        "tenant_id": "test_tenant_id",
                    },
                ).encrypt(),
            )
        ]

        self.tenant_usecase.tenant_repo.get_external_data_connections.return_value = external_data_connections

        got = self.tenant_usecase.get_external_data_connections(tenant_id)

        self.tenant_usecase.tenant_repo.get_external_data_connections.assert_called_once_with(tenant_id)
        assert got[0].hidden_credentials == external_data_connection_domain.HiddenCredentials(
            root={
                "client_id": "tes" + "*" * 10,
                "client_secret": "tes" + "*" * 10,
                "tenant_id": "tes" + "*" * 10,
            }
        )

    def test_create_sharepoint_connection(self, setup):
        """外部データ連携情報作成テスト for SharePoint"""
        tenant_id = tenant_domain.Id(value=1)
        connection_for_create = external_data_connection_domain.ExternalDataConnectionForCreate(
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            decrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "tenant_id": "test_tenant_id",
                },
            ),
        )

        self.tenant_usecase.tenant_repo.find_by_id = Mock(
            return_value=self.dummy_tenant(
                tenant_id=tenant_id,
                enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=True),
            )
        )

        async def mock_is_authorized_client(*args, **kwargs):
            return True

        self.tenant_usecase.msgraph_service.is_authorized_client = Mock(side_effect=mock_is_authorized_client)
        self.tenant_usecase.tenant_repo.create_external_data_connection = Mock()

        self.tenant_usecase.create_external_data_connection(connection_for_create)

        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.tenant_repo.create_external_data_connection.assert_called_once_with(connection_for_create)

    def test_create_box_connection(self, setup):
        """外部データ連携情報作成テスト for Box"""
        tenant_id = tenant_domain.Id(value=1)
        connection_for_create = external_data_connection_domain.ExternalDataConnectionForCreate(
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            decrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.BOX,
                raw={
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "enterprise_id": "test_enterprise_id",
                },
            ),
        )

        self.tenant_usecase.tenant_repo.find_by_id = Mock(
            return_value=self.dummy_tenant(
                tenant_id=tenant_id,
                enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=True),
            )
        )

        self.tenant_usecase.box_service.is_authorized_client = Mock(return_value=True)
        self.tenant_usecase.tenant_repo.create_external_data_connection = Mock()

        self.tenant_usecase.create_external_data_connection(connection_for_create)

        self.tenant_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.tenant_usecase.tenant_repo.create_external_data_connection.assert_called_once_with(connection_for_create)

    def test_delete_external_data_connection(self, setup):
        """外部データ連携情報削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        connection_id = external_data_connection_domain.Id(root=uuid.uuid4())

        self.tenant_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant(
            tenant_id=tenant_id,
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=True),
        )

        self.tenant_usecase.tenant_repo.hard_delete_external_data_connection.return_value = None

        self.tenant_usecase.delete_external_data_connection(tenant_id, connection_id)

        self.tenant_usecase.tenant_repo.hard_delete_external_data_connection.assert_called_once_with(
            tenant_id, connection_id
        )
