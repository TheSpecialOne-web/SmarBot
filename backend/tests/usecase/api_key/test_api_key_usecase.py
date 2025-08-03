import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.usecase.api_key import ApiKeyUseCase
from api.usecase.api_key.api_key import ApiKeyWithBot, GetApiKeysOutput


class TestApiKeyUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.api_key_repo = Mock()
        self.api_key_usecase = ApiKeyUseCase(
            bot_repo=self.bot_repo,
            api_key_repo=self.api_key_repo,
        )

    def dummy_tenant(self):
        return tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="Test Tenant"),
            alias=tenant_domain.Alias(root="test-tenant"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-index"),
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-tenant"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_bot(self):
        return bot_domain.Bot(
            id=bot_domain.Id(value=1),
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#000000"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def test_get_api_keys(self, setup):
        """API key 取得テスト"""
        # input
        tenant = self.dummy_tenant()
        bot = self.dummy_bot()

        # mock
        api_key = api_key_domain.ApiKey(
            id=api_key_domain.Id(root=uuid.uuid4()),
            bot_id=bot.id,
            name=api_key_domain.Name(root="test_get_api_keys_name"),
            decrypted_api_key=api_key_domain.DecryptedApiKey(root="test_get_api_keys_decrypted_api_key"),
            expires_at=None,
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
        )
        self.api_key_usecase.bot_repo.find_by_ids_and_tenant_id = Mock(return_value=[bot])
        self.api_key_usecase.api_key_repo.find_all = Mock(return_value=[api_key])

        # run
        out = self.api_key_usecase.get_api_keys(tenant.id)

        # assert
        assert out == GetApiKeysOutput(
            api_keys=[
                ApiKeyWithBot(
                    id=api_key.id,
                    bot=bot,
                    name=api_key.name,
                    api_key=api_key.decrypted_api_key,
                    expires_at=api_key.expires_at,
                    endpoint_id=api_key.endpoint_id,
                )
            ]
        )
        self.api_key_usecase.api_key_repo.find_all.assert_called_once_with(tenant.id)
        self.api_key_usecase.bot_repo.find_by_ids_and_tenant_id.assert_called_once_with([bot.id], tenant.id)

    def test_create_api_key(self, setup):
        """API key 作成テスト"""
        # input
        tenant = self.dummy_tenant()
        bot = self.dummy_bot()
        api_key_for_create = api_key_domain.ApiKeyForCreate(
            bot_id=bot.id,
            name=api_key_domain.Name(root="test_create_api_key_name"),
            expires_at=None,
        )

        # mock
        self.api_key_usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.api_key_usecase.api_key_repo.create = Mock(
            return_value=api_key_domain.ApiKey(
                id=api_key_domain.Id(root=uuid.uuid4()),
                bot_id=bot.id,
                name=api_key_domain.Name(root="test_create_api_key_name"),
                decrypted_api_key=api_key_domain.DecryptedApiKey(root="test_create_api_key_decrypted_api_key"),
                expires_at=None,
                endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            )
        )

        # run
        self.api_key_usecase.create_api_key(tenant.id, api_key_for_create)

        # assert
        self.api_key_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(
            api_key_for_create.bot_id, tenant.id
        )
        self.api_key_usecase.api_key_repo.create.assert_called_once_with(api_key_for_create)

    def test_delete_api_keys(self, setup):
        """API key 複数削除テスト"""
        # input
        tenant_id = tenant_domain.Id(value=1)
        api_key_ids = [
            api_key_domain.Id(root=uuid.uuid4()),
            api_key_domain.Id(root=uuid.uuid4()),
        ]

        # mock
        self.api_key_usecase.api_key_repo.delete_by_ids_and_tenant_id = Mock()

        # run
        self.api_key_usecase.delete_api_keys(tenant_id, api_key_ids)

        # assert
        self.api_key_usecase.api_key_repo.delete_by_ids_and_tenant_id.assert_called_once_with(api_key_ids, tenant_id)
