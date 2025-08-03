from abc import ABC, abstractmethod
from datetime import datetime

from ..api_key import Id as ApiKeyId
from ..bot import Id as BotId
from ..tenant import Id as TenantId
from .api_key_token_count import ApiKeyTokenCountSummary
from .user_token_count import UserTokenCountSummary


class IStatisticsRepository(ABC):
    @abstractmethod
    def get_conversation_token_count(
        self,
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> UserTokenCountSummary:
        pass

    @abstractmethod
    def get_conversation_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> UserTokenCountSummary:
        pass

    @abstractmethod
    def get_chat_completion_token_count_by_api_key_ids(
        self,
        api_key_ids: list[ApiKeyId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> ApiKeyTokenCountSummary:
        pass

    @abstractmethod
    def get_chat_completion_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> ApiKeyTokenCountSummary:
        pass
