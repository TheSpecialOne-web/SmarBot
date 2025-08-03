from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .bot import Bot
    from .conversation_turn import ConversationTurn


class Conversation(BaseModel):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)

    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="conversations",
    )

    conversation_turns: Mapped[list["ConversationTurn"]] = relationship(
        "ConversationTurn",
        back_populates="conversation",
    )
