from abc import ABC, abstractmethod
from datetime import datetime

from injector import inject
from pydantic import BaseModel

from api.domain.models.api_key import IApiKeyRepository
from api.domain.models.bot import (
    IBotRepository,
    Id as BotId,
)
from api.domain.models.chat_completion import IChatCompletionRepository
from api.domain.models.conversation import IConversationRepository
from api.domain.models.metering import IMeteringRepository, Quantity
from api.domain.models.statistics import (
    ApiKeyTokenCountSummary,
    BotPdfParserTokenCount,
    BotPdfParserTokenCountSummary,
    IStatisticsRepository,
    TokenCountBreakdown,
    UserTokenCountSummary,
)
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.domain.models.workflow_thread import IWorkflowThreadRepository
from api.domain.services.metabase import IMetabaseService
from api.libs.exceptions import NotFound


class TokenCountOutput(BaseModel):
    users_token_counts: UserTokenCountSummary
    api_keys_token_counts: ApiKeyTokenCountSummary
    bot_pdf_parsers_token_counts: BotPdfParserTokenCountSummary


class IStatisticsUseCase(ABC):
    @abstractmethod
    def get_token_count(
        self,
        tenant_id: TenantId,
        bot_id: BotId | None,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCountOutput:
        pass

    @abstractmethod
    def get_token_count_v2(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCountBreakdown:
        pass

    @abstractmethod
    def get_document_intelligence_page_count(
        self,
        tenant_id: TenantId,
        bot_id: BotId | None,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        pass

    @abstractmethod
    def get_tenant_usage_dashboard(self, tenant_id: TenantId, year_month: str, type: str) -> str:
        pass


class StatisticsUseCase(IStatisticsUseCase):
    @inject
    def __init__(
        self,
        statistics_repo: IStatisticsRepository,
        bot_repo: IBotRepository,
        metering_repo: IMeteringRepository,
        api_key_repo: IApiKeyRepository,
        chat_completion_repo: IChatCompletionRepository,
        conversation_repo: IConversationRepository,
        workflow_thread_repo: IWorkflowThreadRepository,
        metabase_service: IMetabaseService,
    ):
        self.statistics_repo = statistics_repo
        self.bot_repo = bot_repo
        self.metering_repo = metering_repo
        self.api_key_repo = api_key_repo
        self.conversation_repo = conversation_repo
        self.workflow_thread_repo = workflow_thread_repo
        self.chat_completion_repo = chat_completion_repo
        self.metabase_service = metabase_service

    def get_token_count_v2(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCountBreakdown:
        converasation_token_count = self.conversation_repo.get_conversation_token_count_by_tenant_id(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        api_key_token_count = self.chat_completion_repo.get_chat_completion_token_count_by_tenant_id(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        pdf_parser_token_count = self.metering_repo.get_pdf_parser_token_count_by_tenant_id(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        workflow_thread_token_count = self.workflow_thread_repo.get_workflow_thread_token_count_by_tenant_id(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        return TokenCountBreakdown(
            conversation_token_count=converasation_token_count,
            chat_completion_token_count=api_key_token_count,
            pdf_parser_token_count=pdf_parser_token_count,
            workflow_thread_token_count=workflow_thread_token_count,
        )

    def get_token_count(
        self,
        tenant_id: TenantId,
        bot_id: BotId | None,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCountOutput:
        tenant_bot_ids = [bot.id for bot in self.bot_repo.find_all_by_tenant_id(tenant_id, include_deleted=True)]

        if bot_id is not None and bot_id not in tenant_bot_ids:
            raise NotFound(f"基盤モデルまたはアシスタント {bot_id} がテナント {tenant_id} に存在しません。")

        bot_ids = [bot_id] if bot_id is not None else tenant_bot_ids

        # user token count
        user_token_counts = self.statistics_repo.get_conversation_token_count(
            bot_ids=bot_ids,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        # api key token count
        api_keys = self.api_key_repo.find_by_bot_ids(bot_ids, include_deleted=True)

        if len(api_keys) == 0:
            api_key_token_counts = ApiKeyTokenCountSummary(
                total_count=TokenCount(root=0),
                api_keys_tokens=[],
            )
        else:
            api_key_token_counts = self.statistics_repo.get_chat_completion_token_count_by_api_key_ids(
                api_key_ids=[api_key.id for api_key in api_keys],
                start_date_time=start_date_time,
                end_date_time=end_date_time,
            )

        # bot pdf parser token count
        bot_pdf_parsers_page_counts = self.metering_repo.get_bot_pdf_parser_page_count(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
            bot_id=bot_id,
        )

        bot_pdf_parsers_token_counts = [
            BotPdfParserTokenCount.from_bot_pdf_parser_page_count(bot_pdf_parsers_page_count)
            for bot_pdf_parsers_page_count in bot_pdf_parsers_page_counts
        ]

        return TokenCountOutput(
            users_token_counts=user_token_counts,
            api_keys_token_counts=api_key_token_counts,
            bot_pdf_parsers_token_counts=BotPdfParserTokenCountSummary.from_list_bot_pdf_parser_token_count(
                bot_pdf_parsers_token_counts
            ),
        )

    def get_document_intelligence_page_count(
        self,
        tenant_id: TenantId,
        bot_id: BotId | None,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        if bot_id is not None:
            return self.metering_repo.get_document_intelligence_page_count_by_bot_id(
                tenant_id=tenant_id,
                bot_id=bot_id,
                start_date_time=start_date_time,
                end_date_time=end_date_time,
            )
        return self.metering_repo.get_document_intelligence_page_count(
            tenant_id=tenant_id,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

    def get_tenant_usage_dashboard(
        self,
        tenant_id: TenantId,
        year_month: str,
        type: str,
    ) -> str:
        return self.metabase_service.find_tenant_usage_dashboard(tenant_id, year_month, type)
