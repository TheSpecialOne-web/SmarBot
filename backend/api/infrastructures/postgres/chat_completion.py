from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    bot as bot_domain,
    chat_completion as chat_completion_domain,
)
from api.domain.models.api_key import Id as ApiKeyId
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.libs.exceptions import NotFound

from .models.api_key import ApiKey
from .models.bot import Bot
from .models.chat_completion import ChatCompletion
from .models.chat_completion_data_point import ChatCompletionDataPoint


class ChatCompletionRepository(chat_completion_domain.IChatCompletionRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        api_key_id: ApiKeyId,
        chat_completion: chat_completion_domain.ChatCompletion,
    ) -> chat_completion_domain.ChatCompletion:
        cc = ChatCompletion.from_domain(
            api_key_id=api_key_id,
            chat_completion=chat_completion,
        )
        dps = [
            ChatCompletionDataPoint.from_domain(
                chat_completion_id=chat_completion.id,
                chat_completion_data_point=dp,
            )
            for dp in chat_completion.data_points
        ]
        try:
            self.session.add(cc)
            self.session.flush()
            self.session.add_all(dps)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return cc.to_domain()

    def update(
        self,
        api_key_id: ApiKeyId,
        chat_completion: chat_completion_domain.ChatCompletion,
    ) -> None:
        try:
            cc = ChatCompletion.from_domain(
                api_key_id=api_key_id,
                chat_completion=chat_completion,
            )
            result = self.session.execute(
                update(ChatCompletion)
                .where(
                    ChatCompletion.api_key_id == api_key_id.root,
                    ChatCompletion.id == chat_completion.id.root,
                )
                .values(
                    messages=cc.messages,
                    answer=cc.answer,
                    token_count=cc.token_count,
                )
                .execution_options(synchronize_session="fetch")  # Ensures session syncs with DB state
            )
            if result.rowcount == 0:
                raise NotFound("Chat completion id does not exist")

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_create_data_points(
        self,
        chat_completion_id: chat_completion_domain.Id,
        chat_completion_data_points: list[chat_completion_domain.ChatCompletionDataPoint],
    ) -> None:
        dps = [
            ChatCompletionDataPoint.from_domain(
                chat_completion_id=chat_completion_id,
                chat_completion_data_point=dp,
            )
            for dp in chat_completion_data_points
        ]
        try:
            self.session.add_all(dps)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_api_key_ids_and_date(
        self,
        api_key_ids: list[ApiKeyId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[chat_completion_domain.ChatCompletionWithApiKeyId]:
        api_key_id_values = [api_key_id.root for api_key_id in api_key_ids]

        stmt = (
            select(ChatCompletion)
            .where(ChatCompletion.api_key_id.in_(api_key_id_values))
            .where(ChatCompletion.created_at >= start_date_time)
            .where(ChatCompletion.created_at < end_date_time)
            .order_by(ChatCompletion.created_at.asc())
            .execution_options(include_deleted=True)  # join先の論理削除されたデータも取得する
        )

        chat_completions = self.session.execute(stmt).unique().scalars().all()
        return [cc.to_domain_with_api_key_id() for cc in chat_completions]

    def delete_completions_and_data_points_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        completions = (
            self.session.execute(
                select(ChatCompletion)
                .join(ApiKey, ApiKey.id == ChatCompletion.api_key_id)
                .where(ApiKey.bot_id == bot_id.value)
                .options(joinedload(ChatCompletion.data_points))
            )
            .unique()
            .scalars()
            .all()
        )

        now = datetime.now()
        for completion in completions:
            completion.deleted_at = now
            for data_point in completion.data_points:
                data_point.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_api_key_ids(self, api_key_ids: list[ApiKeyId]) -> None:
        api_key_id_values = [api_key_id.root for api_key_id in api_key_ids]
        try:
            self.session.execute(
                delete(ChatCompletion)
                .where(ChatCompletion.api_key_id.in_(api_key_id_values))
                .where(ChatCompletion.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update_chat_completion_feedback_evaluation(
        self, id: chat_completion_domain.Id, evaluation: chat_completion_domain.Evaluation
    ) -> None:
        try:
            result = self.session.execute(
                update(ChatCompletion)
                .where(ChatCompletion.id == id.root)
                .values(
                    evaluation=evaluation,
                )
            )
            if result.rowcount == 0:
                raise NotFound("Chat completion id does not exist")

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update_chat_completion_feedback_comment(
        self, id: chat_completion_domain.Id, comment: chat_completion_domain.Comment
    ) -> None:
        try:
            result = self.session.execute(
                update(ChatCompletion).where(ChatCompletion.id == id.root).values(comment=comment.root)
            )
            if result.rowcount == 0:
                raise NotFound("Chat completion id does not exist")

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_chat_completion_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCount:
        stmt = (
            select(func.coalesce(func.sum(ChatCompletion.token_count), 0))
            .join(ApiKey, ApiKey.id == ChatCompletion.api_key_id)
            .join(Bot, Bot.id == ApiKey.bot_id)
            .where(Bot.tenant_id == tenant_id.value)
            .where(ChatCompletion.created_at >= start_date_time)
            .where(ChatCompletion.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )
        result = self.session.execute(stmt).scalar_one()
        return TokenCount(root=result)
