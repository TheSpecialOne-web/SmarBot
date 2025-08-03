from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
)
from api.domain.models.api_key import (
    ApiKey,
    Id as ApiKeyId,
    Name as ApiKeyname,
)
from api.domain.models.api_key.crypt_api_key import DecryptedApiKey
from api.domain.models.bot.bot import Id as BotId
from api.domain.models.llm.model import ModelFamily
from api.domain.models.metering.bot_pdf_parser_page_count import BotPdfParserPageCount
from api.domain.models.metering.quantity import Quantity
from api.domain.models.metering.type import PDFParserCountType
from api.domain.models.search.index_name import IndexName
from api.domain.models.statistics import (
    ApiKeyTokenCount,
    ApiKeyTokenCountSummary,
    BotPdfParserTokenCount,
    BotPdfParserTokenCountSummary,
    TokenCountBreakdown,
    UserTokenCount,
    UserTokenCountSummary,
)
from api.domain.models.storage import ContainerName
from api.domain.models.tenant.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.domain.models.user import (
    Id as UserId,
    Name as UserName,
)
from api.usecase.statistics.statistics import StatisticsUseCase, TokenCountOutput


@dataclass
class TotalTokenCountOutput:
    total_token_count: TokenCount


class TestStatisticsUseCase:
    @pytest.fixture
    def setup(self):
        self.statistics_repo = Mock()
        self.metering_repo = Mock()
        self.bot_repo = Mock()
        self.api_key_repo = Mock()
        self.conversation_repo = Mock()
        self.chat_completion_repo = Mock()
        self.workflow_thread_repo = Mock()
        self.metabase_service = Mock()
        self.statistics_usecase = StatisticsUseCase(
            statistics_repo=self.statistics_repo,
            metering_repo=self.metering_repo,
            bot_repo=self.bot_repo,
            api_key_repo=self.api_key_repo,
            conversation_repo=self.conversation_repo,
            chat_completion_repo=self.chat_completion_repo,
            workflow_thread_repo=self.workflow_thread_repo,
            metabase_service=self.metabase_service,
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

    def test_get_token_count(self, setup):
        # Given
        tenant_id = TenantId(value=1)
        bot_id = BotId(value=1)
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
        dummy_bot = self.dummy_bot(bot_id)
        user_token_count1 = UserTokenCount(
            user_id=UserId(value=1), user_name=UserName(value="test1"), token_count=TokenCount(root=13)
        )
        user_token_count2 = UserTokenCount(
            user_id=UserId(value=2), user_name=UserName(value="test2"), token_count=TokenCount(root=14)
        )
        id_3 = uuid.uuid4()
        api_key_token_count_summary = ApiKeyTokenCountSummary(
            total_count=TokenCount(root=8),
            api_keys_tokens=[
                ApiKeyTokenCount(
                    api_key_id=ApiKeyId(root=id_3),
                    name=ApiKeyname(root="test3"),
                    token_count=TokenCount(root=8),
                )
            ],
        )
        bot_pdf_parsers_page_counts = [
            BotPdfParserPageCount(
                bot_id=bot_id,
                bot_name=dummy_bot.name,
                page_count=Quantity(root=385),
                count_type=PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
            )
        ]

        self.statistics_usecase.bot_repo.find_all_by_tenant_id.return_value = [dummy_bot]
        self.statistics_usecase.statistics_repo.get_conversation_token_count.return_value = UserTokenCountSummary(
            total_count=TokenCount(root=user_token_count1.token_count.root + user_token_count2.token_count.root),
            users_tokens=[user_token_count1, user_token_count2],
        )
        self.statistics_usecase.api_key_repo.find_by_bot_ids.return_value = [
            ApiKey(
                id=ApiKeyId(root=uuid.uuid4()),
                bot_id=bot_id,
                name=ApiKeyname(root="test3"),
                decrypted_api_key=DecryptedApiKey(root="test3"),
                endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
                expires_at=None,
            )
        ]
        self.statistics_usecase.statistics_repo.get_chat_completion_token_count_by_api_key_ids.return_value = (
            api_key_token_count_summary
        )
        self.statistics_usecase.metering_repo.get_bot_pdf_parser_page_count.return_value = bot_pdf_parsers_page_counts

        want = TokenCountOutput(
            users_token_counts=UserTokenCountSummary(
                total_count=TokenCount(root=user_token_count1.token_count.root + user_token_count2.token_count.root),
                users_tokens=[user_token_count1, user_token_count2],
            ),
            api_keys_token_counts=api_key_token_count_summary,
            bot_pdf_parsers_token_counts=BotPdfParserTokenCountSummary.from_list_bot_pdf_parser_token_count(
                bot_pdf_parsers_token_counts=[
                    BotPdfParserTokenCount.from_bot_pdf_parser_page_count(bot_pdf_parsers_page_count)
                    for bot_pdf_parsers_page_count in bot_pdf_parsers_page_counts
                ]
            ),
        )

        # When
        got = self.statistics_usecase.get_token_count(
            tenant_id=tenant_id,
            bot_id=bot_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        # Then
        assert got == want

    def test_get_document_intelligence_page_count(self, setup):
        # Given
        tenant_id = TenantId(value=1)
        bot_id = BotId(value=1)
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
        self.statistics_usecase.metering_repo.get_document_intelligence_page_count.return_value = Quantity(root=12)
        self.statistics_usecase.metering_repo.get_document_intelligence_page_count_by_bot_id.return_value = Quantity(
            root=12
        )

        want = Quantity(root=12)

        got = self.statistics_usecase.get_document_intelligence_page_count(
            tenant_id=tenant_id,
            bot_id=None,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        got_with_bot_id = self.statistics_usecase.get_document_intelligence_page_count(
            tenant_id=tenant_id,
            bot_id=bot_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        # Then
        assert got == want
        assert got_with_bot_id == want

    def test_get_token_count_v2(self, setup):
        # Given
        tenant_id = TenantId(value=1)
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)

        conversation_token_count = TokenCount(root=500)
        chat_completion_token_count = TokenCount(root=300)
        pdf_parser_token_count = TokenCount(root=100)
        workflow_thread_token_count = TokenCount(root=100)

        self.statistics_usecase.conversation_repo.get_conversation_token_count_by_tenant_id.return_value = (
            conversation_token_count
        )
        self.statistics_usecase.chat_completion_repo.get_chat_completion_token_count_by_tenant_id.return_value = (
            chat_completion_token_count
        )
        self.statistics_usecase.metering_repo.get_pdf_parser_token_count_by_tenant_id.return_value = (
            pdf_parser_token_count
        )
        self.statistics_usecase.workflow_thread_repo.get_workflow_thread_token_count_by_tenant_id.return_value = (
            workflow_thread_token_count
        )

        want = TokenCountBreakdown(
            conversation_token_count=conversation_token_count,
            chat_completion_token_count=chat_completion_token_count,
            pdf_parser_token_count=pdf_parser_token_count,
            workflow_thread_token_count=workflow_thread_token_count,
        )

        # When
        got = self.statistics_usecase.get_token_count_v2(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        # Then
        assert got == want

    def test_get_tenant_usage_dashboard(self, setup):
        tenant_id = TenantId(value=1)
        year_month = "2023-01"
        type = "user"

        want = "https://example.com/"

        self.statistics_usecase.metabase_service.find_tenant_usage_dashboard.return_value = "https://example.com/"
        got = self.statistics_usecase.metabase_service.find_tenant_usage_dashboard(tenant_id, year_month, type)

        assert got == want
