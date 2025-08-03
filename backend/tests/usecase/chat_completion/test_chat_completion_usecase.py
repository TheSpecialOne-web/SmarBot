from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion_export as chat_completion_export_domain,
    data_point as dp_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    term as term_domain,
    user as user_domain,
)
from api.domain.models.chat_completion import (
    ChatCompletion,
    ChatCompletionWithApiKeyId,
    Comment,
    Content,
    Evaluation,
    Id,
    Message,
    Messages,
    Role,
)
from api.domain.models.chat_completion.chat_completion import ChatCompletionForCreate
from api.domain.models.chat_completion.data_point import ChatCompletionDataPoint
from api.domain.models.llm import AllowForeignRegion, ModelName
from api.domain.models.llm.model import ModelFamily
from api.domain.models.query.query import Queries
from api.domain.models.search.endpoint import Endpoint
from api.domain.models.search.index_name import IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.token import TokenCount
from api.domain.services.llm.llm import QueryGeneratorOutput, ResponseGeneratorOutputToken
from api.usecase.chat_completion.chat_completion import ChatCompletionUseCase
from api.usecase.chat_completion.types import (
    ChatCompletionAnswer,
    ChatCompletionDataPoints,
    ChatCompletionWithBotAndApiKey,
    CreateChatCompletionInput,
    UpdateChatCompletionFeedbackCommentInput,
    UpdateChatCompletionFeedbackEvaluationInput,
)
from api.usecase.conversation.conversation import QUERY_GENERATOR_TOKEN, RESPONSE_GENERATOR_TOKEN


class TestChatCompletionUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.chat_completion_repo = Mock()
        self.api_key_repo = Mock()
        self.term_repo = Mock()
        self.llm_service = Mock()
        self.cognitive_search_service = Mock()
        self.user_repo = Mock()
        self.chat_completion_export_repo = Mock()
        self.queue_storage_service = Mock()
        self.blob_storage_service = Mock()
        self.tenant_repo = Mock()
        self.chat_completion_usecase = ChatCompletionUseCase(
            bot_repo=self.bot_repo,
            chat_completion_repo=self.chat_completion_repo,
            chat_completion_export_repo=self.chat_completion_export_repo,
            api_key_repo=self.api_key_repo,
            term_repo=self.term_repo,
            llm_service=self.llm_service,
            cognitive_search_service=self.cognitive_search_service,
            user_repo=self.user_repo,
            queue_storage_service=self.queue_storage_service,
            blob_storage_service=self.blob_storage_service,
            tenant_repo=self.tenant_repo,
        )

    @pytest.fixture
    def mock_create_chat_completion_id(self, monkeypatch):
        mock_create_chat_completion_id = Mock(return_value=uuid.UUID("00000000-0000-0000-0000-000000000000"))
        monkeypatch.setattr(
            "api.domain.models.chat_completion.id.uuid4",
            mock_create_chat_completion_id,
        )
        return mock_create_chat_completion_id

    @pytest.fixture
    def mock_create_chat_completion_data_point_id(self, monkeypatch):
        mock_create_chat_completion_data_point_id = Mock(
            return_value=uuid.UUID("00000000-0000-0000-0000-000000000001")
        )
        monkeypatch.setattr(
            "api.domain.models.chat_completion.data_point.id.uuid4",
            mock_create_chat_completion_data_point_id,
        )
        return mock_create_chat_completion_data_point_id

    def dummy_user(self, user_id: user_domain.Id):
        return user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test_user"),
            email=user_domain.Email(value="test@test.user"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

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

    def dummy_bot(self, bot_id: bot_domain.Id) -> bot_domain.Bot:
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_api_key(
        self,
        bot_id: bot_domain.Id,
        api_key_id: api_key_domain.Id,
        endpoint_id: bot_domain.EndpointId,
    ) -> api_key_domain.ApiKey:
        return api_key_domain.ApiKey(
            id=api_key_id,
            bot_id=bot_id,
            name=api_key_domain.Name(root="Test API Key"),
            expires_at=api_key_domain.ExpiresAt(root=datetime.now() + timedelta(days=1)),
            decrypted_api_key=api_key_domain.DecryptedApiKey(root="test"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
        )

    def dummy_chat_completion(self, id: Id, api_key_id: api_key_domain.Id) -> ChatCompletionWithApiKeyId:
        return ChatCompletionWithApiKeyId(
            id=id,
            api_key_id=api_key_id,
            messages=Messages(root=[Message(role=Role.USER, content=Content(root="Test message."))]),
            answer=Content(root="Test answer."),
            token_count=TokenCount(root=100),
            data_points=[],
        )

    def dummy_chat_completion_export(
        self,
        id: chat_completion_export_domain.Id,
        creator_id: user_domain.Id,
        bot_id: bot_domain.Id,
        api_key_id: api_key_domain.Id,
    ) -> chat_completion_export_domain.ChatCompletionExport:
        return chat_completion_export_domain.ChatCompletionExport(
            id=id,
            creator_id=creator_id,
            start_date_time=chat_completion_export_domain.StartDateTime(root=datetime.now(timezone.utc)),
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.now(timezone.utc)),
            target_api_key_id=api_key_id,
            target_bot_id=bot_id,
            status=chat_completion_export_domain.Status("processing"),
        )

    def test_get_chat_completions_for_download(self, setup):
        # ダミーデータ作成
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id)
        self.chat_completion_usecase.bot_repo.find_by_id.return_value = bot
        api_key_id = api_key_domain.Id(root=uuid.uuid4())
        api_key = self.dummy_api_key(bot_id, api_key_id, bot.endpoint_id)
        chat_completion = self.dummy_chat_completion(id=Id(root=uuid.uuid4()), api_key_id=api_key_id)

        want = [
            ChatCompletionWithBotAndApiKey(
                chat_completion=ChatCompletion(
                    id=chat_completion.id,
                    messages=chat_completion.messages,
                    answer=chat_completion.answer,
                    token_count=chat_completion.token_count,
                    data_points=chat_completion.data_points,
                ),
                bot=bot,
                api_key=api_key,
            )
        ]

        self.chat_completion_usecase.bot_repo.find_all_by_tenant_id.return_value = [bot]
        self.chat_completion_usecase.api_key_repo.find_by_id_and_bot_id.return_value = api_key
        self.chat_completion_usecase.chat_completion_repo.find_by_api_key_ids_and_date.return_value = [chat_completion]

        got = self.chat_completion_usecase.get_chat_completions_for_download(
            tenant_id=tenant_id,
            bot_id=bot_id,
            api_key_id=api_key_id,
            start_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            end_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        )
        assert got == want

    def test_get_chat_completions_for_download_without_api_key_id(self, setup):
        # ダミーデータ作成
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        bot = self.dummy_bot(bot_id)
        api_keys = [
            self.dummy_api_key(bot_id, api_key_domain.Id(root=uuid.uuid4()), bot.endpoint_id),
            self.dummy_api_key(bot_id, api_key_domain.Id(root=uuid.uuid4()), bot.endpoint_id),
        ]

        self.chat_completion_usecase.bot_repo.find_by_id.return_value = bot
        self.chat_completion_usecase.api_key_repo.find_by_bot_ids.return_value = api_keys

        self.chat_completion_usecase.bot_repo.find_all_by_tenant_id.return_value = [bot]
        chat_completions = [
            self.dummy_chat_completion(id=Id(root=uuid.uuid4()), api_key_id=api_key.id) for api_key in api_keys
        ]

        want = [
            ChatCompletionWithBotAndApiKey(
                chat_completion=ChatCompletion(
                    id=chat_completion.id,
                    messages=chat_completion.messages,
                    answer=chat_completion.answer,
                    token_count=chat_completion.token_count,
                    data_points=chat_completion.data_points,
                ),
                bot=bot,
                api_key=next((api_key for api_key in api_keys if api_key.id == chat_completion.api_key_id)),
            )
            for chat_completion in chat_completions
        ]

        self.chat_completion_usecase.chat_completion_repo.find_by_api_key_ids_and_date.return_value = chat_completions

        got = self.chat_completion_usecase.get_chat_completions_for_download(
            tenant_id=tenant_id,
            bot_id=bot_id,
            api_key_id=None,
            start_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            end_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        )
        assert got == want

    def test_get_chat_completions_for_download_without_api_key_id_and_bot_id(self, setup):
        # ダミーデータ作成
        tenant_id = tenant_domain.Id(value=1)
        bots = [
            self.dummy_bot(bot_domain.Id(value=1)),
            self.dummy_bot(bot_domain.Id(value=2)),
            self.dummy_bot(bot_domain.Id(value=3)),
        ]
        api_keys = [
            self.dummy_api_key(bots[0].id, api_key_domain.Id(root=uuid.uuid4()), bots[0].endpoint_id),
            self.dummy_api_key(bots[0].id, api_key_domain.Id(root=uuid.uuid4()), bots[0].endpoint_id),
            self.dummy_api_key(bots[1].id, api_key_domain.Id(root=uuid.uuid4()), bots[1].endpoint_id),
            self.dummy_api_key(bots[2].id, api_key_domain.Id(root=uuid.uuid4()), bots[2].endpoint_id),
        ]

        self.chat_completion_usecase.api_key_repo.find_by_bot_ids.return_value = api_keys

        self.chat_completion_usecase.bot_repo.find_all_by_tenant_id.return_value = bots
        chat_completions: list[ChatCompletionWithApiKeyId] = []
        for api_key in api_keys:
            for _ in range(3):
                chat_completions.append(self.dummy_chat_completion(id=Id(root=uuid.uuid4()), api_key_id=api_key.id))

        chat_completions_with_bot_and_api_key: list[ChatCompletionWithBotAndApiKey] = []
        for chat_completion in chat_completions:
            api_key = next((api_key for api_key in api_keys if api_key.id == chat_completion.api_key_id))
            bot = next((bot for bot in bots if bot.id == api_key.bot_id))
            chat_completions_with_bot_and_api_key.append(
                ChatCompletionWithBotAndApiKey(
                    chat_completion=ChatCompletion(
                        id=chat_completion.id,
                        messages=chat_completion.messages,
                        answer=chat_completion.answer,
                        token_count=chat_completion.token_count,
                        data_points=chat_completion.data_points,
                    ),
                    bot=bot,
                    api_key=api_key,
                )
            )
        want = chat_completions_with_bot_and_api_key

        self.chat_completion_usecase.chat_completion_repo.find_by_api_key_ids_and_date.return_value = chat_completions

        got = self.chat_completion_usecase.get_chat_completions_for_download(
            tenant_id=tenant_id,
            bot_id=None,
            api_key_id=None,
            start_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            end_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        )
        assert got == want

    def dummy_data_points(self) -> list[dp_domain.DataPointWithoutCiteNumber]:
        return [
            dp_domain.DataPointWithoutCiteNumber(
                document_id=None,
                chunk_name=dp_domain.ChunkName(root="chunk1"),
                page_number=dp_domain.PageNumber(root=10),
                blob_path=dp_domain.BlobPath(root="file1.pdf"),
                content=dp_domain.Content(root="内容1"),
                type=dp_domain.Type.INTERNAL,
                url=dp_domain.Url(root=""),
            ),
            dp_domain.DataPointWithoutCiteNumber(
                document_id=None,
                chunk_name=dp_domain.ChunkName(root="chunk2"),
                page_number=dp_domain.PageNumber(root=20),
                blob_path=dp_domain.BlobPath(root="file2.pdf"),
                content=dp_domain.Content(root="内容2"),
                type=dp_domain.Type.INTERNAL,
                url=dp_domain.Url(root=""),
            ),
        ]

    def test_calculate_token_count(self, setup):
        response_system_prompt = "test"
        response_system_prompt_hidden = " ".join(["test"] * 2)
        messages = Messages(
            root=[
                Message(
                    role=Role.USER,
                    content=Content(root=" ".join(["test"] * 2**2)),
                )
            ]
        )
        answer = " ".join(["test"] * 2**3)
        data_points = [
            dp_domain.DataPoint(
                document_id=None,
                cite_number=dp_domain.CiteNumber(root=1),
                chunk_name=dp_domain.ChunkName(root="chunk1"),
                page_number=dp_domain.PageNumber(root=10),
                blob_path=dp_domain.BlobPath(root="file1.pdf"),
                content=dp_domain.Content(root=" ".join(["test"] * 2**4)),
                type=dp_domain.Type.INTERNAL,
                url=dp_domain.Url(root=""),
            ),
            dp_domain.DataPoint(
                document_id=None,
                cite_number=dp_domain.CiteNumber(root=2),
                chunk_name=dp_domain.ChunkName(root="chunk2"),
                page_number=dp_domain.PageNumber(root=20),
                blob_path=dp_domain.BlobPath(root="file2.pdf"),
                content=dp_domain.Content(root=" ".join(["test"] * 2**5)),
                type=dp_domain.Type.INTERNAL,
                url=dp_domain.Url(root=""),
            ),
        ]
        terms = {
            " ".join(["test"] * 2**6): " ".join(["test"] * 2**7),
            " ".join(["test"] * 2**8): " ".join(["test"] * 2**9),
        }
        use_query_generator = True
        model_name = ModelName.GPT_4_TURBO_1106

        got = self.chat_completion_usecase._calculate_token_count(
            response_system_prompt=bot_domain.ResponseSystemPrompt(root=response_system_prompt),
            response_system_prompt_hidden=bot_domain.ResponseSystemPromptHidden(root=response_system_prompt_hidden),
            use_query_generator=use_query_generator,
            terms_dict=term_domain.TermsDict(root=terms),
            used_data_points=data_points,
            history=messages,
            answer=answer,
            model_name=model_name,
        )

        want = 0
        for i in range(10):
            want += 2**i
        want += QUERY_GENERATOR_TOKEN + RESPONSE_GENERATOR_TOKEN
        assert got == TokenCount(root=want)

    def test_create_chat_completion_stream_custom_gpt(self, setup, mock_create_chat_completion_id):
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        tenant = self.dummy_tenant(
            id=tenant_id,
            name=tenant_name,
            index_name=tenant_index_name,
            container_name=tenant_container_name,
        )
        bot = bot_domain.Bot(
            id=bot_domain.Id(value=1),
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
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )
        api_key = self.dummy_api_key(
            bot_id=bot.id,
            api_key_id=api_key_domain.Id(root=uuid.uuid4()),
            endpoint_id=bot.endpoint_id,
        )
        answer = "ダミーの回答"

        self.chat_completion_usecase.llm_service.update_query_with_terms = Mock(
            return_value=(Queries.from_list([]), term_domain.TermsDict())
        )
        self.chat_completion_usecase.llm_service.generate_response_without_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.chat_completion_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.chat_completion_usecase.chat_completion_repo.create = Mock(return_value=ChatCompletion.create_empty())
        self.chat_completion_usecase.chat_completion_repo.update = Mock()
        self.chat_completion_usecase.chat_completion_repo.bulk_create_data_points = Mock()

        inputs = CreateChatCompletionInput(
            tenant=tenant,
            bot=bot,
            api_key=api_key,
            chat_completion=ChatCompletionForCreate(
                messages=Messages(root=[Message(role=Role.USER, content=Content(root="ダミーのメッセージ"))])
            ),
        )
        out = self.chat_completion_usecase.create_chat_completion_stream(input=inputs)

        for item in out:
            if isinstance(item, ChatCompletionAnswer):
                assert item.answer.root == answer
            if isinstance(item, ChatCompletionDataPoints):
                assert item.data_points == []

        self.chat_completion_usecase.chat_completion_repo.create.assert_called_once_with(
            api_key_id=api_key.id,
            chat_completion=ChatCompletion.create_empty(),
        )
        self.chat_completion_usecase.chat_completion_repo.update.assert_called_once_with(
            api_key_id=api_key.id,
            chat_completion=ChatCompletion(
                messages=inputs.chat_completion.messages,
                answer=Content(root=answer),
                token_count=TokenCount(root=100.0),
                data_points=[],
            ),
        )
        self.chat_completion_usecase.chat_completion_repo.bulk_create_data_points.assert_called_once_with(
            chat_completion_id=Id(root=mock_create_chat_completion_id.return_value),
            chat_completion_data_points=[],
        )

    def test_create_chat_completion_stream_neollm(
        self,
        setup,
        mock_create_chat_completion_id,
        mock_create_chat_completion_data_point_id,
    ):
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        tenant = self.dummy_tenant(
            id=tenant_id,
            name=tenant_name,
            index_name=tenant_index_name,
            container_name=tenant_container_name,
        )
        bot = bot_domain.Bot(
            id=bot_domain.Id(value=1),
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
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )
        api_key = self.dummy_api_key(
            bot_id=bot.id,
            api_key_id=api_key_domain.Id(root=uuid.uuid4()),
            endpoint_id=bot.endpoint_id,
        )
        data_points = self.dummy_data_points()
        answer = "ダミーの回答"

        self.chat_completion_usecase.llm_service.generate_query = Mock(
            return_value=QueryGeneratorOutput(
                queries=Queries.from_list(["クエリ1", "クエリ2"]),
                input_token=100,
                output_token=150,
            )
        )
        self.chat_completion_usecase.llm_service.update_query_with_terms = Mock(
            return_value=(Queries.from_list([]), term_domain.TermsDict())
        )
        self.chat_completion_usecase.llm_service.generate_embeddings = Mock(return_value=[0, 0, 0])
        self.chat_completion_usecase.cognitive_search_service.search_documents = Mock(return_value=data_points)
        self.chat_completion_usecase.llm_service.generate_response_with_internal_data = Mock(
            return_value=iter([answer, [], ResponseGeneratorOutputToken(input_token=100, output_token=150)])
        )
        self.chat_completion_usecase._calculate_token_count = Mock(return_value=TokenCount(root=100.0))
        self.chat_completion_usecase.chat_completion_repo.create = Mock(return_value=ChatCompletion.create_empty())
        self.chat_completion_usecase.chat_completion_repo.update = Mock()
        self.chat_completion_usecase.chat_completion_repo.bulk_create_data_points = Mock()

        inputs = CreateChatCompletionInput(
            tenant=tenant,
            bot=bot,
            api_key=api_key,
            chat_completion=ChatCompletionForCreate(
                messages=Messages(root=[Message(role=Role.USER, content=Content(root="ダミーのメッセージ"))])
            ),
        )
        out = self.chat_completion_usecase.create_chat_completion_stream(input=inputs)

        chat_completion_data_points = [
            ChatCompletionDataPoint(
                cite_number=dp_domain.CiteNumber(root=i + 1),
                **dp.model_dump(),
            )
            for i, dp in enumerate(data_points)
        ]
        for item in out:
            if isinstance(item, ChatCompletionAnswer):
                assert item.answer.root == answer
            if isinstance(item, ChatCompletionDataPoints):
                assert item.data_points == chat_completion_data_points

        self.chat_completion_usecase.chat_completion_repo.create.assert_called_once_with(
            api_key_id=api_key.id,
            chat_completion=ChatCompletion.create_empty(),
        )
        self.chat_completion_usecase.chat_completion_repo.update.assert_called_once_with(
            api_key_id=api_key.id,
            chat_completion=ChatCompletion(
                messages=inputs.chat_completion.messages,
                answer=Content(root=answer),
                token_count=TokenCount(root=100.0),
                data_points=chat_completion_data_points,
            ),
        )
        self.chat_completion_usecase.chat_completion_repo.bulk_create_data_points.assert_called_once_with(
            chat_completion_id=Id(root=mock_create_chat_completion_id.return_value),
            chat_completion_data_points=chat_completion_data_points,
        )

    def test_get_chat_completion_exports_with_user(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        tenant = self.dummy_tenant(
            id=tenant_id,
            name=tenant_name,
            index_name=tenant_index_name,
            container_name=tenant_container_name,
        )
        dummy_user = self.dummy_user(user_id=user_domain.Id(value=1))
        chat_completion_export_with_user = [
            chat_completion_export_domain.ChatCompletionExportWithUser(
                id=chat_completion_export_domain.Id(root=uuid.UUID("00000000-0000-0000-0000-000000000000")),
                creator=dummy_user,
                status=chat_completion_export_domain.Status.PROCESSING,
                created_at=chat_completion_export_domain.CreatedAt(root=datetime.now()),
            )
        ]
        self.chat_completion_usecase.chat_completion_export_repo.find_with_user_by_tenant_id = Mock(
            return_value=chat_completion_export_with_user
        )

        result = self.chat_completion_usecase.get_chat_completion_exports_with_user(tenant.id)

        assert result == chat_completion_export_with_user
        self.chat_completion_usecase.chat_completion_export_repo.find_with_user_by_tenant_id.assert_called_once_with(
            tenant_id=tenant.id
        )

    def test_delete_chat_completion_exports(self, setup):
        # Given
        tenant_id = tenant_domain.Id(value=1)
        tenant_name = tenant_domain.Name(value="test_tenant_name")
        tenant_index_name = IndexName(root="tenant-index-name")
        tenant_container_name = ContainerName(root="test-container")
        tenant = self.dummy_tenant(
            id=tenant_id,
            name=tenant_name,
            index_name=tenant_index_name,
            container_name=tenant_container_name,
        )
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        api_key_id = api_key_domain.Id(root=uuid.uuid4())
        chat_completion_export_id = chat_completion_export_domain.Id(root=uuid.uuid4())
        chat_completion_export_ids = [chat_completion_export_id]
        chat_completion_exports = [
            self.dummy_chat_completion_export(chat_completion_export_id, user_id, bot_id, api_key_id)
        ]
        self.chat_completion_usecase.chat_completion_export_repo.delete_by_ids_and_tenant_id = Mock(return_value=None)
        self.chat_completion_usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.chat_completion_usecase.chat_completion_export_repo.find_by_ids_and_tenant_id = Mock(
            return_value=chat_completion_exports
        )
        self.chat_completion_usecase.blob_storage_service.delete_blob_export = Mock(return_value=None)

        # Call the method
        self.chat_completion_usecase.delete_chat_completion_exports(tenant_id, chat_completion_export_ids)

        # Assertions
        self.chat_completion_usecase.chat_completion_export_repo.delete_by_ids_and_tenant_id.assert_called_once_with(
            tenant_id, chat_completion_export_ids
        )
        self.chat_completion_usecase.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.chat_completion_usecase.chat_completion_export_repo.find_by_ids_and_tenant_id.assert_called()
        self.chat_completion_usecase.blob_storage_service.delete_blob_export.assert_called()

    def test_creat_chat_completion_exports(self, setup):
        # Given
        chat_completion_export_create = chat_completion_export_domain.ChatCompletionExportForCreate(
            creator_id=user_domain.Id(value=1),
            start_date_time=chat_completion_export_domain.StartDateTime(root=datetime.now(timezone.utc)),
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.now(timezone.utc)),
            target_api_key_id=api_key_domain.Id(root=uuid.uuid4()),
            target_bot_id=bot_domain.Id(value=1),
        )
        chat_completion_export_id = chat_completion_export_domain.Id(root=uuid.uuid4())
        chat_completion_export = self.dummy_chat_completion_export(
            id=chat_completion_export_id,
            creator_id=chat_completion_export_create.creator_id,
            bot_id=chat_completion_export_create.target_bot_id,
            api_key_id=chat_completion_export_create.target_api_key_id,
        )
        self.chat_completion_usecase.chat_completion_export_repo.create = Mock(return_value=chat_completion_export)
        self.chat_completion_usecase._get_bot_with_api_keys_list = Mock(return_value=None)
        self.chat_completion_usecase.queue_storage_service.send_message_to_create_chat_completion_export_queue = Mock(
            return_value=None
        )

        # Call the method
        self.chat_completion_usecase.create_chat_completion_export(
            tenant_id=tenant_domain.Id(value=1), chat_completion_export_for_create=chat_completion_export_create
        )

        # Assertions
        self.chat_completion_export_repo.create.assert_called_once_with(chat_completion_export_create)
        self.chat_completion_usecase._get_bot_with_api_keys_list.assert_called()
        self.chat_completion_usecase.queue_storage_service.send_message_to_create_chat_completion_export_queue.assert_called()

    def test_get_chat_completion_export_signed_url(self, setup):
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant_name"),
            index_name=IndexName(root="tenant-index-name"),
            container_name=ContainerName(root="test-container"),
        )
        chat_completion_export_id = chat_completion_export_domain.Id(
            root=uuid.UUID("00000000-0000-0000-0000-000000000000")
        )
        chat_completion_export = chat_completion_export_domain.ChatCompletionExport(
            id=chat_completion_export_id,
            status=chat_completion_export_domain.Status.PROCESSING,
            creator_id=user_domain.Id(value=1),
            start_date_time=chat_completion_export_domain.StartDateTime(root=datetime.now(timezone.utc)),
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.now(timezone.utc)),
            target_api_key_id=api_key_domain.Id(root=uuid.uuid4()),
            target_bot_id=bot_domain.Id(value=1),
        )
        signed_url = chat_completion_export_domain.SignedUrl(
            root="https://test-signed-url.com",
        )

        self.chat_completion_usecase.chat_completion_export_repo.find_by_id = Mock(return_value=chat_completion_export)
        self.chat_completion_usecase.blob_storage_service.create_blob_chat_completion_sas_url = Mock(
            return_value=signed_url
        )

        result = self.chat_completion_usecase.get_chat_completion_export_signed_url(
            tenant=tenant, chat_completion_export_id=chat_completion_export_id
        )

        assert result == signed_url
        self.chat_completion_usecase.chat_completion_export_repo.find_by_id.assert_called_once_with(
            tenant_id=tenant.id, id=chat_completion_export_id
        )
        self.chat_completion_usecase.blob_storage_service.create_blob_chat_completion_sas_url.assert_called_once_with(
            container_name=tenant.container_name, blob_path=chat_completion_export.blob_path
        )

    def test_update_chat_completion_feedback_evaluation(self, setup, mock_create_chat_completion_id):
        # Given
        chat_completion_id = Id(root=mock_create_chat_completion_id.return_value)
        evaluation = Evaluation(value="good")
        self.chat_completion_usecase.chat_completion_repo.update_chat_completion_feedback_evaluation = Mock(
            return_value=None
        )

        # Call the method
        self.chat_completion_usecase.update_chat_completion_feedback_evaluation(
            UpdateChatCompletionFeedbackEvaluationInput(
                id=chat_completion_id,
                evaluation=evaluation,
            )
        )

        # Assertions
        self.chat_completion_usecase.chat_completion_repo.update_chat_completion_feedback_evaluation.assert_called_once_with(
            id=chat_completion_id, evaluation=evaluation
        )

    def test_update_chat_completion_feedback_comment(self, setup, mock_create_chat_completion_id):
        # Given
        chat_completion_id = Id(root=mock_create_chat_completion_id.return_value)
        comment = Comment(root="comment")
        self.chat_completion_usecase.chat_completion_repo.update_chat_completion_feedback_comment = Mock(
            return_value=None
        )

        # Call the method
        self.chat_completion_usecase.update_chat_completion_feedback_comment(
            UpdateChatCompletionFeedbackCommentInput(
                id=chat_completion_id,
                comment=comment,
            )
        )

        # Assertions
        self.chat_completion_usecase.chat_completion_repo.update_chat_completion_feedback_comment.assert_called_once_with(
            id=chat_completion_id, comment=comment
        )
