from abc import ABC, abstractmethod
from datetime import datetime

from ..api_key import Id as ApiKeyId
from ..bot import Id as BotId
from ..tenant import Id as TenantId
from ..token import TokenCount
from .chat_completion import ChatCompletion, ChatCompletionWithApiKeyId
from .data_point import ChatCompletionDataPoint
from .feedback.comment import Comment
from .feedback.evaluation import Evaluation
from .id import Id


class IChatCompletionRepository(ABC):
    @abstractmethod
    def create(self, api_key_id: ApiKeyId, chat_completion: ChatCompletion) -> ChatCompletion:
        pass

    @abstractmethod
    def update(self, api_key_id: ApiKeyId, chat_completion: ChatCompletion) -> None:
        pass

    @abstractmethod
    def bulk_create_data_points(
        self, chat_completion_id: Id, chat_completion_data_points: list[ChatCompletionDataPoint]
    ) -> None:
        pass

    @abstractmethod
    def find_by_api_key_ids_and_date(
        self,
        api_key_ids: list[ApiKeyId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[ChatCompletionWithApiKeyId]:
        pass

    @abstractmethod
    def delete_completions_and_data_points_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_api_key_ids(self, api_key_ids: list[ApiKeyId]) -> None:
        pass

    @abstractmethod
    def update_chat_completion_feedback_evaluation(self, id: Id, evaluation: Evaluation) -> None:
        pass

    @abstractmethod
    def update_chat_completion_feedback_comment(self, id: Id, comment: Comment) -> None:
        pass

    @abstractmethod
    def get_chat_completion_token_count_by_tenant_id(
        self, tenant_id: TenantId, start_date_time: datetime, end_date_time: datetime
    ) -> TokenCount:
        pass
