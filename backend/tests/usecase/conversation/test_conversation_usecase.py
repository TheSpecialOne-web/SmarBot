from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    conversation as conversation_domain,
    conversation_export as conversation_export_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    term as term_domain,
    token as token_domain,
    user as user_domain,
)
from api.domain.models.bot.approach_variable import (
    ApproachVariable,
    Name as ApproachVariableName,
    Value as ApproachVariableValue,
)
from api.domain.models.conversation import (
    conversation_data_point as conversation_data_point_domain,
    conversation_turn as conversation_turn_domain,
)
from api.domain.models.conversation.validation import SensitiveContent, SensitiveContentType, Validation
from api.domain.models.data_point import BlobPath, ChunkName, CiteNumber, Content, DataPoint, PageNumber, Type, Url
from api.domain.models.llm import AllowForeignRegion, ModelName
from api.domain.models.llm.model import ModelFamily, get_lightweight_model_orders
from api.domain.models.query import Queries
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.token import Token, TokenCount
from api.domain.services.llm.llm import QueryGeneratorOutput, ResponseGeneratorOutputToken
from api.usecase.conversation import ConversationUseCase
from api.usecase.conversation.conversation import (
    FOLLOW_UP_QUESTION_TOKEN,
    IMAGE_GENERATOR_TOKEN,
    QUERY_GENERATOR_TOKEN,
    RESPONSE_GENERATOR_TOKEN,
    ConversationAttachment,
    CreateOrUpdateConversationTurnFeedbackCommentInput,
    UpdateConversationEvaluationInput,
    UpdateConversationInput,
)
from api.usecase.conversation.types import (
    ConversationOutputAnswer,
    ConversationOutputDataPoints,
    ConversationOutputQuery,
    CreateConversationInput,
    GetConversationsByUserIdInput,
    Limit,
    Offset,
    PreviewConversationInput,
)


class TestConversationUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.bot_repo = Mock()
        self.document_folder_repo = Mock()
        self.document_repo = Mock()
        self.term_repo = Mock()
        self.attachment_repo = Mock()
        self.conversation_repo = Mock()
        self.conversation_export_repo = Mock()
        self.metering_repo = Mock()
        self.user_repo = Mock()
        self.blob_storage_service = Mock()
        self.document_intelligence_service = Mock()
        self.ai_vision_service = Mock()
        self.llm_service = Mock()
        self.cognitive_search_service = Mock()
        self.bing_search_service = Mock()
        self.web_scraping_service = Mock()
        self.queue_storage_service = Mock()
        self.conversation_usecase = ConversationUseCase(
            tenant_repo=self.tenant_repo,
            bot_repo=self.bot_repo,
            document_folder_repo=self.document_folder_repo,
            document_repo=self.document_repo,
            term_repo=self.term_repo,
            attachment_repo=self.attachment_repo,
            conversation_repo=self.conversation_repo,
            conversation_export_repo=self.conversation_export_repo,
            metering_repo=self.metering_repo,
            user_repo=self.user_repo,
            blob_storage_service=self.blob_storage_service,
            document_intelligence_service=self.document_intelligence_service,
            ai_vision_service=self.ai_vision_service,
            llm_service=self.llm_service,
            cognitive_search_service=self.cognitive_search_service,
            bing_search_service=self.bing_search_service,
            web_scraping_service=self.web_scraping_service,
            queue_storage_service=self.queue_storage_service,
        )

    @pytest.fixture
    def mock_create_conversation_id(self, monkeypatch):
        mock_create_conversation_id = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440000"))
        monkeypatch.setattr(
            "api.domain.models.conversation.id.uuid4",
            mock_create_conversation_id,
        )
        return mock_create_conversation_id

    @pytest.fixture
    def mock_create_conversation_turn_id(self, monkeypatch):
        mock_create_conversation_turn_id = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440001"))
        monkeypatch.setattr(
            "api.domain.models.conversation.conversation_turn.id.uuid4", mock_create_conversation_turn_id
        )
        return mock_create_conversation_turn_id

    @pytest.fixture
    def mock_create_conversation_data_point_id(self, monkeypatch):
        mock_create_conversation_data_point_id = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440002"))
        monkeypatch.setattr(
            "api.domain.models.conversation.conversation_data_point.id.uuid4", mock_create_conversation_data_point_id
        )
        return mock_create_conversation_data_point_id

    @pytest.fixture
    def mock_calculate_token_count(self, monkeypatch):
        mock_calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        monkeypatch.setattr(
            "api.usecase.conversation.conversation.ConversationUseCase._calculate_token_count",
            mock_calculate_token_count,
        )
        return mock_calculate_token_count

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock(return_value=False)
        monkeypatch.setattr("api.usecase.conversation.conversation.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def dummy_tenant(
        self,
        id: tenant_domain.Id,
        name: tenant_domain.Name,
        index_name: IndexName,
        container_name: ContainerName,
    ):
        return tenant_domain.Tenant(
            id=id,
            name=name,
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=index_name,
            container_name=container_name,
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

    def dummy_bot_for_web_browsing(self, bot_id: bot_domain.Id):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot 2"),
            description=bot_domain.Description(value="This is a test bot 2."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_data_points(self) -> list[DataPoint]:
        return [
            DataPoint(
                document_id=None,
                chunk_name=ChunkName(root="chunk1"),
                page_number=PageNumber(root=10),
                blob_path=BlobPath(root="file1.pdf"),
                content=Content(root="内容1"),
                type=Type.INTERNAL,
                url=Url(root=""),
                cite_number=CiteNumber(root=1),
            ),
            DataPoint(
                document_id=None,
                chunk_name=ChunkName(root="chunk2"),
                page_number=PageNumber(root=20),
                blob_path=BlobPath(root="file2.pdf"),
                content=Content(root="内容2"),
                type=Type.INTERNAL,
                url=Url(root=""),
                cite_number=CiteNumber(root=2),
            ),
        ]

    def dummy_conversation_data_points(
        self, conversation_turn_id: Mock
    ) -> list[conversation_data_point_domain.ConversationDataPoint]:
        data_points = self.dummy_data_points()
        return [
            conversation_data_point_domain.ConversationDataPoint(
                **data_point.model_dump(),
                id=conversation_data_point_domain.Id(root=uuid4()),
                turn_id=conversation_turn_id.return_value,
            )
            for data_point in data_points
        ]

    def dummy_document_folder_with_descentants(self):
        return document_folder_domain.DocumentFolderWithDescendants(
            id=document_folder_domain.Id(root=uuid4()),
            name=document_folder_domain.Name(root="dummy_folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
            descendant_folders=[
                document_folder_domain.DocumentFolder(
                    id=document_folder_domain.Id(root=uuid4()),
                    name=document_folder_domain.Name(root="descendant_folder1"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
                ),
                document_folder_domain.DocumentFolder(
                    id=document_folder_domain.Id(root=uuid4()),
                    name=document_folder_domain.Name(root="descendant_folder2"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
                ),
            ],
        )

    def test_create_search_filter(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        dummy_bot = self.dummy_bot(bot_id)
        dummy_document_folder_with_descentants = self.dummy_document_folder_with_descentants()

        # Expected
        expected_output = f"bot_id eq {dummy_bot.id.value} and search.in(document_folder_id, '{dummy_document_folder_with_descentants.id.root},{dummy_document_folder_with_descentants.descendant_folders[0].id.root},{dummy_document_folder_with_descentants.descendant_folders[1].id.root}')"

        # Execute
        output = self.conversation_usecase._create_search_filter(
            dummy_bot,
            dummy_document_folder_with_descentants,
        )

        # Test
        assert output == expected_output

    def test_get_conversations_for_download(
        self,
        setup,
    ):
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 想定される戻り値の設定
        want = conversation_domain.ConversationWithUserAndBot(
            id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
            title=conversation_domain.Title(root="title"),
            user_id=user_id,
            bot_id=bot_id,
            user_name=user_domain.Name(value="test_user"),
            bot_name=bot_domain.Name(value="test_bot"),
        )

        self.user_repo.find_by_tenant_id.return_value = [
            Mock(id=user_domain.Id(value=1)),
        ]

        # ボットリポジトリのモック設定
        self.bot_repo.find_all_by_tenant_id.return_value = [Mock(id=bot_domain.Id(value=1))]

        self.conversation_usecase.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date.return_value = [
            want
        ]

        # テスト対象メソッドの実行
        got = self.conversation_usecase.get_conversations_for_download(
            bot_id=bot_id,
            tenant_id=tenant_id,
            user_id=user_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        # 結果の検証
        assert got == [want]
        self.conversation_usecase.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date.assert_called_once_with(
            user_ids=[user_id],
            bot_ids=[bot_id],
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

    def test_create_conversation_export(self, setup):
        # input
        tenant_id = tenant_domain.Id(value=1)
        dummy_user = self.dummy_user(user_id=user_domain.Id(value=1))
        dummy_bot = self.dummy_bot(bot_id=bot_domain.Id(value=1))
        conversation_export_for_create = conversation_export_domain.ConversationExportForCreate(
            user_id=dummy_user.id,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.now()),
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.now()),
            target_bot_id=dummy_bot.id,
            target_user_id=dummy_user.id,
        )
        conversation_export = conversation_export_domain.ConversationExport(
            id=conversation_export_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001")),
            status=conversation_export_domain.Status.PROCESSING,
            user_id=conversation_export_for_create.user_id,
            start_date_time=conversation_export_for_create.start_date_time,
            end_date_time=conversation_export_for_create.end_date_time,
            target_bot_id=conversation_export_for_create.target_bot_id,
            target_user_id=conversation_export_for_create.target_user_id,
        )

        # mock
        self.conversation_usecase.user_repo.find_by_tenant_id = Mock(return_value=[dummy_user])
        self.conversation_usecase.bot_repo.find_all_by_tenant_id = Mock(return_value=[dummy_bot])
        self.conversation_usecase.conversation_export_repo.create = Mock(return_value=conversation_export)
        self.conversation_usecase.queue_storage_service.send_message_to_create_conversation_export_queue = Mock()

        # run
        self.conversation_usecase.create_conversation_export(
            tenant_id=tenant_id,
            conversation_export_for_create=conversation_export_for_create,
        )

        # assert
        self.conversation_usecase.user_repo.find_by_tenant_id.assert_called_once_with(
            tenant_id=tenant_id, include_deleted=True
        )
        self.conversation_usecase.bot_repo.find_all_by_tenant_id.assert_called_once_with(
            tenant_id=tenant_id, include_deleted=True
        )
        self.conversation_usecase.conversation_export_repo.create.assert_called_once_with(
            conversation_export_for_create
        )
        self.conversation_usecase.queue_storage_service.send_message_to_create_conversation_export_queue.assert_called_once_with(
            tenant_id=tenant_id,
            conversation_export_id=conversation_export.id,
        )

    def test_get_conversation_export_with_user(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        dummy_user = self.dummy_user(user_id=user_domain.Id(value=1))
        conversation_export_with_user = [
            conversation_export_domain.ConversationExportWithUser(
                id=conversation_export_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                user=dummy_user,
                status=conversation_export_domain.Status.PROCESSING,
                created_at=conversation_export_domain.CreateAt(root=datetime.now()),
            )
        ]
        self.conversation_usecase.conversation_export_repo.find_with_user_by_tenant_id.return_value = (
            conversation_export_with_user
        )

        result = self.conversation_usecase.get_conversation_export_with_user(tenant_id)

        assert result == conversation_export_with_user
        self.conversation_usecase.conversation_export_repo.find_with_user_by_tenant_id.assert_called_once_with(
            tenant_id
        )

    def test_create_conversation_title(self, setup):
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant"),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
        )
        bot_id = bot_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        title = conversation_domain.Title(root="test_title")

        self.conversation_usecase.conversation_repo.find_turns_by_id_and_bot_id.return_value = (
            conversation_turn_domain.Turn(
                user=conversation_turn_domain.Message(root="user input"),
                bot=conversation_turn_domain.Message(root="bot output"),
            )
        )
        self.conversation_usecase.llm_service.generate_conversation_title.return_value = conversation_domain.Title(
            root="test_title"
        )

        got = self.conversation_usecase.create_conversation_title(tenant, bot_id, conversation_id)

        assert got == title

    def test_get_conversations_by_user_id(self, setup, mock_create_conversation_id):
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        title = conversation_domain.Title(root="test_title")

        input = GetConversationsByUserIdInput(
            user_id=user_id,
            offset=Offset(root=0),
            limit=Limit(root=10),
            tenant_id=tenant_id,
        )

        want = [
            conversation_domain.Conversation(
                id=conversation_id,
                title=title,
                user_id=user_id,
                bot_id=bot_id,
            )
        ]

        self.conversation_usecase.conversation_repo.find_by_user_id.return_value = [
            conversation_domain.Conversation(
                id=conversation_id,
                title=title,
                user_id=user_id,
                bot_id=bot_id,
            )
        ]

        got = self.conversation_usecase.get_conversations_by_user_id(input)
        # 結果の検証
        assert got == want
        # 一回の呼び出しであることを確認
        self.conversation_usecase.conversation_repo.find_by_user_id.assert_called_once_with(
            tenant_id,
            user_id,
            0,
            10,
        )

    def test_get_conversation_by_id(self, setup, mock_create_conversation_id):
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        # tenant_id = tenant_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        new_conversation_data_point_id = conversation_data_point_domain.Id(
            root=UUID("550e8400-e29b-41d4-a716-446655440002")
        )
        attachment_id = attachment_domain.Id(root=uuid4())

        title = conversation_domain.Title(root="test_title")

        dummy_data_points = self.dummy_data_points()
        dummy_answer = "ダミーの回答"
        dummy_query_input_token = 100
        dummy_query_output_token = 150
        dummy_response_input_token = 200
        dummy_response_output_token = 250
        dummy_query = ["クエリ1", "クエリ2"]

        want = conversation_domain.ConversationWithAttachments(
            id=conversation_id,
            title=title,
            user_id=user_id,
            bot_id=bot_id,
            conversation_turns=[
                conversation_turn_domain.ConversationTurnWithAttachments(
                    id=conversation_turn_id,
                    conversation_id=conversation_id,
                    user_input=conversation_turn_domain.UserInput(root="sample question"),
                    bot_output=conversation_turn_domain.BotOutput(root=dummy_answer),
                    queries=[conversation_turn_domain.Query(root=query) for query in dummy_query],
                    token_set=token_domain.TokenSet(
                        query_input_token=token_domain.Token(root=dummy_query_input_token),
                        query_output_token=token_domain.Token(root=dummy_query_output_token),
                        response_input_token=token_domain.Token(root=dummy_response_input_token),
                        response_output_token=token_domain.Token(root=dummy_response_output_token),
                    ),
                    token_count=token_domain.TokenCount(root=100.0),
                    query_generator_model=ModelName.GPT_35_TURBO,
                    response_generator_model=ModelName.GPT_35_TURBO,
                    evaluation=None,
                    comment=None,
                    created_at=conversation_turn_domain.CreatedAt(root=datetime.utcnow()),
                    data_points=[
                        conversation_data_point_domain.ConversationDataPoint(
                            id=new_conversation_data_point_id,
                            turn_id=conversation_turn_id,
                            document_id=None,
                            cite_number=data_point.cite_number,
                            chunk_name=data_point.chunk_name,
                            page_number=data_point.page_number,
                            blob_path=data_point.blob_path,
                            content=data_point.content,
                            type=data_point.type,
                            url=data_point.url,
                        )
                        for data_point in dummy_data_points
                    ],
                    attachments=[
                        attachment_domain.Attachment(
                            id=attachment_id,
                            name=attachment_domain.Name(root="test-attachment"),
                            created_at=attachment_domain.CreatedAt(root=datetime.utcnow()),
                            file_extension=attachment_domain.FileExtension.PDF,
                            is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
                        )
                    ],
                )
            ],
        )

        self.conversation_usecase.conversation_repo.find_by_id.return_value = want

        got = self.conversation_usecase.get_conversation_by_id(conversation_id, user_id)
        # 結果の検証
        assert got == want
        # 一回の呼び出しであることを確認
        self.conversation_usecase.conversation_repo.find_by_id.assert_called_once_with(
            conversation_id,
            user_id,
        )

    def test_update_conversation(self, setup, mock_create_conversation_id):
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        title = conversation_domain.Title(root="test_title")

        input = UpdateConversationInput(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            is_archived=None,
        )

        self.conversation_usecase.conversation_repo.update_conversation.return_value = (
            conversation_domain.Conversation(
                id=conversation_id,
                title=title,
                user_id=user_id,
                bot_id=bot_id,
            )
        )
        self.conversation_usecase.update_conversation(input)

        self.conversation_usecase.conversation_repo.update_conversation.assert_called_once_with(
            id=input.conversation_id,
            user_id=input.user_id,
            title=input.title,
            is_archived=input.is_archived,
        )

    def test_update_evaluation(self, setup, mock_create_conversation_id):
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        evaluation = "good"

        input = UpdateConversationEvaluationInput(
            conversation_id=conversation_id,
            conversation_turn_id=conversation_turn_id,
            evaluation=conversation_turn_domain.Evaluation(evaluation),
        )

        self.conversation_usecase.update_evaluation(input)

        self.conversation_usecase.conversation_repo.update_evaluation.assert_called_once_with(
            id=input.conversation_id,
            turn_id=input.conversation_turn_id,
            evaluation=input.evaluation,
        )

    def test_save_comment(self, setup, mock_create_conversation_id):
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        comment = "good"

        input = CreateOrUpdateConversationTurnFeedbackCommentInput(
            conversation_id=conversation_id,
            conversation_turn_id=conversation_turn_id,
            comment=conversation_turn_domain.Comment(comment),
        )

        self.conversation_usecase.conversation_repo.save_comment = Mock(return_value=None)

        self.conversation_usecase.save_comment(input)

        self.conversation_usecase.conversation_repo.save_comment.assert_called_once_with(
            conversation_id=input.conversation_id,
            conversation_turn_id=input.conversation_turn_id,
            comment=input.comment,
        )

    def test_validate_conversation(self, setup, mock_create_conversation_id):
        question1 = conversation_turn_domain.UserInput(root="電話番号は000-0000-0000です")
        question2 = conversation_turn_domain.UserInput(root="メールアドレスはaaaa@gmail.comです")
        question3 = conversation_turn_domain.UserInput(root="郵便番号は000-0000です")
        question4 = conversation_turn_domain.UserInput(root="マイナンバーは0000-0000-0000です")
        question5 = conversation_turn_domain.UserInput(root="クレジットカードは0000-0000-0000-0000です")
        want1 = Validation(
            is_valid=False,
            sensitive_contents=[
                SensitiveContent(type=SensitiveContentType.PHONE_NUMBER, content="000-0000-0000"),
            ],
        )
        want2 = Validation(
            is_valid=False,
            sensitive_contents=[
                SensitiveContent(type=SensitiveContentType.EMAIL, content="aaaa@gmail.com"),
            ],
        )
        want3 = Validation(
            is_valid=False,
            sensitive_contents=[
                SensitiveContent(type=SensitiveContentType.POSTAL_CODE, content="000-0000"),
            ],
        )
        want4 = Validation(
            is_valid=False,
            sensitive_contents=[
                SensitiveContent(type=SensitiveContentType.MY_NUMBER, content="0000-0000-0000"),
            ],
        )
        want5 = Validation(
            is_valid=False,
            sensitive_contents=[
                SensitiveContent(type=SensitiveContentType.CREDIT_CARD, content="0000-0000-0000-0000"),
            ],
        )

        got1 = self.conversation_usecase.validate_conversation(
            question=question1,
        )
        got2 = self.conversation_usecase.validate_conversation(
            question=question2,
        )
        got3 = self.conversation_usecase.validate_conversation(
            question=question3,
        )
        got4 = self.conversation_usecase.validate_conversation(
            question=question4,
        )
        got5 = self.conversation_usecase.validate_conversation(
            question=question5,
        )

        assert got1 == want1
        assert got2 == want2
        assert got3 == want3
        assert got4 == want4
        assert got5 == want5

    def test_preview_conversation(self, setup):
        input = PreviewConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_domain.Id(value=1),
                name=tenant_domain.Name(value="test_tenant_name"),
                index_name=IndexName(root="test-index-name"),
                container_name=ContainerName(root="test-container-name"),
            ),
            history=[
                conversation_turn_domain.Turn(
                    user=conversation_turn_domain.Message(root="hello"),
                    bot=None,
                )
            ],
            approach=bot_domain.Approach.CUSTOM_GPT,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            response_system_prompt=bot_domain.ResponseSystemPrompt(root="test"),
        )

        dummy_data_points = self.dummy_data_points()
        dummy_answer = "ダミーの回答"
        mock_output = [
            ConversationOutputAnswer(answer=dummy_answer),
            ConversationOutputDataPoints(data_points=dummy_data_points),
        ]
        self.conversation_usecase._preview_chat_completion_create = Mock(return_value=iter(mock_output))

        got = self.conversation_usecase.preview_conversation(input)

        for item in got:
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == dummy_data_points
                continue
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == dummy_answer
                continue

    def test_save_conversation(self, setup, mock_create_conversation_id: Mock):
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=mock_create_conversation_id.return_value)

        self.conversation_usecase.conversation_repo.save_conversation = Mock(
            return_value=conversation_domain.Conversation(
                title=None,
                user_id=user_id,
                bot_id=bot_id,
                id=conversation_id,
            )
        )

        got = self.conversation_usecase._save_conversation(
            bot_id=bot_id,
            user_id=user_id,
        )

        self.conversation_usecase.conversation_repo.save_conversation.assert_called_once_with(
            conversation_domain.ConversationForCreate(
                user_id=user_id,
                bot_id=bot_id,
            )
        )
        assert got == conversation_id

    def test_get_conversation_with_bot(self, setup):
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))

        want = conversation_domain.ConversationWithBot(
            id=conversation_id,
            title=conversation_domain.Title(root="title"),
            user_id=user_id,
            bot_id=bot_id,
            bot=self.dummy_bot(bot_id),
            turns=[],
        )
        self.conversation_usecase.conversation_repo.find_with_bot_by_id_and_bot_id_and_user_id = Mock(
            return_value=want
        )

        got = self.conversation_usecase._get_conversation_with_bot(
            conversation_id=conversation_id,
            bot_id=bot_id,
            user_id=user_id,
        )

        self.conversation_usecase.conversation_repo.find_with_bot_by_id_and_bot_id_and_user_id.assert_called_once_with(
            conversation_id, bot_id, user_id
        )
        assert got == want

    def test_save_conversation_turn(
        self,
        setup,
        mock_create_conversation_id: Mock,
        mock_create_conversation_turn_id: Mock,
        mock_create_conversation_data_point_id: Mock,
    ):
        conversation_id = conversation_domain.Id(root=mock_create_conversation_id.return_value)
        conversation_turn_id = conversation_turn_domain.Id(root=mock_create_conversation_turn_id.return_value)
        conversation_data_point_id = conversation_data_point_domain.Id(
            root=mock_create_conversation_data_point_id.return_value
        )
        question = conversation_turn_domain.UserInput(root="test question")
        answer = "test answer"
        queries = ["クエリ1", "クエリ2"]
        bot = self.dummy_bot(bot_id=bot_domain.Id(value=1))
        query_input_token = 100
        query_output_token = 150
        response_input_token = 200
        response_output_token = 250
        token_count = token_domain.TokenCount(root=100.0)
        data_points = self.dummy_data_points()
        allow_foreign_region = AllowForeignRegion(root=False)
        additional_platforms = tenant_domain.AdditionalPlatformList(root=[])
        query_generator_model_orders = get_lightweight_model_orders(
            platforms=[platform.root for platform in additional_platforms.root],
            allow_foreign_region=allow_foreign_region,
        )
        response_generator_model = bot.response_generator_model_family.to_model(
            additional_platforms=[platform.root for platform in additional_platforms.root],
            allow_foreign_region=allow_foreign_region,
        )

        query_generator_model = query_generator_model_orders[0]

        self.conversation_usecase.conversation_repo.save_conversation_turn = Mock(
            return_value=conversation_turn_domain.ConversationTurn(
                id=conversation_turn_id,
                conversation_id=conversation_id,
                user_input=question,
                bot_output=conversation_turn_domain.BotOutput(root=answer),
                queries=[conversation_turn_domain.Query(root=query) for query in queries],
                token_set=token_domain.TokenSet(
                    query_input_token=token_domain.Token(root=query_input_token),
                    query_output_token=token_domain.Token(root=query_output_token),
                    response_input_token=token_domain.Token(root=response_input_token),
                    response_output_token=token_domain.Token(root=response_output_token),
                ),
                token_count=token_count,
                query_generator_model=query_generator_model,
                response_generator_model=response_generator_model,
                evaluation=None,
                comment=None,
                created_at=conversation_turn_domain.CreatedAt(root=datetime.utcnow()),
                data_points=[
                    conversation_data_point_domain.ConversationDataPoint(
                        id=conversation_data_point_id,
                        content=data_point.content,
                        cite_number=data_point.cite_number,
                        chunk_name=data_point.chunk_name,
                        page_number=data_point.page_number,
                        blob_path=data_point.blob_path,
                        type=data_point.type,
                        url=data_point.url,
                        turn_id=conversation_turn_id,
                    )
                    for data_point in data_points
                ],
            )
        )
        self.conversation_usecase.conversation_repo.update_conversation_timestamp = Mock()

        got = self.conversation_usecase._save_conversation_turn(
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            queries=queries,
            query_input_token=query_input_token,
            query_output_token=query_output_token,
            response_input_token=response_input_token,
            response_output_token=response_output_token,
            token_count=token_count,
            data_points=data_points,
            query_generator_model=query_generator_model,
            response_generator_model=response_generator_model,
            image_generator_model=None,
            document_folder=None,
        )

        self.conversation_usecase.conversation_repo.save_conversation_turn.assert_called_once_with(
            conversation_turn_domain.ConversationTurnForCreate(
                conversation_id=conversation_id,
                user_input=question,
                bot_output=conversation_turn_domain.BotOutput(root=answer),
                queries=[conversation_turn_domain.Query(root=query) for query in queries],
                token_set=token_domain.TokenSet(
                    query_input_token=token_domain.Token(root=query_input_token),
                    query_output_token=token_domain.Token(root=query_output_token),
                    response_input_token=token_domain.Token(root=response_input_token),
                    response_output_token=token_domain.Token(root=response_output_token),
                ),
                token_count=token_count,
                query_generator_model=query_generator_model,
                response_generator_model=response_generator_model,
            ),
            [
                conversation_data_point_domain.ConversationDataPointForCreate(
                    content=data_point.content,
                    cite_number=data_point.cite_number,
                    chunk_name=data_point.chunk_name,
                    page_number=data_point.page_number,
                    blob_path=data_point.blob_path,
                    type=data_point.type,
                    url=data_point.url,
                    turn_id=conversation_turn_id,
                )
                for data_point in data_points
            ],
        )
        self.conversation_usecase.conversation_repo.update_conversation_timestamp.assert_called_once_with(
            conversation_id
        )
        assert got == conversation_turn_id

    def test_validate_search_conversation(self, setup, mock_get_feature_flag):
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant"),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
        )
        bot = self.dummy_bot(bot_id=bot_domain.Id(value=1))

        assert self.conversation_usecase._validate_search_conversation(tenant, bot) is None

    def test_get_attachment_for_conversation(self, setup):
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant"),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
        )
        bot_id = bot_domain.Id(value=1)
        container_name = ContainerName(root="test-container")
        pdf_parser = llm_domain.PdfParser.PYPDF
        attachment_id = attachment_domain.Id(root=uuid4())

        attachment = attachment_domain.Attachment(
            id=attachment_id,
            name=attachment_domain.Name(root="test-attachment"),
            created_at=attachment_domain.CreatedAt(root=datetime.utcnow()),
            file_extension=attachment_domain.FileExtension.PDF,
            is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
        )
        self.conversation_usecase.attachment_repo.find_by_id = Mock(return_value=attachment)
        self.conversation_usecase.blob_storage_service.get_attachment_blob_content = Mock(
            return_value=attachment_domain.BlobContent(root=b"test pdf content")
        )

        with (
            patch.object(attachment_domain.BlobContent, "parse_pdf_file_by_pypdf", return_value="test"),
            patch.object(
                attachment_domain.BlobContent,
                "count_pages",
                return_value=attachment_domain.ContentPageCount(root=1),
            ),
        ):
            got = self.conversation_usecase._get_attachment_for_conversation(
                tenant=tenant,
                bot_id=bot_id,
                container_name=container_name,
                attachment_id=attachment_id,
                pdf_parser=pdf_parser,
            )

        self.conversation_usecase.attachment_repo.find_by_id.assert_called_once_with(attachment_id)
        self.conversation_usecase.blob_storage_service.get_attachment_blob_content.assert_called_once_with(
            bot_id=bot_id, container_name=container_name, blob_name=attachment.blob_name
        )
        assert got == attachment_domain.AttachmentForConversation(
            name=attachment_domain.Name(root="test-attachment"),
            content=attachment_domain.Content(root="test"),
        )

    def test_update_attachments(self, setup, mock_create_conversation_turn_id: Mock):
        conversation_turn_id = conversation_turn_domain.Id(root=mock_create_conversation_turn_id.return_value)
        attachment_id = attachment_domain.Id(root=uuid4())
        attachments = [
            ConversationAttachment(
                from_="user",
                attachment_id=attachment_id,
            )
        ]

        self.conversation_usecase.attachment_repo.update_conversation_turn_ids = Mock()

        assert (
            self.conversation_usecase._update_attachments(
                conversation_turn_id=conversation_turn_id,
                attachments=attachments,
            )
            is None
        )
        self.conversation_usecase.attachment_repo.update_conversation_turn_ids.assert_called_once_with(
            [attachment_id], conversation_turn_id
        )

    def test_calculate_token_count(self, setup, mock_get_feature_flag):
        mock_get_feature_flag.return_value = True
        response_system_prompt = "test"
        response_system_prompt_hidden = " ".join(["test"] * 2)
        turns = [
            conversation_turn_domain.Turn(
                user=conversation_turn_domain.Message(root=" ".join(["test"] * 2**2)),
                bot=conversation_turn_domain.Message(root=" ".join(["test"] * 2**3)),
            )
        ]
        answer = " ".join(["test"] * 2**4)
        attachments = [
            {
                "user": attachment_domain.AttachmentForConversation(
                    name=attachment_domain.Name(root=" ".join(["test"] * 2**5)),
                    content=attachment_domain.Content(root=" ".join(["test"] * 2**6)),
                )
            }
        ]
        data_points = [
            DataPoint(
                document_id=None,
                cite_number=CiteNumber(root=1),
                chunk_name=ChunkName(root="chunk1"),
                page_number=PageNumber(root=10),
                blob_path=BlobPath(root="file1.pdf"),
                content=Content(root=" ".join(["test"] * 2**7)),
                type=Type.INTERNAL,
                url=Url(root=""),
            ),
            DataPoint(
                document_id=None,
                cite_number=CiteNumber(root=2),
                chunk_name=ChunkName(root="chunk2"),
                page_number=PageNumber(root=20),
                blob_path=BlobPath(root="file2.pdf"),
                content=Content(root=" ".join(["test"] * 2**8)),
                type=Type.INTERNAL,
                url=Url(root=""),
            ),
        ]
        terms = {
            " ".join(["test"] * 2**9): " ".join(["test"] * 2**10),
            " ".join(["test"] * 2**11): " ".join(["test"] * 2**12),
        }
        use_query_generator = True
        model_name = ModelName.GPT_4_TURBO_2024_04_09

        got = self.conversation_usecase._calculate_token_count(
            response_system_prompt=bot_domain.ResponseSystemPrompt(root=response_system_prompt),
            response_system_prompt_hidden=bot_domain.ResponseSystemPromptHidden(root=response_system_prompt_hidden),
            history=turns,
            answer_tokens=Token.from_string(answer),
            attachments=attachments,
            data_points=data_points,
            terms_dict=term_domain.TermsDict(root=terms),
            use_query_generator=use_query_generator,
            use_image_generator=True,
            model_name=model_name,
            is_follow_up_questions_generated=True,
        )

        want = 0
        for i in range(13):
            want += 2**i
        want += QUERY_GENERATOR_TOKEN + RESPONSE_GENERATOR_TOKEN + FOLLOW_UP_QUESTION_TOKEN + IMAGE_GENERATOR_TOKEN
        assert got == TokenCount(root=want)

    def test_create_conversation_stream_chat_gpt_default(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        question = conversation_turn_domain.UserInput(root="sample question")
        attachments = []
        use_web_browsing = conversation_domain.UseWebBrowsing(root=False)
        inputs = CreateConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_id,
                name=tenant_name,
                index_name=tenant_index_name,
                container_name=tenant_container_name,
            ),
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=None,
            question=question,
            attachments=attachments,
            use_web_browsing=use_web_browsing,
        )

        # Mock
        answer = "ダミーの回答"
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        self.conversation_usecase._save_conversation = Mock(
            return_value=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        )
        self.conversation_usecase._get_conversation_with_bot = Mock(
            return_value=conversation_domain.ConversationWithBot(
                id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                title=conversation_domain.Title(root="title"),
                user_id=user_id,
                bot_id=bot_id,
                bot=self.dummy_bot(bot_id),
                turns=[],
            )
        )
        self.conversation_usecase._validate_search_conversation = Mock()
        self.conversation_usecase.term_repo.find_by_bot_id = Mock(return_value=[])
        self.conversation_usecase.llm_service.update_query_with_terms = Mock(
            return_value=([], term_domain.TermsDict())
        )
        self.conversation_usecase.llm_service.generate_response_without_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.conversation_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.conversation_usecase._save_conversation_turn = Mock(return_value=conversation_turn_id)
        self.conversation_usecase._update_attachments = Mock()

        # Execute
        it = self.conversation_usecase.create_conversation_stream(inputs)

        # Test
        for item in it:
            if isinstance(item, conversation_domain.Id):
                assert item == conversation_id
            if isinstance(item, conversation_turn_domain.Id):
                assert item == conversation_turn_id
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == []
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == answer

    def test_create_conversation_stream_custom_gpt(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        question = conversation_turn_domain.UserInput(root="sample question")
        attachments = []
        use_web_browsing = conversation_domain.UseWebBrowsing(root=True)
        inputs = CreateConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_id,
                name=tenant_name,
                index_name=tenant_index_name,
                container_name=tenant_container_name,
            ),
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=None,
            question=question,
            attachments=attachments,
            use_web_browsing=use_web_browsing,
        )

        # Mock
        answer = "ダミーの回答"
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        data_points_from_web = self.dummy_data_points()
        self.conversation_usecase._save_conversation = Mock(
            return_value=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        )
        self.conversation_usecase._get_conversation_with_bot = Mock(
            return_value=conversation_domain.ConversationWithBot(
                id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                title=conversation_domain.Title(root="title"),
                user_id=user_id,
                bot_id=bot_id,
                bot=bot_domain.Bot(
                    id=bot_id,
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
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    status=bot_domain.Status.ACTIVE,
                    icon_url=bot_domain.IconUrl(
                        root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
                    ),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    endpoint_id=bot_domain.EndpointId(root=uuid4()),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                ),
                turns=[],
            )
        )
        self.conversation_usecase._validate_search_conversation = Mock()
        self.conversation_usecase.term_repo.find_by_bot_id = Mock(return_value=[])
        self.conversation_usecase.llm_service.generate_query = Mock(
            return_value=QueryGeneratorOutput(
                queries=Queries.from_list(["クエリ1", "クエリ2"]),
                input_token=100,
                output_token=150,
            )
        )
        self.conversation_usecase.llm_service.update_query_with_terms = Mock(
            return_value=(Queries.from_list([]), term_domain.TermsDict())
        )
        self.conversation_usecase.bing_search_service.search_web_documents = Mock(return_value=data_points_from_web)
        self.conversation_usecase.llm_service.generate_response_without_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.conversation_usecase.web_scraping_service.find_url_from_text = Mock(return_value=[])
        self.conversation_usecase.web_scraping_service.web_search_from_url = Mock(return_value=[])
        self.conversation_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.conversation_usecase._save_conversation_turn = Mock(return_value=conversation_turn_id)
        self.conversation_usecase._update_attachments = Mock()

        # Execute
        it = self.conversation_usecase.create_conversation_stream(inputs)

        # Test
        for item in it:
            if isinstance(item, conversation_domain.Id):
                assert item == conversation_id
            if isinstance(item, conversation_turn_domain.Id):
                assert item == conversation_turn_id
            if isinstance(item, ConversationOutputQuery):
                assert item.query == ["クエリ1", "クエリ2"]
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == data_points_from_web
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == answer

    def test_create_conversation_stream_neollm(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        question = conversation_turn_domain.UserInput(root="sample question")
        attachments = []
        use_web_browsing = conversation_domain.UseWebBrowsing(root=False)
        inputs = CreateConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_id,
                name=tenant_name,
                index_name=tenant_index_name,
                container_name=tenant_container_name,
            ),
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=None,
            question=question,
            attachments=attachments,
            use_web_browsing=use_web_browsing,
        )

        # Mock
        answer = "ダミーの回答"
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        data_points_from_internal = self.dummy_data_points()
        self.conversation_usecase._save_conversation = Mock(
            return_value=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        )
        self.conversation_usecase._get_conversation_with_bot = Mock(
            return_value=conversation_domain.ConversationWithBot(
                id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                title=conversation_domain.Title(root="title"),
                user_id=user_id,
                bot_id=bot_id,
                bot=bot_domain.Bot(
                    id=bot_id,
                    group_id=group_domain.Id(value=1),
                    name=bot_domain.Name(value="Test Bot"),
                    description=bot_domain.Description(value="This is a test bot."),
                    created_at=bot_domain.CreatedAt(root=datetime.now()),
                    index_name=None,
                    container_name=ContainerName(root="test-container"),
                    approach=bot_domain.Approach.NEOLLM,
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                    example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                    search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
                    response_generator_model_family=ModelFamily.GPT_35_TURBO,
                    approach_variables=[],
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    status=bot_domain.Status.ACTIVE,
                    icon_url=bot_domain.IconUrl(
                        root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
                    ),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    endpoint_id=bot_domain.EndpointId(root=uuid4()),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                ),
                turns=[],
            )
        )
        self.conversation_usecase._validate_search_conversation = Mock()
        self.conversation_usecase.term_repo.find_by_bot_id = Mock(return_value=[])
        self.conversation_usecase.llm_service.generate_query = Mock(
            return_value=QueryGeneratorOutput(
                queries=Queries.from_list(["クエリ1", "クエリ2"]),
                input_token=100,
                output_token=150,
            )
        )
        self.conversation_usecase.llm_service.update_query_with_terms = Mock(
            return_value=(Queries.from_list([]), term_domain.TermsDict())
        )
        self.conversation_usecase.llm_service.generate_embeddings = Mock(return_value=[0, 0, 0])
        self.conversation_usecase.cognitive_search_service.search_documents = Mock(
            return_value=data_points_from_internal
        )
        self.conversation_usecase.llm_service.generate_response_with_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.conversation_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.conversation_usecase._save_conversation_turn = Mock(return_value=conversation_turn_id)
        self.conversation_usecase._update_attachments = Mock()

        # Execute
        it = self.conversation_usecase.create_conversation_stream(inputs)

        # Test
        for item in it:
            if isinstance(item, conversation_domain.Id):
                assert item == conversation_id
            if isinstance(item, conversation_turn_domain.Id):
                assert item == conversation_turn_id
            if isinstance(item, ConversationOutputQuery):
                assert item.query == ["クエリ1", "クエリ2"]
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == data_points_from_internal
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == answer

    def test_create_conversation_stream_neollm_with_document_folder(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        question = conversation_turn_domain.UserInput(root="sample question")
        attachments = []
        use_web_browsing = conversation_domain.UseWebBrowsing(root=False)
        dummy_document_folder_with_descentants = self.dummy_document_folder_with_descentants()
        inputs = CreateConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_id,
                name=tenant_name,
                index_name=tenant_index_name,
                container_name=tenant_container_name,
            ),
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=None,
            question=question,
            attachments=attachments,
            use_web_browsing=use_web_browsing,
            document_folder_id=dummy_document_folder_with_descentants.id,
        )

        # Mock
        answer = "ダミーの回答"
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        data_points_from_internal = self.dummy_data_points()
        self.conversation_usecase._save_conversation = Mock(
            return_value=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        )
        self.conversation_usecase._get_conversation_with_bot = Mock(
            return_value=conversation_domain.ConversationWithBot(
                id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                title=conversation_domain.Title(root="title"),
                user_id=user_id,
                bot_id=bot_id,
                bot=bot_domain.Bot(
                    id=bot_id,
                    group_id=group_domain.Id(value=1),
                    name=bot_domain.Name(value="Test Bot"),
                    description=bot_domain.Description(value="This is a test bot."),
                    created_at=bot_domain.CreatedAt(root=datetime.now()),
                    index_name=None,
                    container_name=ContainerName(root="test-container"),
                    approach=bot_domain.Approach.NEOLLM,
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                    example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                    search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
                    response_generator_model_family=ModelFamily.GPT_35_TURBO,
                    approach_variables=[],
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    status=bot_domain.Status.ACTIVE,
                    icon_url=bot_domain.IconUrl(
                        root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
                    ),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    endpoint_id=bot_domain.EndpointId(root=uuid4()),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                ),
                turns=[],
            )
        )
        self.conversation_usecase._validate_search_conversation = Mock()
        self.conversation_usecase.term_repo.find_by_bot_id = Mock(return_value=[])
        self.conversation_usecase.llm_service.generate_query = Mock(
            return_value=QueryGeneratorOutput(
                queries=Queries.from_list(["クエリ1", "クエリ2"]),
                input_token=100,
                output_token=150,
            )
        )
        self.conversation_usecase.llm_service.update_query_with_terms = Mock(
            return_value=(Queries.from_list([]), term_domain.TermsDict())
        )
        self.conversation_usecase.llm_service.generate_embeddings = Mock(return_value=[0, 0, 0])
        self.conversation_usecase.cognitive_search_service.search_documents = Mock(
            return_value=data_points_from_internal
        )
        self.conversation_usecase.llm_service.generate_response_with_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.conversation_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.conversation_usecase._save_conversation_turn = Mock(return_value=conversation_turn_id)
        self.conversation_usecase._update_attachments = Mock()
        self.conversation_usecase.document_folder_repo.find_with_descendants_by_id_and_bot_id = Mock(
            return_value=dummy_document_folder_with_descentants
        )

        # Execute
        it = self.conversation_usecase.create_conversation_stream(inputs)

        # Test
        for item in it:
            if isinstance(item, conversation_domain.Id):
                assert item == conversation_id
            if isinstance(item, conversation_turn_domain.Id):
                assert item == conversation_turn_id
            if isinstance(item, ConversationOutputQuery):
                assert item.query == ["クエリ1", "クエリ2"]
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == data_points_from_internal
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == answer

    def test_create_conversation_stream_ursa(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        question = conversation_turn_domain.UserInput(root="sample question")
        attachments = []
        use_web_browsing = conversation_domain.UseWebBrowsing(root=False)
        inputs = CreateConversationInput(
            tenant=self.dummy_tenant(
                id=tenant_id,
                name=tenant_name,
                index_name=tenant_index_name,
                container_name=tenant_container_name,
            ),
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=None,
            question=question,
            attachments=attachments,
            use_web_browsing=use_web_browsing,
        )

        # Mock
        answer = "ダミーの回答"
        conversation_id = conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        conversation_turn_id = conversation_turn_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440001"))
        data_points = self.dummy_data_points()
        self.conversation_usecase._save_conversation = Mock(
            return_value=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000"))
        )
        self.conversation_usecase._get_conversation_with_bot = Mock(
            return_value=conversation_domain.ConversationWithBot(
                id=conversation_domain.Id(root=UUID("550e8400-e29b-41d4-a716-446655440000")),
                title=conversation_domain.Title(root="title"),
                user_id=user_id,
                bot_id=bot_id,
                bot=bot_domain.Bot(
                    id=bot_id,
                    group_id=group_domain.Id(value=1),
                    name=bot_domain.Name(value="Test Bot"),
                    description=bot_domain.Description(value="This is a test bot."),
                    created_at=bot_domain.CreatedAt(root=datetime.now()),
                    index_name=IndexName(root="test-index"),
                    container_name=ContainerName(root="test-container"),
                    approach=bot_domain.Approach.URSA,
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                    example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                    search_method=bot_domain.SearchMethod.URSA,
                    response_generator_model_family=ModelFamily.GPT_35_TURBO,
                    approach_variables=[
                        ApproachVariable(
                            name=ApproachVariableName(value="search_service_endpoint"),
                            value=ApproachVariableValue(value="https://test-search-service-endpoint.com"),
                        )
                    ],
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    status=bot_domain.Status.ACTIVE,
                    icon_url=bot_domain.IconUrl(
                        root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
                    ),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    endpoint_id=bot_domain.EndpointId(root=uuid4()),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                ),
                turns=[],
            )
        )
        self.conversation_usecase._validate_search_conversation = Mock()
        self.conversation_usecase.term_repo.find_by_bot_id = Mock(return_value=[])
        self.conversation_usecase.llm_service.generate_ursa_query = Mock(
            return_value=QueryGeneratorOutput(
                queries=Queries.from_list(["クエリ1", "クエリ2"]),
                input_token=100,
                output_token=150,
            )
        )
        self.conversation_usecase.llm_service.update_query_with_terms = Mock(
            return_value=([], term_domain.TermsDict())
        )
        self.conversation_usecase.llm_service.generate_embeddings = Mock(return_value=[0, 0, 0])
        self.conversation_usecase.cognitive_search_service.search_documents = Mock(return_value=data_points)
        self.conversation_usecase.llm_service.generate_ursa_response = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.conversation_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.conversation_usecase._save_conversation_turn = Mock(return_value=conversation_turn_id)
        self.conversation_usecase._update_attachments = Mock()

        # Execute
        it = self.conversation_usecase.create_conversation_stream(inputs)

        # Test
        for item in it:
            if isinstance(item, conversation_domain.Id):
                assert item == conversation_id
            if isinstance(item, conversation_turn_domain.Id):
                assert item == conversation_turn_id
            if isinstance(item, ConversationOutputQuery):
                assert item.query == ["クエリ1", "クエリ2"]
            if isinstance(item, ConversationOutputDataPoints):
                assert item.data_points == data_points
            if isinstance(item, ConversationOutputAnswer):
                assert item.answer == answer
                assert item.answer == answer

    def test_get_data_points_with_document_feedback_summary(
        self, setup, mock_create_conversation_id: Mock, mock_create_conversation_turn_id: Mock
    ):
        # Input
        user_id = user_domain.Id(value=1)
        conversation_data_points = self.dummy_conversation_data_points(mock_create_conversation_turn_id)

        # Mock
        self.conversation_usecase.conversation_repo.find_data_points_with_total_good_by_user_id_and_id_and_turn_id = (
            Mock(return_value=conversation_data_points)
        )
        self.conversation_usecase.document_repo.find_feedbacks_by_ids_and_user_id = Mock(return_value=[])

        # Execute
        self.conversation_usecase.get_data_points_with_document_feedback_summary(
            user_id, mock_create_conversation_id.return_value, mock_create_conversation_turn_id.return_value
        )

        # Test
        self.conversation_usecase.conversation_repo.find_data_points_with_total_good_by_user_id_and_id_and_turn_id.assert_called_once_with(
            user_id, mock_create_conversation_id.return_value, mock_create_conversation_turn_id.return_value
        )
        self.conversation_usecase.document_repo.find_feedbacks_by_ids_and_user_id.assert_called_once_with([], user_id)

    def test_get_conversation_export_signed_url(self, setup):
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant_name"),
            index_name=IndexName(root="tenant-index-name"),
            container_name=ContainerName(root="test-container"),
        )
        conversation_export_id = conversation_export_domain.Id(root=uuid4())
        user_id = user_domain.Id(value=1)
        conversation_export = conversation_export_domain.ConversationExport(
            id=conversation_export_id,
            status=conversation_export_domain.Status.PROCESSING,
            user_id=user_id,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime(2024, 10, 1, 0, 0, 0)),
            end_date_time=conversation_export_domain.EndDateTime(root=datetime(2024, 10, 16, 0, 0, 0)),
            target_user_id=user_id,
            target_bot_id=bot_domain.Id(value=1),
        )
        signed_url = conversation_export_domain.SignedUrl(
            root="https://test-signed-url.com",
        )

        self.conversation_usecase.conversation_export_repo.find_by_id = Mock(return_value=conversation_export)
        self.conversation_usecase.blob_storage_service.create_blob_conversation_sas_url = Mock(return_value=signed_url)

        result = self.conversation_usecase.get_conversation_export_signed_url(
            tenant=tenant, conversation_export_id=conversation_export_id
        )

        assert result == signed_url
        self.conversation_usecase.conversation_export_repo.find_by_id.assert_called_once_with(
            tenant_id=tenant.id, id=conversation_export_id
        )
        self.conversation_usecase.blob_storage_service.create_blob_conversation_sas_url.assert_called_once_with(
            container_name=tenant.container_name, blob_path=conversation_export.blob_path
        )
