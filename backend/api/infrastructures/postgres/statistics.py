from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.domain.models.api_key import (
    Id as ApiKeyId,
    Name as ApiKeyName,
)
from api.domain.models.bot import Id as BotId
from api.domain.models.statistics import (
    ApiKeyTokenCount,
    ApiKeyTokenCountSummary,
    IStatisticsRepository,
    UserTokenCount,
    UserTokenCountSummary,
)
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.domain.models.user import (
    Id as UserId,
    Name as UserName,
)

from .models.api_key import ApiKey
from .models.bot import Bot
from .models.chat_completion import ChatCompletion
from .models.conversation import Conversation
from .models.conversation_turn import ConversationTurn
from .models.user import User


class StatisticsRepository(IStatisticsRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_conversation_token_count(
        self,
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> UserTokenCountSummary:
        bot_id_values = [bot_id.value for bot_id in bot_ids]

        stmt = (
            select(Conversation.user_id, User.name, func.sum(ConversationTurn.token_count))
            .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
            .join(User, User.id == Conversation.user_id)
            .where(Conversation.bot_id.in_(bot_id_values))
            .where(ConversationTurn.created_at >= start_date_time)
            .where(ConversationTurn.created_at < end_date_time)
            .group_by(Conversation.user_id, User.name)
            .order_by(func.sum(ConversationTurn.token_count).desc())
        )
        user_token_counts = self.session.execute(stmt, execution_options={"include_deleted": True}).all()

        total_token_count = sum(token_count for _, _, token_count in user_token_counts)
        return UserTokenCountSummary(
            total_count=TokenCount(root=total_token_count),
            users_tokens=[
                UserTokenCount(
                    user_id=UserId(value=user_id),
                    user_name=UserName(value=user_name),
                    token_count=TokenCount(root=token_count),
                )
                for user_id, user_name, token_count in user_token_counts
            ],
        )

    def get_conversation_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> UserTokenCountSummary:
        stmt = (
            select(Conversation.user_id, User.name, func.sum(ConversationTurn.token_count))
            .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
            .join(User, User.id == Conversation.user_id)
            .join(Bot, Bot.id == Conversation.bot_id)
            .where(Bot.tenant_id == tenant_id.value)
            .where(ConversationTurn.created_at >= start_date_time)
            .where(ConversationTurn.created_at < end_date_time)
            .group_by(Conversation.user_id, User.name)
            .order_by(func.sum(ConversationTurn.token_count).desc())
        )
        user_token_counts = self.session.execute(stmt, execution_options={"include_deleted": True}).all()

        total_token_count = sum(token_count for _, _, token_count in user_token_counts)
        return UserTokenCountSummary(
            total_count=TokenCount(root=total_token_count),
            users_tokens=[
                UserTokenCount(
                    user_id=UserId(value=user_id),
                    user_name=UserName(value=user_name),
                    token_count=TokenCount(root=token_count),
                )
                for user_id, user_name, token_count in user_token_counts
            ],
        )

    def get_chat_completion_token_count_by_api_key_ids(
        self,
        api_key_ids: list[ApiKeyId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> ApiKeyTokenCountSummary:
        api_key_id_values = [api_key_id.root for api_key_id in api_key_ids]
        stmt = (
            select(
                ChatCompletion.api_key_id,
                # ApiKey.nameでは group_byする必要ない、かつ、ApiKey.nameとApiKey.idは1対1であるため
                func.min(ApiKey.name).label("name"),
                func.sum(ChatCompletion.token_count),
            )
            .join(ApiKey, ApiKey.id == ChatCompletion.api_key_id)
            .where(ChatCompletion.api_key_id.in_(api_key_id_values))
            .where(ChatCompletion.created_at >= start_date_time)
            .where(ChatCompletion.created_at < end_date_time)
            .group_by(
                ChatCompletion.api_key_id,
            )
            .order_by(func.sum(ChatCompletion.token_count).desc())
        )
        api_key_token_counts = self.session.execute(stmt, execution_options={"include_deleted": True}).all()

        total_token_count = sum(token_count for _, _, token_count in api_key_token_counts)

        return ApiKeyTokenCountSummary(
            total_count=TokenCount(root=total_token_count),
            api_keys_tokens=[
                ApiKeyTokenCount(
                    api_key_id=api_key_id,
                    name=ApiKeyName(root=name),
                    token_count=TokenCount(root=token_count),
                )
                for api_key_id, name, token_count in api_key_token_counts
            ],
        )

    def get_chat_completion_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> ApiKeyTokenCountSummary:
        stmt = (
            select(
                ChatCompletion.api_key_id,
                # ApiKey.nameでは group_byする必要ない、かつ、ApiKey.nameとApiKey.idは1対1であるため
                func.min(ApiKey.name).label("name"),
                func.sum(ChatCompletion.token_count),
            )
            .join(ApiKey, ApiKey.id == ChatCompletion.api_key_id)
            .join(Bot, Bot.id == ApiKey.bot_id)
            .where(Bot.tenant_id == tenant_id.value)
            .where(ChatCompletion.created_at >= start_date_time)
            .where(ChatCompletion.created_at < end_date_time)
            .group_by(
                ChatCompletion.api_key_id,
            )
            .order_by(func.sum(ChatCompletion.token_count).desc())
        )
        api_key_token_counts = self.session.execute(stmt, execution_options={"include_deleted": True}).all()

        total_token_count = sum(token_count for _, _, token_count in api_key_token_counts)

        return ApiKeyTokenCountSummary(
            total_count=TokenCount(root=total_token_count),
            api_keys_tokens=[
                ApiKeyTokenCount(
                    api_key_id=api_key_id,
                    name=ApiKeyName(root=name),
                    token_count=TokenCount(root=token_count),
                )
                for api_key_id, name, token_count in api_key_token_counts
            ],
        )
