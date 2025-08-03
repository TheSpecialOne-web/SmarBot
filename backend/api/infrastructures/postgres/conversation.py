from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import conversation as conversation_domain
from api.domain.models.bot import (
    Id as BotId,
    Status,
)
from api.domain.models.conversation import (
    Id as ConversationId,
    conversation_turn as conversation_turn_domain,
)
from api.domain.models.conversation.conversation_data_point import (
    ConversationDataPointForCreate,
    ConversationDataPointWithTotalGood,
)
from api.domain.models.conversation.conversation_turn.conversation_turn import (
    Id as ConversationTurnId,
)
from api.domain.models.conversation.conversation_turn.feedback.evaluation import (
    Evaluation,
)
from api.domain.models.conversation.conversation_turn.turn import Turn
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.domain.models.user import Id as UserId
from api.libs.exceptions import NotFound

from .models.attachment import Attachment
from .models.bot import Bot
from .models.conversation import Conversation
from .models.conversation_data_point import ConversationDataPoint
from .models.conversation_turn import ConversationTurn
from .models.document import Document
from .models.document_folder import DocumentFolder, DocumentFolderPath
from .models.user import User
from .models.user_document import UserDocument
from .models.user_group import UserGroup


class ConversationRepository(conversation_domain.IConversationRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_with_bot_by_id_and_bot_id_and_user_id(
        self, conversation_id: ConversationId, bot_id: BotId, user_id: UserId
    ) -> conversation_domain.ConversationWithBot:
        conversation = (
            self.session.execute(
                select(Conversation)
                .join(Bot, Conversation.bot_id == Bot.id)
                .where(Bot.id == bot_id.value)
                .where(Conversation.id == conversation_id.root)
                .where(Conversation.user_id == user_id.value)
                .outerjoin(ConversationTurn, Conversation.id == ConversationTurn.conversation_id)
                .outerjoin(ConversationDataPoint, ConversationTurn.id == ConversationDataPoint.turn_id)
                .order_by(ConversationTurn.created_at.asc())
                .options(joinedload(Conversation.bot).joinedload(Bot.approach_variables))
                .options(joinedload(Conversation.conversation_turns))
            )
            .scalars()
            .first()
        )
        if not conversation:
            raise NotFound("会話履歴が見つかりませんでした。")
        return conversation.to_domain_with_bot(
            conversation.bot,
            conversation.bot.approach_variables,
        )

    def save_conversation(
        self, conversation: conversation_domain.ConversationForCreate
    ) -> conversation_domain.Conversation:
        new_conversation = Conversation.from_domain(
            domain_model=conversation,
            user_id=conversation.user_id,
            bot_id=conversation.bot_id,
        )
        try:
            self.session.add(new_conversation)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return new_conversation.to_domain()

    def save_conversation_turn(
        self,
        turn: conversation_turn_domain.ConversationTurnForCreate,
        data_points: list[ConversationDataPointForCreate],
    ) -> conversation_turn_domain.ConversationTurn:
        new_conversation_turn = ConversationTurn.from_domain(
            domain_model=turn,
        )

        try:
            self.session.add(new_conversation_turn)
            self.session.flush()

            new_data_points = [
                ConversationDataPoint.from_domain(
                    domain_model=data_point,
                    turn_id=ConversationTurnId(root=new_conversation_turn.id),
                )
                for data_point in data_points
            ]
            self.session.add_all(new_data_points)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return new_conversation_turn.to_domain()

    def find_conversation_turns_by_user_ids_bot_ids_and_date(
        self,
        user_ids: list[UserId],
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[conversation_turn_domain.ConversationTurnWithUserAndBot]:
        user_id_values = [user_id.value for user_id in user_ids]
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        conversation_turns = (
            self.session.execute(
                select(ConversationTurn)
                .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
                .where(Conversation.user_id.in_(user_id_values))
                .where(Conversation.bot_id.in_(bot_id_values))
                .where(ConversationTurn.created_at >= start_date_time)
                .where(ConversationTurn.created_at < end_date_time)
                .order_by(ConversationTurn.created_at.asc())
                .execution_options(include_deleted=True)  # join先の論理削除されたデータも取得する
            )
            .unique()
            .scalars()
            .all()
        )
        return [
            conversation_turn.to_domain_with_attachment_and_user_and_bot() for conversation_turn in conversation_turns
        ]

    def find_conversation_turns_by_user_ids_bot_ids_and_date_v2(
        self,
        user_ids: list[UserId],
        bot_ids: list[BotId],
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> list[conversation_turn_domain.ConversationTurnWithUserAndBotAndGroup]:
        user_id_values = [user_id.value for user_id in user_ids]
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        conversation_turns = (
            self.session.execute(
                select(ConversationTurn)
                .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
                .where(Conversation.user_id.in_(user_id_values))
                .where(Conversation.bot_id.in_(bot_id_values))
                .where(ConversationTurn.created_at >= start_date_time)
                .where(ConversationTurn.created_at < end_date_time)
                .options(
                    joinedload(ConversationTurn.conversation_data_points).joinedload(
                        ConversationDataPoint.question_answer
                    )
                )
                .options(
                    joinedload(ConversationTurn.conversation)
                    .joinedload(Conversation.user)
                    .joinedload(User.user_groups)
                    .joinedload(UserGroup.group)
                )
                .options(
                    joinedload(ConversationTurn.conversation_data_points)
                    .joinedload(ConversationDataPoint.document)
                    .joinedload(Document.document_folder)
                    .joinedload(DocumentFolder.ancestors)
                    .joinedload(DocumentFolderPath.descendant)
                )
                .order_by(ConversationTurn.created_at.asc())
                .execution_options(include_deleted=True)  # join先の論理削除されたデータも取得する
            )
            .unique()
            .scalars()
            .all()
        )
        return [conversation_turn.to_domain_with_user_and_bot_and_group() for conversation_turn in conversation_turns]

    def find_turns_by_id_and_bot_id(self, bot_id: BotId, conversation_id: ConversationId) -> list[Turn]:
        conversation_turns = (
            self.session.execute(
                select(ConversationTurn)
                .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
                .where(Conversation.bot_id == bot_id.value)
                .where(ConversationTurn.conversation_id == conversation_id.root)
                .order_by(ConversationTurn.created_at.asc())
            )
            .unique()
            .scalars()
            .all()
        )

        return [
            Turn(
                user=conversation_turn_domain.Message(root=conversation_turn.user_input),
                bot=conversation_turn_domain.Message(root=conversation_turn.bot_output),
            )
            for conversation_turn in conversation_turns
        ]

    def find_by_user_id(
        self,
        tenant_id: TenantId,
        user_id: UserId,
        offset: int,
        limit: int,
        bot_statuses: list[Status] | None = None,
    ) -> list[conversation_domain.Conversation]:
        conversations = (
            self.session.execute(
                select(Conversation)
                .join(Bot, Bot.id == Conversation.bot_id)
                .where(
                    Conversation.user_id == user_id.value,
                    Conversation.archived_at.is_(None),
                    Bot.tenant_id == tenant_id.value,
                    Bot.status.in_(bot_statuses if bot_statuses is not None else [Status.ACTIVE]),
                )
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )
        return [conversation.to_domain() for conversation in conversations]

    def find_by_id(
        self,
        conversation_id: ConversationId,
        user_id: UserId,
    ) -> conversation_domain.ConversationWithAttachments:
        conversation = (
            self.session.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id.root)
                .where(Conversation.user_id == user_id.value)
                .outerjoin(ConversationTurn, Conversation.id == ConversationTurn.conversation_id)
                .outerjoin(ConversationDataPoint, ConversationTurn.id == ConversationDataPoint.turn_id)
                .outerjoin(Attachment, ConversationTurn.id == Attachment.conversation_turn_id)
                .where(Conversation.archived_at.is_(None))
                .options(joinedload(Conversation.conversation_turns).joinedload(ConversationTurn.attachments))
            )
            .scalars()
            .first()
        )
        if not conversation:
            raise NotFound("会話履歴が見つかりませんでした。")
        return conversation.to_domain_with_attachments()

    # conversation の updated_at を更新する
    def update_conversation_timestamp(self, conversation_id: ConversationId) -> None:
        conversation = self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id.root)
        ).scalar()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            self.session.commit()
        else:
            raise NotFound("会話履歴が見つかりませんでした。")

    def update_conversation(
        self,
        id: ConversationId,
        user_id: UserId,
        title: Optional[conversation_domain.Title],
        is_archived: Optional[bool],
    ) -> conversation_domain.Conversation:
        conversation = self.session.execute(
            select(Conversation).where(Conversation.id == id.root).where(Conversation.user_id == user_id.value)
        ).scalar()
        if not conversation:
            raise NotFound("会話履歴が見つかりませんでした。")
        if title:
            conversation.title = title.root
        if is_archived is True:
            conversation.archived_at = datetime.utcnow()
        self.session.commit()
        return conversation.to_domain()

    def update_evaluation(
        self,
        id: ConversationId,
        turn_id: ConversationTurnId,
        evaluation: Evaluation,
    ) -> None:
        conversation_turn = self.session.execute(
            select(ConversationTurn)
            .where(ConversationTurn.id == turn_id.root)
            .join(Conversation)
            .where(Conversation.id == id.root)
        ).scalar()
        if not conversation_turn:
            raise NotFound("会話履歴が見つかりませんでした。")
        try:
            conversation_turn.evaluation = evaluation
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def save_comment(
        self,
        conversation_id: ConversationId,
        conversation_turn_id: ConversationTurnId,
        comment: conversation_turn_domain.Comment,
    ) -> None:
        conversation_turn = self.session.execute(
            select(ConversationTurn)
            .where(ConversationTurn.conversation_id == conversation_id.root)
            .where(ConversationTurn.id == conversation_turn_id.root)
        ).scalar()
        if not conversation_turn:
            raise NotFound("会話履歴が見つかりませんでした。")
        stmt = (
            update(ConversationTurn)
            .where(ConversationTurn.id == conversation_turn_id.root)
            .values(comment=comment.root)
        )
        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def save_conversation_title(self, conversation_id: ConversationId, title: conversation_domain.Title) -> None:
        conversation = self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id.root)
        ).scalar()
        if not conversation:
            raise NotFound("会話履歴が見つかりませんでした。")
        conversation.title = title.root
        self.session.commit()

    def find_data_points_with_total_good_by_user_id_and_id_and_turn_id(
        self, user_id: UserId, conversation_id: ConversationId, turn_id: ConversationTurnId
    ) -> list[ConversationDataPointWithTotalGood]:
        total_good_subquery = (
            select(func.count(UserDocument.id))
            .where(UserDocument.document_id == ConversationDataPoint.document_id)
            .where(UserDocument.evaluation == document_feedback_domain.Evaluation.GOOD)
            .correlate(ConversationDataPoint)
            .scalar_subquery()
        )

        stmt = (
            select(ConversationDataPoint, total_good_subquery)
            .where(ConversationDataPoint.turn_id == turn_id.root)
            .join(ConversationTurn, ConversationDataPoint.turn_id == ConversationTurn.id)
            .where(ConversationTurn.conversation_id == conversation_id.root)
            .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id.value)
        )

        results = self.session.execute(stmt).all()

        cdps = []
        for result in results:
            conversation_data_point: ConversationDataPoint = result[0]
            total_good: int = result[1]

            cdps.append(conversation_data_point.to_domain_with_total_good(total_good))

        return cdps

    def delete_by_bot_id(self, bot_id: BotId) -> None:
        now = datetime.now(timezone.utc)

        conversation_id_subquery = select(Conversation.id).where(Conversation.bot_id == bot_id.value).scalar_subquery()
        conversation_turn_id_subquery = (
            select(ConversationTurn.id)
            .where(ConversationTurn.conversation_id.in_(conversation_id_subquery))
            .scalar_subquery()
        )

        try:
            self.session.execute(
                update(Conversation).where(Conversation.id.in_(conversation_id_subquery)).values(deleted_at=now)
            )
            self.session.execute(
                update(ConversationTurn)
                .where(ConversationTurn.id.in_(conversation_turn_id_subquery))
                .values(deleted_at=now)
            )
            self.session.execute(
                update(ConversationDataPoint)
                .where(ConversationDataPoint.turn_id.in_(conversation_turn_id_subquery))
                .values(deleted_at=now)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_user_ids(self, user_ids: list[UserId]) -> None:
        user_id_values = [user_id.value for user_id in user_ids]
        try:
            self.session.execute(
                delete(Conversation)
                .where(Conversation.user_id.in_(user_id_values))
                .where(Conversation.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_conversation_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCount:
        stmt = (
            select(func.coalesce(func.sum(ConversationTurn.token_count), 0))
            .join(Conversation, Conversation.id == ConversationTurn.conversation_id)
            .join(Bot, Bot.id == Conversation.bot_id)
            .where(Bot.tenant_id == tenant_id.value)
            .where(ConversationTurn.created_at >= start_date_time)
            .where(ConversationTurn.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )
        result = self.session.execute(stmt).scalar_one()
        return TokenCount(root=result)
