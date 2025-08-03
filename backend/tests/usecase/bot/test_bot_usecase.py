from datetime import datetime
from typing import Optional
from unittest.mock import Mock, patch
import uuid
from uuid import UUID, uuid4

import pytest

from api.domain.models import (
    bot as bot_domain,
    bot_template as bot_template_domain,
    common_document_template as cdt_domain,
    common_prompt_template as cpt_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    policy as policy_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.bot import prompt_template as bot_prompt_template_domain
from api.domain.models.bot.icon_file_extension import IconFileExtension
from api.domain.models.bot.icon_url import IconUrl
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.libs.ctx import ContextUser
from api.libs.exceptions import BadRequest, NotFound
from api.usecase.bot import BotUseCase, GetBotsByCurrentUserInput, UpdateBotByUserInput, UploadBotIconInput
from api.usecase.bot.bot import UpdateLikedBotInput


class TestBotUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.cognitive_search_service = Mock()
        self.blob_storage_service = Mock()
        self.tenant_repo = Mock()
        self.bot_template_repo = Mock()
        self.common_document_template_repo = Mock()
        self.document_repo = Mock()
        self.document_folder_repo = Mock()
        self.common_prompt_template_repo = Mock()
        self.api_key_repo = Mock()
        self.group_repo = Mock()
        self.queue_storage_service = Mock()
        self.group_repo = Mock()
        self.user_repo = Mock()
        self.bot_usecase = BotUseCase(
            bot_repo=self.bot_repo,
            cognitive_search_service=self.cognitive_search_service,
            blob_storage_service=self.blob_storage_service,
            tenant_repo=self.tenant_repo,
            bot_template_repo=self.bot_template_repo,
            common_document_template_repo=self.common_document_template_repo,
            document_repo=self.document_repo,
            document_folder_repo=self.document_folder_repo,
            common_prompt_template_repo=self.common_prompt_template_repo,
            api_key_repo=self.api_key_repo,
            queue_storage_service=self.queue_storage_service,
            group_repo=self.group_repo,
            user_repo=self.user_repo,
        )

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock()
        monkeypatch.setattr("api.usecase.bot.bot.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def dummy_bot(
        self,
        bot_id: bot_domain.Id,
        group_id: group_domain.Id | None = None,
        approach: bot_domain.Approach = bot_domain.Approach.CHAT_GPT_DEFAULT,
        search_method: Optional[bot_domain.SearchMethod] = None,
        status: bot_domain.Status = bot_domain.Status.ACTIVE,
        response_generator_model_family: ModelFamily = ModelFamily.GPT_35_TURBO,
    ):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_id if group_id is not None else group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=approach,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=search_method,
            response_generator_model_family=response_generator_model_family,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=status,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#000000"),
            endpoint_id=bot_domain.EndpointId(root=UUID("81e418a2-820b-4059-82ee-3e90174ee5f5")),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_bot_with_group_name(
        self,
        bot_id: bot_domain.Id,
        group_id: group_domain.Id,
        approach: bot_domain.Approach = bot_domain.Approach.CHAT_GPT_DEFAULT,
        search_method: Optional[bot_domain.SearchMethod] = None,
        status: bot_domain.Status = bot_domain.Status.ACTIVE,
        response_generator_model_family: ModelFamily = ModelFamily.GPT_35_TURBO,
    ):
        bot = self.dummy_bot(
            bot_id=bot_id,
            group_id=group_id,
            approach=approach,
            search_method=search_method,
            status=status,
            response_generator_model_family=response_generator_model_family,
        )
        return bot_domain.BotWithGroupName(
            id=bot.id,
            group_id=bot.group_id,
            name=bot.name,
            description=bot.description,
            created_at=bot.created_at,
            index_name=bot.index_name,
            container_name=bot.container_name,
            approach=bot.approach,
            pdf_parser=bot.pdf_parser,
            example_questions=bot.example_questions,
            search_method=bot.search_method,
            response_generator_model_family=bot.response_generator_model_family,
            approach_variables=bot.approach_variables,
            enable_web_browsing=bot.enable_web_browsing,
            enable_follow_up_questions=bot.enable_follow_up_questions,
            status=bot.status,
            icon_url=bot.icon_url,
            icon_color=bot.icon_color,
            endpoint_id=bot.endpoint_id,
            max_conversation_turns=bot.max_conversation_turns,
            group_name=group_domain.Name(value="Test Group"),
        )

    def dummy_assistant(
        self,
        bot_id: bot_domain.Id,
        approach: bot_domain.Approach = bot_domain.Approach.NEOLLM,
        search_method: Optional[bot_domain.SearchMethod] = bot_domain.SearchMethod.SEMANTIC_HYBRID,
        status: bot_domain.Status = bot_domain.Status.ACTIVE,
    ):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Assistant"),
            description=bot_domain.Description(value="This is a test assistant."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
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
            endpoint_id=bot_domain.EndpointId(root=UUID("81e418a2-820b-4059-82ee-3e90174ee5f5")),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_group(
        self,
        group_id: group_domain.Id,
    ):
        return group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="Test Group"),
            created_at=group_domain.CreatedAt(value=datetime.now()),
            is_general=group_domain.IsGeneral(root=False),
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

    def dummy_bot_template(self, id: bot_template_domain.Id, is_public=True):
        return bot_template_domain.BotTemplate(
            id=id,
            name=bot_template_domain.Name(root="Test Bot Made By Template"),
            description=bot_template_domain.Description(root="This is a test bot made by template."),
            approach=bot_template_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root="Test response system prompt"),
            document_limit=bot_template_domain.DocumentLimit(root=5),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=False),
            is_public=bot_template_domain.IsPublic(root=is_public),
            icon_color=bot_template_domain.IconColor(root="#000000"),
        )

    def dummy_bot_prompt_templates(self):
        return [
            cpt_domain.CommonPromptTemplate(
                id=cpt_domain.Id(root=uuid4()),
                title=cpt_domain.Title(root="Test Prompt Template"),
                prompt=cpt_domain.Prompt(root="Test prompt"),
            )
        ]

    def dummy_bot_document_templates(self):
        return [
            cdt_domain.CommonDocumentTemplate(
                id=cdt_domain.Id(root=uuid4()),
                basename=cdt_domain.Basename(root="test"),
                memo=cdt_domain.Memo(root="Test document template"),
                file_extension=cdt_domain.FileExtension("pdf"),
                created_at=cdt_domain.CreatedAt(root=datetime.now()),
            )
        ]

    def test_validate_pdf_parser(self, setup):
        tenant = self.dummy_tenant()

        pdf_parser = llm_domain.PdfParser.PYPDF

        got = self.bot_usecase._validate_pdf_parser(tenant, pdf_parser)
        assert got is None

        pdf_parser = llm_domain.PdfParser.DOCUMENT_INTELLIGENCE

        with pytest.raises(BadRequest):
            self.bot_usecase._validate_pdf_parser(tenant, pdf_parser)

    def test_validate_allowed_model_families(self, setup):
        tenant = self.dummy_tenant()

        response_generator_model_family = ModelFamily.GPT_35_TURBO

        got = self.bot_usecase._validate_allowed_model_families(tenant, response_generator_model_family)
        assert got is None

        response_generator_model_family = ModelFamily.CLAUDE_3_HAIKU

        with pytest.raises(BadRequest):
            self.bot_usecase._validate_allowed_model_families(tenant, response_generator_model_family)

    def test_find_all_bots_by_tenant_id(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        want = [
            self.dummy_bot(bot_id=bot_domain.Id(value=1)),
            self.dummy_bot(bot_id=bot_domain.Id(value=2)),
        ]

        self.bot_usecase.bot_repo.find_all_by_tenant_id.return_value = want

        got = self.bot_usecase.find_all_bots_by_tenant_id(tenant_id)

        assert got == want
        self.bot_usecase.bot_repo.find_all_by_tenant_id.assert_called_once_with(tenant_id=tenant_id)

    def test_get_bots_by_current_user_admin(self, setup):
        """管理者ユーザーによるボット取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        context_user = ContextUser(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="Test User"),
            email=user_domain.Email(value="test@example.com"),
            tenant=self.dummy_tenant(),
            roles=[user_domain.Role.ADMIN],
            policies=[],
            is_administrator=user_domain.IsAdministrator(value=False),
        )
        input = GetBotsByCurrentUserInput(
            tenant_id=tenant_id,
            current_user=context_user,
            statuses=[bot_domain.Status.ACTIVE],
        )
        dummy_bot = self.dummy_bot_with_group_name(bot_id=bot_domain.Id(value=1), group_id=group_id)

        self.bot_usecase.bot_repo.find_with_groups_by_tenant_id.return_value = [dummy_bot]

        got = self.bot_usecase.get_bots_by_current_user(input)

        assert got == [dummy_bot]
        self.bot_usecase.bot_repo.find_with_groups_by_tenant_id.assert_called_once_with(
            tenant_id=tenant_id, statuses=[bot_domain.Status.ACTIVE]
        )

    def test_get_bot(self, setup):
        """一般ユーザーによるボット取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        want = self.dummy_bot(bot_id=bot_id)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = want

        got = self.bot_usecase.get_bot(tenant_id, bot_id)

        assert got == want
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(
            bot_id,
            tenant_id,
        )

    def test_get_bots_by_current_user_user(self, setup):
        """一般ユーザーによるボット取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group = group_domain.Group(
            id=group_domain.Id(value=1),
            name=group_domain.Name(value="Test Group"),
            created_at=group_domain.CreatedAt(value=datetime.now()),
            is_general=group_domain.IsGeneral(root=False),
        )
        bot = self.dummy_bot_with_group_name(bot_id=bot_domain.Id(value=1), group_id=group.id)

        context_user = ContextUser(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="Test User"),
            email=user_domain.Email(value="test@example.com"),
            tenant=self.dummy_tenant(),
            roles=[user_domain.Role.USER],
            is_administrator=user_domain.IsAdministrator(value=False),
        )
        input = GetBotsByCurrentUserInput(
            tenant_id=tenant_id,
            current_user=context_user,
            statuses=[bot_domain.Status.ACTIVE],
        )

        self.bot_usecase.user_repo.find_policies.return_value = [
            policy_domain.Policy(
                bot_id=bot.id,
                action=policy_domain.Action(root=policy_domain.ActionEnum.READ),
            )
        ]
        self.bot_usecase.bot_repo.find_with_groups_by_ids_and_tenant_id.return_value = [bot]

        got = self.bot_usecase.get_bots_by_current_user(input)

        assert got == [bot]
        self.bot_usecase.bot_repo.find_with_groups_by_ids_and_tenant_id.assert_called_once_with(
            [bot.id], tenant_id, [bot_domain.Status.ACTIVE]
        )
        self.bot_usecase.user_repo.find_policies.assert_called_once_with(context_user.id, tenant_id)

    def test_update_bot_by_user(self, setup):
        """ユーザーによるボット更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        input = UpdateBotByUserInput(
            tenant_id=tenant_id,
            bot_id=bot_id,
            name=bot_domain.Name(value="Updated Bot"),
            description=bot_domain.Description(value="This is an updated bot."),
            example_questions=[bot_domain.ExampleQuestion(value="Updated example question.")],
            approach=bot_domain.Approach.CUSTOM_GPT,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            response_system_prompt=bot_domain.ResponseSystemPrompt(root="Updated response system prompt."),
            document_limit=bot_domain.DocumentLimit(root=5),
            pdf_parser=llm_domain.PdfParser.PYPDF,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            search_method=bot_domain.SearchMethod.BM25,
        )

        current_bot = self.dummy_bot(bot_id=bot_id, approach=bot_domain.Approach.CUSTOM_GPT)

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = current_bot
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = None

        with patch.object(bot_domain.Bot, "update", return_value=None) as mock_update:
            self.bot_usecase.update_bot_by_user(input)

        mock_update.assert_called_once_with(
            bot_domain.BotForUpdate.by_user(
                current=current_bot,
                name=input.name,
                description=input.description,
                example_questions=input.example_questions,
                approach=input.approach,
                response_generator_model_family=input.response_generator_model_family,
                response_system_prompt=input.response_system_prompt,
                document_limit=input.document_limit,
                pdf_parser=input.pdf_parser,
                enable_web_browsing=input.enable_web_browsing,
                enable_follow_up_questions=input.enable_follow_up_questions,
                icon_color=input.icon_color,
                max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                search_method=input.search_method,
            )
        )

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(
            id=bot_id,
            tenant_id=tenant_id,
        )
        self.bot_usecase.bot_repo.update.assert_called_once_with(current_bot)

    def test_update_bot_by_user_with_existing_name(self, setup, mock_get_feature_flag):
        """同名のボットが存在する場合のボット更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        input = UpdateBotByUserInput(
            tenant_id=tenant_id,
            bot_id=bot_id,
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is an updated bot."),
            example_questions=[bot_domain.ExampleQuestion(value="Updated example question.")],
            approach=bot_domain.Approach.CUSTOM_GPT,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            response_system_prompt=bot_domain.ResponseSystemPrompt(root="Updated response system prompt."),
            document_limit=bot_domain.DocumentLimit(root=5),
            pdf_parser=llm_domain.PdfParser.PYPDF,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            search_method=bot_domain.SearchMethod.BM25,
        )

        current_bot = self.dummy_bot(bot_id=bot_id)

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = current_bot
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = self.dummy_bot(
            bot_id=bot_domain.Id(value=2)
        )

        with pytest.raises(BadRequest):
            self.bot_usecase.update_bot_by_user(input)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(
            id=bot_id,
            tenant_id=tenant_id,
        )
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(
            group_id=group_id,
            name=input.name,
        )

    def test_update_bot_by_user_with_document_intelligence_disabled(self, setup, mock_get_feature_flag):
        """Document Intelligenceが無効の場合のボット更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        input = UpdateBotByUserInput(
            tenant_id=tenant_id,
            bot_id=bot_id,
            name=bot_domain.Name(value="Updated Bot"),
            description=bot_domain.Description(value="This is an updated bot."),
            example_questions=[bot_domain.ExampleQuestion(value="Updated example question.")],
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            response_system_prompt=bot_domain.ResponseSystemPrompt(root="Updated response system prompt."),
            document_limit=bot_domain.DocumentLimit(root=5),
            pdf_parser=llm_domain.PdfParser.DOCUMENT_INTELLIGENCE,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            search_method=bot_domain.SearchMethod.BM25,
        )

        current_bot = self.dummy_bot(bot_id=bot_id)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = current_bot
        self.bot_usecase.tenant_repo.find_by_id.return_value = tenant_domain.Tenant(
            id=tenant_id,
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

        with pytest.raises(BadRequest):
            self.bot_usecase.update_bot_by_user(input)

        self.bot_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)

    def test_create_bot_manually(self, setup, mock_get_feature_flag):
        """ボット作成テスト"""

        mock_get_feature_flag.return_value = False

        tenant_id = tenant_domain.Id(value=1)
        creator_id = user_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = None

        self.bot_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = None
        self.bot_usecase.bot_repo.create.return_value = self.dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
        )
        self.bot_usecase.document_folder_repo.find_root_document_folder_by_bot_id.side_effect = NotFound("Not Found")
        self.bot_usecase.cognitive_search_service = Mock()
        self.bot_usecase.blob_storage_service = Mock()

        self.bot_usecase.create_bot(
            tenant_id=tenant_id,
            group_id=group_id,
            bot_for_create=bot_for_create,
            bot_template_id=None,
            creator_id=creator_id,
        )
        self.bot_usecase.document_folder_repo.create_root_document_folder.assert_called()
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(
            group_id=group_id,
            name=bot_for_create.name,
        )
        if not mock_get_feature_flag.return_value:
            self.bot_usecase.blob_storage_service.create_blob_container.assert_called_once_with(
                bot_for_create.container_name
            )

        self.bot_usecase.bot_repo.create.assert_called_once_with(
            tenant_id=tenant_id, group_id=group_id, bot=bot_for_create
        )

    def test_create_bot_by_template(self, setup, mock_get_feature_flag):
        """テンプレートからボット作成テスト"""
        mock_get_feature_flag.return_value = True
        tenant_id = tenant_domain.Id(value=1)
        bot_template_id = bot_template_domain.Id(root=uuid4())
        creator_id = user_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

        bot = bot_domain.Bot(
            id=bot_domain.Id(value=4),
            name=bot_for_create.name,
            group_id=group_id,
            description=bot_for_create.description,
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=bot_for_create.index_name,
            container_name=bot_for_create.container_name,
            approach=bot_for_create.approach,
            pdf_parser=bot_for_create.pdf_parser,
            example_questions=bot_for_create.example_questions,
            search_method=bot_for_create.search_method,
            response_generator_model_family=bot_for_create.response_generator_model_family,
            enable_web_browsing=bot_for_create.enable_web_browsing,
            enable_follow_up_questions=bot_for_create.enable_follow_up_questions,
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_for_create.icon_url,
            icon_color=bot_for_create.icon_color,
            endpoint_id=bot_for_create.endpoint_id,
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=bot_for_create.approach_variables,
        )

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = None
        self.bot_usecase.bot_template_repo.find_by_id.return_value = self.dummy_bot_template(
            id=bot_template_id, is_public=True
        )
        self.bot_usecase.common_prompt_template_repo.find_by_bot_template_id.return_value = (
            self.dummy_bot_prompt_templates()
        )
        self.bot_usecase.common_document_template_repo.find_by_bot_template_id.return_value = (
            self.dummy_bot_document_templates()
        )
        self.bot_usecase.bot_repo.create.return_value = bot
        self.bot_usecase.document_folder_repo.find_root_document_folder_by_bot_id.side_effect = NotFound("Not Found")
        self.bot_usecase.cognitive_search_service = Mock()
        self.bot_usecase.blob_storage_service = Mock()
        self.bot_usecase.queue_storage_service = Mock()

        # 実際の呼び出し
        mock_uuid = uuid4()
        with patch("uuid.uuid4", return_value=mock_uuid):
            self.bot_usecase.create_bot(
                tenant_id=tenant_id,
                group_id=group_id,
                bot_for_create=bot_for_create,
                bot_template_id=bot_template_id,
                creator_id=creator_id,
            )
            self.bot_usecase.bot_repo.create.assert_called_once_with(
                tenant_id=tenant_id,
                group_id=group_id,
                bot=bot_for_create,
            )
        self.bot_usecase.document_folder_repo.create_root_document_folder.assert_called()
        self.bot_usecase.bot_template_repo.find_by_id.assert_called_once_with(bot_template_id)
        self.bot_usecase.common_prompt_template_repo.find_by_bot_template_id.assert_called_once_with(bot_template_id)
        self.bot_usecase.common_document_template_repo.find_by_bot_template_id.assert_called_once_with(bot_template_id)
        self.bot_usecase.blob_storage_service.copy_blob_from_common_container_to_bot_container.assert_called()
        self.bot_usecase.queue_storage_service.send_messages_to_documents_process_queue.assert_called()

    def test_create_bot_by_template_with_private_template(self, setup, mock_get_feature_flag):
        """テンプレートからボット作成テスト"""
        mock_get_feature_flag.return_value = True
        tenant_id = tenant_domain.Id(value=1)
        bot_template_id = bot_template_domain.Id(root=uuid4())
        creator_id = user_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = None
        self.bot_usecase.bot_template_repo.find_by_id.return_value = self.dummy_bot_template(
            bot_template_id, is_public=False
        )

        # 実際の呼び出し
        mock_uuid = uuid4()
        with pytest.raises(NotFound, match="テンプレートが見つかりません"):
            with patch("uuid.uuid4", return_value=mock_uuid):
                self.bot_usecase.create_bot(
                    tenant_id=tenant_id,
                    group_id=group_id,
                    bot_for_create=bot_for_create,
                    bot_template_id=bot_template_id,
                    creator_id=creator_id,
                )
        self.bot_usecase.bot_template_repo.find_by_id.assert_called_once_with(bot_template_id)

    def test_create_bot_with_existing_name(self, setup, mock_get_feature_flag):
        """同名のボットが存在する場合のボット作成テスト"""
        tenant_id = tenant_domain.Id(value=1)
        creator_id = user_domain.Id(value=1)

        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

        existing_bot = self.dummy_bot(
            bot_id=bot_domain.Id(value=1),
        )

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = existing_bot

        with pytest.raises(BadRequest):
            self.bot_usecase.create_bot(
                tenant_id=tenant_id,
                group_id=existing_bot.group_id,
                bot_for_create=bot_for_create,
                bot_template_id=None,
                creator_id=creator_id,
            )

        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(
            group_id=existing_bot.group_id,
            name=bot_for_create.name,
        )

    def test_create_bot_with_document_intelligence_disabled(self, setup, mock_get_feature_flag):
        """Document Intelligenceが無効の場合のボット作成テスト"""
        tenant_id = tenant_domain.Id(value=1)
        creator_id = user_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        bot_for_create = bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.DOCUMENT_INTELLIGENCE,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

        tenant = tenant_domain.Tenant(
            id=tenant_id,
            name=tenant_domain.Name(value="Test Tenant"),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-alias"),
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-alias"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        self.bot_usecase.tenant_repo.find_by_id.return_value = tenant

        with pytest.raises(BadRequest):
            self.bot_usecase.create_bot(
                tenant_id=tenant_id,
                group_id=group_id,
                bot_for_create=bot_for_create,
                bot_template_id=None,
                creator_id=creator_id,
            )

        self.bot_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)

    def test_update_bot(self, setup):
        """ボット更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        bot_for_update = bot_domain.BotForUpdate(
            name=bot_domain.Name(value="Updated Bot"),
            description=bot_domain.Description(value="This is an updated bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Updated example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

        current_bot = self.dummy_bot(bot_id=bot_id)

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = current_bot
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = None

        with patch.object(bot_domain.Bot, "update", return_value=None) as mock_update:
            self.bot_usecase.update_bot(tenant_id=tenant_id, bot_id=bot_id, bot=bot_for_update)

        mock_update.assert_called_once_with(bot_for_update)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.bot_usecase.bot_repo.update.assert_called_once()

    def test_update_bot_with_existing_name(self, setup):
        """同名のボットが存在する場合のボット更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        bot_for_update = bot_domain.BotForUpdate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is an updated bot."),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Updated example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

        current_bot = self.dummy_bot(bot_id=bot_id)

        self.bot_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = current_bot
        self.bot_usecase.bot_repo.find_by_group_id_and_name.return_value = self.dummy_bot(
            bot_id=bot_domain.Id(value=2)
        )

        with pytest.raises(BadRequest):
            self.bot_usecase.update_bot(tenant_id=tenant_id, bot_id=bot_id, bot=bot_for_update)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(
            group_id=current_bot.group_id,
            name=bot_for_update.name,
        )

    def test_archive_bot(self, setup):
        """ボットアーカイブテスト"""
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        bot = self.dummy_bot(bot_id, approach=bot_domain.Approach.NEOLLM, search_method=bot_domain.SearchMethod.BM25)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.bot_usecase.bot_repo.update.return_value = None

        self.bot_usecase.archive_bot(tenant_id=tenant_id, bot_id=bot_id)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.bot_usecase.bot_repo.update.assert_called_once_with(bot)

    def test_restore_bot(self, setup):
        """ボット復元テスト"""
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        bot = self.dummy_bot(
            bot_id,
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.BM25,
            status=bot_domain.Status.ARCHIVED,
        )

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.bot_usecase.bot_repo.update.return_value = None

        self.bot_usecase.restore_bot(tenant_id=tenant_id, bot_id=bot_id)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.bot_usecase.bot_repo.update.assert_called_once_with(bot)

    def test_delete_bot(self, setup, mock_get_feature_flag):
        """ボット削除テスト"""
        mock_get_feature_flag.return_value = False

        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        bot = self.dummy_bot(bot_id, approach=bot_domain.Approach.NEOLLM, search_method=bot_domain.SearchMethod.BM25)
        tenant = self.dummy_tenant()
        documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test"),
                memo=document_domain.Memo(value="test"),
                file_extension=document_domain.FileExtension("pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10000),
                created_at=document_domain.CreatedAt(value=datetime.now()),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
            )
        ]

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.bot_usecase.tenant_repo.find_by_id.return_value = tenant
        self.bot_usecase.document_repo.find_by_bot_id.return_value = documents
        self.bot_usecase.bot_repo.update.return_value = None
        self.bot_usecase.document_repo.bulk_update.return_value = None
        self.bot_usecase.queue_storage_service.send_message_to_delete_bot_queue.return_value = None

        self.bot_usecase.delete_bot(tenant_id=tenant_id, bot_id=bot_id)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.bot_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.bot_usecase.document_repo.find_by_bot_id.assert_called_once_with(bot_id)
        self.bot_usecase.bot_repo.update.assert_called_once_with(bot)
        self.bot_usecase.document_repo.bulk_update.assert_called_once_with(documents)
        self.bot_usecase.queue_storage_service.send_message_to_delete_bot_queue.assert_called_once_with(
            tenant_id, bot_id
        )

    def test_find_prompt_templates_by_bot_id(self, setup):
        """ボットIDによる質問例取得テスト"""
        bot_id = bot_domain.Id(value=1)
        want = [
            bot_prompt_template_domain.PromptTemplate(
                id=bot_prompt_template_domain.Id(root=UUID("00000000-0000-0000-0000-000000000001")),
                title=bot_prompt_template_domain.Title(root="Test Prompt Template"),
                description=bot_prompt_template_domain.Description(root="This is a test prompt template."),
                prompt=bot_prompt_template_domain.Prompt(root="This is a test prompt."),
            ),
            bot_prompt_template_domain.PromptTemplate(
                id=bot_prompt_template_domain.Id(root=UUID("00000000-0000-0000-0000-000000000002")),
                title=bot_prompt_template_domain.Title(root="Test Prompt Template 2"),
                description=bot_prompt_template_domain.Description(root="This is a test prompt template 2."),
                prompt=bot_prompt_template_domain.Prompt(root="This is a test prompt 2."),
            ),
        ]

        self.bot_usecase.bot_repo.find_prompt_templates_by_bot_id.return_value = want

        got = self.bot_usecase.find_prompt_templates_by_bot_id(bot_id=bot_id)

        assert got == want
        self.bot_usecase.bot_repo.find_prompt_templates_by_bot_id.assert_called_once_with(bot_id=bot_id)

    def create_prompt_template(self, setup):
        bot_id = bot_domain.Id(value=1)
        prompt_template_for_create = bot_prompt_template_domain.PromptTemplateForCreate(
            title=bot_prompt_template_domain.Title(root="Test Prompt Template"),
            description=bot_prompt_template_domain.Description(root="This is a test prompt template."),
            prompt=bot_prompt_template_domain.Prompt(root="This is a test prompt."),
        )

        want = bot_prompt_template_domain.PromptTemplate(
            id=prompt_template_for_create.id,
            title=bot_prompt_template_domain.Title(root="Test Prompt Template"),
            description=bot_prompt_template_domain.Description(root="This is a test prompt template."),
            prompt=bot_prompt_template_domain.Prompt(root="This is a test prompt."),
        )

        self.bot_usecase.bot_repo.create_prompt_template.return_value = want

        got = self.bot_usecase.create_prompt_template(bot_id=bot_id, prompt_template=prompt_template_for_create)

        assert got == want

    def test_update_prompt_template(self, setup):
        bot_id = bot_domain.Id(value=1)
        id = bot_prompt_template_domain.Id(
            root=UUID("00000000-0000-0000-0000-000000000001"),
        )
        title = bot_prompt_template_domain.Title(root="Updated Prompt Template")
        description = bot_prompt_template_domain.Description(root="This is an updated prompt template.")
        prompt = bot_prompt_template_domain.Prompt(root="This is an updated prompt.")

        prompt_template_for_update = bot_prompt_template_domain.PromptTemplateForUpdate(
            id=id,
            title=title,
            description=description,
            prompt=prompt,
        )

        prompt_template = bot_prompt_template_domain.PromptTemplate(
            id=id,
            title=title,
            description=description,
            prompt=prompt,
        )

        self.bot_usecase.bot_repo.find_prompt_template_by_id_and_bot_id.return_value = prompt_template

        self.bot_usecase.bot_repo.update_prompt_template.return_value = None

        got = self.bot_usecase.update_prompt_template(bot_id=bot_id, prompt_template=prompt_template_for_update)

        self.bot_usecase.bot_repo.find_prompt_template_by_id_and_bot_id.assert_called_once_with(
            bot_id=bot_id, bot_prompt_template_id=prompt_template_for_update.id
        )
        self.bot_usecase.bot_repo.update_prompt_template.assert_called_once_with(
            bot_id=bot_id, prompt_template=prompt_template
        )

        assert got is None

    def test_delete_prompt_template(self, setup):
        bot_id = bot_domain.Id(value=1)
        bot_prompt_template_ids = [
            bot_prompt_template_domain.Id(root=UUID("00000000-0000-0000-0000-000000000001")),
            bot_prompt_template_domain.Id(root=UUID("00000000-0000-0000-0000-000000000002")),
        ]
        self.bot_usecase.bot_repo.delete_prompt_templates.return_value = None
        self.bot_usecase.delete_prompt_templates(bot_id=bot_id, bot_prompt_template_ids=bot_prompt_template_ids)

    def test_upload_bot_icon(self, setup):
        """アイコンのアップロードテスト"""
        bot_id = bot_domain.Id(value=1)
        alias = tenant_domain.Alias(root="test-tenant")
        icon_file = b"dummy_icon_file"
        input = UploadBotIconInput(file=icon_file, extension=IconFileExtension.PNG)
        expected_icon_url = IconUrl(root="https://example.com/test-tenant/icon.png")

        bot = self.dummy_bot(bot_id=bot_id)
        old_icon_url = bot.icon_url
        self.bot_usecase.bot_repo.find_by_id.return_value = bot
        self.bot_usecase.bot_repo.update.return_value = None
        self.bot_usecase.blob_storage_service.upload_bot_icon.return_value = expected_icon_url
        self.bot_usecase.blob_storage_service.delete_bot_icon.return_value = None

        mock_uuid = uuid.uuid4()
        with patch("uuid.uuid4", return_value=mock_uuid):
            self.bot_usecase.upload_bot_icon(alias, bot_id, input)

        self.bot_usecase.blob_storage_service.upload_bot_icon.assert_called_once_with(
            f"{alias.root}/{mock_uuid}.png",
            icon_file,
        )
        self.bot_usecase.bot_repo.update.assert_called_once_with(bot)
        self.bot_usecase.blob_storage_service.delete_bot_icon.assert_called_once_with(alias, old_icon_url)

    def test_delete_bot_icon(self, setup):
        """アイコンの削除テスト"""
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id=bot_id)
        alias = tenant_domain.Alias(root="test-tenant")
        old_icon_url = bot.icon_url
        self.bot_usecase.bot_repo.find_by_id.return_value = bot
        self.bot_usecase.bot_repo.update.return_value = None
        self.bot_usecase.blob_storage_service.delete_bot_icon.return_value = None

        self.bot_usecase.delete_bot_icon(alias, bot_id)

        self.bot_usecase.blob_storage_service.delete_bot_icon.assert_called_once_with(alias, old_icon_url)
        self.bot_usecase.bot_repo.update.assert_called_once_with(bot)

    def test_add_liked_bot(self, setup):
        """お気に入りボット追加テスト"""
        bot_id = bot_domain.Id(value=2)
        bot = self.dummy_assistant(bot_id=bot_id)
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        input = UpdateLikedBotInput(
            tenant_id=tenant_id,
            bot_id=bot_id,
            user_id=user_id,
            is_liked=bot_domain.IsLiked(root=True),
        )
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.bot_usecase.bot_repo.find_liked_bot_ids_by_user_id.return_value = []
        self.bot_usecase.bot_repo.add_liked_bot.return_value = None

        self.bot_usecase.update_liked_bot(input=input)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_liked_bot_ids_by_user_id.assert_called_once_with(user_id=user_id)
        self.bot_usecase.bot_repo.add_liked_bot.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, user_id=user_id
        )

    def test_remove_liked_bot(self, setup):
        """お気に入りボット削除テスト"""
        bot_id = bot_domain.Id(value=2)
        bot = self.dummy_assistant(bot_id=bot_id)
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        input = UpdateLikedBotInput(
            tenant_id=tenant_id,
            bot_id=bot_id,
            user_id=user_id,
            is_liked=bot_domain.IsLiked(root=False),
        )
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.bot_usecase.bot_repo.find_liked_bot_ids_by_user_id.return_value = [bot_id]
        self.bot_usecase.bot_repo.remove_liked_bot.return_value = None

        self.bot_usecase.update_liked_bot(input=input)

        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_liked_bot_ids_by_user_id.assert_called_once_with(user_id=user_id)
        self.bot_usecase.bot_repo.remove_liked_bot.assert_called_once_with(bot_id=bot_id, user_id=user_id)

    def test_find_by_group_id(self, setup):
        """グループIDによるボットの取得テスト"""
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id=bot_id)
        group_id = group_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        bots = [bot]
        self.bot_usecase.bot_repo.find_by_group_id.return_value = bots

        got = self.bot_usecase.find_by_group_id(
            tenant_id=tenant_id, group_id=group_id, statuses=[bot_domain.Status.ACTIVE]
        )

        assert got == bots
        self.bot_usecase.bot_repo.find_by_group_id.assert_called_once_with(
            tenant_id=tenant_id, group_id=group_id, statuses=[bot_domain.Status.ACTIVE]
        )

    def test_update_bot_group(self, setup):
        """ボットのグループ変更テスト"""
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id=bot_id)
        group_id = group_domain.Id(value=1)
        group = self.dummy_group(group_id=group_id)
        tenant_id = tenant_domain.Id(value=1)
        self.bot_usecase.group_repo.get_group_by_id_and_tenant_id = Mock(return_value=group)
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.bot_usecase.bot_repo.find_by_group_id_and_name = Mock(side_effect=NotFound("Not Found"))
        self.bot_usecase.bot_repo.update_bot_group = Mock(return_value=None)

        self.bot_usecase.update_bot_group(bot_id=bot_id, group_id=group_id, tenant_id=tenant_id)

        self.bot_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(
            group_id=group_id, tenant_id=tenant_id
        )
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(group_id=group_id, name=bot.name)
        self.bot_usecase.bot_repo.update_bot_group.assert_called_once_with(bot_id=bot_id, group_id=group_id)

    def test_update_bot_group_with_existing_name(self, setup):
        """同名のボットが存在する場合のボットのグループ変更テスト"""
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id=bot_id)
        group_id = group_domain.Id(value=1)
        group = self.dummy_group(group_id=group_id)
        tenant_id = tenant_domain.Id(value=1)
        self.bot_usecase.group_repo.get_group_by_id_and_tenant_id = Mock(return_value=group)
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.bot_usecase.bot_repo.find_by_group_id_and_name = Mock(
            return_value=self.dummy_bot(bot_id=bot_domain.Id(value=2))
        )

        with pytest.raises(BadRequest):
            self.bot_usecase.update_bot_group(bot_id=bot_id, group_id=group_id, tenant_id=tenant_id)

        self.bot_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(
            group_id=group_id, tenant_id=tenant_id
        )
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(group_id=group_id, name=bot.name)
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(group_id=group_id, name=bot.name)
        self.bot_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.bot_usecase.bot_repo.find_by_group_id_and_name.assert_called_once_with(group_id=group_id, name=bot.name)
