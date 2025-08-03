from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    user as user_domain,
)

from .base import BaseModelWithoutDeletedAt

if TYPE_CHECKING:
    from .bot import Bot
    from .user import User


class UserLikedBot(BaseModelWithoutDeletedAt):
    __tablename__ = "users_liked_bots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="liked_bots")
    bot: Mapped["Bot"] = relationship("Bot", back_populates="users_liked")

    @classmethod
    def from_domain(
        cls,
        user_id: user_domain.Id,
        bot_id: bot_domain.Id,
    ) -> "UserLikedBot":
        return cls(
            id=uuid.uuid4(),
            user_id=user_id.value,
            bot_id=bot_id.value,
        )
