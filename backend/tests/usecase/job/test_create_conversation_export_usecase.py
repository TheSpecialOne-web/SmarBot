from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from api.domain.models import (
    bot as bot_domain,
    conversation_export as conversation_export_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.conversation.conversation_turn import conversation_turn as conversation_turn_domain
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.libs.csv import convert_dict_list_to_csv_string
from api.usecase.job.create_conversation_export import CreateConversationExportUseCase


class TestCreateConversationExportUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo_mock = Mock()
        self.conversation_mock = Mock()
        self.conversation_repo_mock = Mock()
        self.tenant_repo_mock = Mock()
        self.user_repo_mock = Mock()
        self.blob_storage_service_mock = Mock()
        self.document_folder_repo = Mock()
        self.use_case = CreateConversationExportUseCase(
            bot_repo=self.bot_repo_mock,
            conversation_repo=self.conversation_mock,
            conversation_export_repo=self.conversation_repo_mock,
            tenant_repo=self.tenant_repo_mock,
            user_repo=self.user_repo_mock,
            blob_storage_service=self.blob_storage_service_mock,
            document_folder_repo=self.document_folder_repo,
        )

    def dummy_tenant(
        self,
        id: tenant_domain.Id,
    ):
        return tenant_domain.Tenant(
            id=id,
            name=tenant_domain.Name(value="test-tenant"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-alias"),
            container_name=ContainerName(root="test-alias"),
            alias=tenant_domain.Alias(root="test-alias"),
            status=tenant_domain.Status.SUBSCRIBED,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit(
                free_user_seat=50,
                additional_user_seat=0,
                free_token=500000,
                additional_token=0,
                free_storage=1000000,
                additional_storage=0,
                document_intelligence_page=0,
            ),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_user(self, user_id: user_domain.Id):
        return user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test_user"),
            email=user_domain.Email(value="test@test.user"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

    def dummy_bot(self, bot_id: bot_domain.Id):
        return bot_domain.Bot(
            id=bot_id,
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
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def test_create_conversation_export(self, setup):
        # input
        dummy_tenant = self.dummy_tenant(id=tenant_domain.Id(value=1))
        dummy_user = self.dummy_user(user_id=user_domain.Id(value=1))
        dummy_bot = self.dummy_bot(bot_id=bot_domain.Id(value=1))
        conversation_turns: list[conversation_turn_domain.ConversationTurnWithUserAndBotAndGroup] = []
        conversation_export = conversation_export_domain.ConversationExport(
            id=conversation_export_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001")),
            status=conversation_export_domain.Status.PROCESSING,
            user_id=dummy_user.id,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.now()),
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.now()),
            target_bot_id=None,
            target_user_id=None,
        )
        csv = [conversation_turn.to_dict() for conversation_turn in conversation_turns]
        csv_bytes = convert_dict_list_to_csv_string(data=csv).getvalue().encode("utf-8")

        # mock
        self.use_case.conversation_export_repo.find_by_id = Mock(return_value=conversation_export)
        self.use_case.tenant_repo.find_by_id = Mock(return_value=dummy_tenant)
        if conversation_export.target_user_id is None:
            self.use_case.user_repo.find_by_tenant_id = Mock(return_value=[dummy_user])
        if conversation_export.target_bot_id is None:
            self.use_case.bot_repo.find_all_by_tenant_id = Mock(return_value=[dummy_bot])
        self.use_case.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date_v2 = Mock(
            return_value=conversation_turns
        )
        self.use_case.blob_storage_service.upload_conversation_export_csv = Mock()
        self.use_case.conversation_export_repo.update = Mock()
        self.use_case._initialize_column_order = Mock(return_value=[])

        # run
        self.use_case.create_conversation_export(
            tenant_id=dummy_tenant.id,
            conversation_export_id=conversation_export.id,
        )

        # assert
        self.use_case.conversation_export_repo.find_by_id.assert_called_once_with(
            tenant_id=dummy_tenant.id, id=conversation_export.id
        )
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(dummy_tenant.id)
        if conversation_export.target_user_id is None:
            self.use_case.user_repo.find_by_tenant_id.assert_called_once_with(
                tenant_id=dummy_tenant.id, include_deleted=True
            )
        if conversation_export.target_bot_id is None:
            self.use_case.bot_repo.find_all_by_tenant_id.assert_called_once_with(
                tenant_id=dummy_tenant.id, include_deleted=True
            )
        self.use_case.blob_storage_service.upload_conversation_export_csv.assert_called_once_with(
            container_name=dummy_tenant.container_name,
            blob_path=conversation_export.blob_path,
            csv=csv_bytes,
        )

        conversation_export.update_status_to_active()
        self.use_case.conversation_export_repo.update.assert_called_once_with(conversation_export)
        self.use_case._initialize_column_order.assert_called()

    def test_initialize_column_order(self, setup):
        # Given
        sorted_columns = [
            "ユーザー",
            "基盤モデル/アシスタント",
            "入力",
            "出力",
            "会話日時",
            "回答生成モデル",
            "総トークン数",
            "評価",
            "コメント",
            "ドキュメント参照元1",
            "ドキュメント参照元2",
            "ドキュメント参照元3",
            "所属グループ1",
            "所属グループ2",
            "所属グループ3",
            "FAQ参照元_質問1",
            "FAQ参照元_回答1",
            "FAQ参照元_質問2",
            "FAQ参照元_回答2",
            "FAQ参照元_質問3",
            "FAQ参照元_回答3",
            "Web参照元_名前1",
            "Web参照元_url1",
            "Web参照元_名前2",
            "Web参照元_url2",
            "Web参照元_名前3",
            "Web参照元_url3",
            "添付ファイル1",
            "添付ファイル2",
            "添付ファイル3",
        ]
        initial_data = [
            {
                "ユーザー": "Neo AI",
                "基盤モデル/アシスタント": "Neo AI",
                "入力": "Hello",
                "出力": "I'm here to help!",
                "会話日時": datetime.now(timezone.utc).isoformat(),
                "回答生成モデル": "GPT",
                "総トークン数": 100,
                "評価": "good",
                "コメント": "good",
                "所属グループ1": "Group 1",
                "所属グループ2": "Group 2",
                "ドキュメント参照元1": "/test/test.pdf",
                "FAQ参照元_質問1": "test",
                "FAQ参照元_回答1": "test",
                "Web参照元_名前1": "Neo AI",
                "Web参照元_url1": "https://www.test-web-url.com/",
                "添付ファイル1": "test.pdf",
                "添付ファイル2": "test.pdf",
            },
            {
                "ユーザー名": "Neo AI",
                "基盤モデル/アシスタント": "Neo AI",
                "入力": "Hello",
                "出力": "I'm here to help!",
                "会話日時": datetime.now(timezone.utc).isoformat(),
                "回答生成モデル": "GPT",
                "総トークン数": 100,
                "評価": "good",
                "コメント": "good",
                "所属グループ1": "Group 1",
                "所属グループ2": "Group 2",
                "所属グループ3": "Group 3",
                "ドキュメント参照元1": "/test1/test.pdf",
                "ドキュメント参照元2": "/test2/test.pdf",
                "ドキュメント参照元3": "/test3/test.pdf",
                "FAQ参照元_質問1": "test",
                "FAQ参照元_回答1": "test",
                "FAQ参照元_質問2": "test",
                "FAQ参照元_回答2": "test",
                "FAQ参照元_質問3": "test",
                "FAQ参照元_回答3": "test",
                "Web参照元_名前1": "test",
                "Web参照元_url1": "https://www.test1-web-url.com/",
                "Web参照元_名前2": "test",
                "Web参照元_url2": "https://www.test2-web-url.com/",
                "Web参照元_名前3": "test",
                "Web参照元_url3": "https://www.test3-web-url.com/",
                "添付ファイル1": "test1.pdf",
                "添付ファイル2": "test2.pdf",
                "添付ファイル3": "test3.pdf",
            },
        ]

        # Call the method
        found_columns = self.use_case._initialize_column_order(data=initial_data)

        # Assertions
        assert sorted_columns == found_columns
