from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..bot import Id as BotId
from ..bot.status import Status
from ..tenant import Id as TenantId
from ..token import TokenCount
from ..user import Id as UserId
from .conversation import (
    Conversation,
    ConversationForCreate,
    ConversationTurn,
    ConversationWithAttachments,
    ConversationWithBot,
    Id as ConversationId,
    Title,
)
from .conversation_data_point import ConversationDataPointForCreate, ConversationDataPointWithTotalGood
from .conversation_turn.conversation_turn import (
    Comment,
    ConversationTurnForCreate,
    ConversationTurnWithUserAndBot,
    ConversationTurnWithUserAndBotAndGroup,
    Evaluation,
    Id as ConversationTurnId,
)
from .conversation_turn.turn import Turn


class IConversationRepository(ABC):
    @abstractmethod
    def find_with_bot_by_id_and_bot_id_and_user_id(
        self, conversation_id: ConversationId, bot_id: BotId, user_id: UserId
    ) -> ConversationWithBot:
        pass

    @abstractmethod
    def save_conversation(self, conversation: ConversationForCreate) -> Conversation:
        pass

    @abstractmethod
    def save_conversation_turn(
        self, turn: ConversationTurnForCreate, data_points: list[ConversationDataPointForCreate]
    ) -> ConversationTurn:
        pass

    @abstractmethod
    def find_conversation_turns_by_user_ids_bot_ids_and_date(
        self,
        user_ids: list[UserId],
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[ConversationTurnWithUserAndBot]:
        pass

    @abstractmethod
    def find_conversation_turns_by_user_ids_bot_ids_and_date_v2(
        self,
        user_ids: list[UserId],
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[ConversationTurnWithUserAndBotAndGroup]:
        pass

    @abstractmethod
    def find_turns_by_id_and_bot_id(self, bot_id: BotId, conversation_id: ConversationId) -> list[Turn]:
        pass

    @abstractmethod
    def find_by_user_id(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        offset: int,
        limit: int,
        bot_statuses: list[Status] | None = None,
    ) -> list[Conversation]:
        pass

    @abstractmethod
    def update_conversation_timestamp(self, conversation_id: ConversationId) -> None:
        pass

    @abstractmethod
    def find_by_id(self, conversation_id: ConversationId, user_id: UserId) -> ConversationWithAttachments:
        pass

    @abstractmethod
    def update_conversation(
        self, id: ConversationId, user_id: UserId, title: Optional[Title], is_archived: Optional[bool]
    ) -> Conversation:
        pass

    @abstractmethod
    def update_evaluation(self, id: ConversationId, turn_id: ConversationTurnId, evaluation: Evaluation) -> None:
        pass

    @abstractmethod
    def save_comment(
        self, conversation_id: ConversationId, conversation_turn_id: ConversationTurnId, comment: Comment
    ) -> None:
        pass

    @abstractmethod
    def save_conversation_title(self, conversation_id: ConversationId, title: Title) -> None:
        pass

    @abstractmethod
    def find_data_points_with_total_good_by_user_id_and_id_and_turn_id(
        self, user_id: UserId, conversation_id: ConversationId, turn_id: ConversationTurnId
    ) -> list[ConversationDataPointWithTotalGood]:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_user_ids(self, user_ids: list[UserId]) -> None:
        pass

    @abstractmethod
    def get_conversation_token_count_by_tenant_id(
        self, tenant_id: TenantId, start_date_time: datetime, end_date_time: datetime
    ) -> TokenCount:
        pass
