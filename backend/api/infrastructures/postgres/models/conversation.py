from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    conversation as conversation_domain,
    user as user_domain,
)

from .approach_variable import ApproachVariable
from .base import BaseModel
from .bot import Bot
from .user import User

if TYPE_CHECKING:
    from .conversation_turn import ConversationTurn


class Conversation(BaseModel):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)

    conversation_turns: Mapped[list["ConversationTurn"]] = relationship(
        "ConversationTurn",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.created_at.asc()",
    )
    bot: Mapped[Bot] = relationship("Bot", back_populates="conversations")
    user: Mapped[User] = relationship("User", back_populates="conversations")

    @classmethod
    def from_domain(
        cls,
        domain_model: conversation_domain.ConversationForCreate,
        user_id: user_domain.Id,
        bot_id: bot_domain.Id,
    ) -> "Conversation":
        return cls(
            id=domain_model.id.root,
            title=domain_model.title.root if domain_model.title else None,
            user_id=user_id.value,
            bot_id=bot_id.value,
        )

    def to_domain(self) -> conversation_domain.Conversation:
        id = conversation_domain.Id(root=self.id)
        title = conversation_domain.Title(root=self.title) if self.title else None
        user_id = user_domain.Id(value=self.user_id)
        bot_id = bot_domain.Id(value=self.bot_id)
        return conversation_domain.Conversation(
            id=id,
            title=title,
            user_id=user_id,
            bot_id=bot_id,
        )

    def to_domain_with_bot(
        self, bot_dtos: Bot, approach_variable_dtos: list[ApproachVariable]
    ) -> conversation_domain.ConversationWithBot:
        id = conversation_domain.Id(root=self.id)
        title = conversation_domain.Title(root=self.title) if self.title else None
        user_id = user_domain.Id(value=self.user_id)
        bot_id = bot_domain.Id(value=self.bot_id)
        bot = bot_dtos.to_domain(approach_variable_dtos)
        conversation_turns = [conversation_turn.to_domain() for conversation_turn in self.conversation_turns]
        return conversation_domain.ConversationWithBot(
            id=id,
            title=title,
            user_id=user_id,
            bot_id=bot_id,
            bot=bot,
            turns=conversation_turns,
        )

    def to_domain_with_attachments(self) -> conversation_domain.ConversationWithAttachments:
        id = conversation_domain.Id(root=self.id)
        title = conversation_domain.Title(root=self.title) if self.title else None
        user_id = user_domain.Id(value=self.user_id)
        bot_id = bot_domain.Id(value=self.bot_id)
        conversation_turns = [
            conversation_turn.to_domain_with_attachments() for conversation_turn in self.conversation_turns
        ]
        return conversation_domain.ConversationWithAttachments(
            id=id,
            title=title,
            user_id=user_id,
            bot_id=bot_id,
            conversation_turns=conversation_turns,
        )
