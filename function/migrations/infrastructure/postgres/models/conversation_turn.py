from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ARRAY, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import TEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .conversation import Conversation


class ConversationTurn(BaseModel):
    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    user_input: Mapped[str] = mapped_column(TEXT)
    bot_output: Mapped[str] = mapped_column(TEXT)
    queries: Mapped[list[str]] = mapped_column(ARRAY(String(255)))
    query_input_token: Mapped[int] = mapped_column(Integer)
    query_output_token: Mapped[int] = mapped_column(Integer)
    response_input_token: Mapped[int] = mapped_column(Integer)
    response_output_token: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[float] = mapped_column(Float)
    query_generator_model: Mapped[str] = mapped_column(String(255))
    response_generator_model: Mapped[str] = mapped_column(String(255))
    feedback: Mapped[str | None] = mapped_column(String(255), nullable=True)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="conversation_turns",
    )
