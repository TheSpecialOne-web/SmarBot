from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import user as user_domain
from api.domain.models.bot import Id as BotId
from api.domain.models.policy import (
    Action,
    Policy as PolicyDomainModel,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class UserPolicy(BaseModel):
    __tablename__ = "users_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    action: Mapped[str] = mapped_column(Enum("read", "write", name="users_policies_action"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="policies")

    @classmethod
    def from_domain(
        cls,
        domain_model: PolicyDomainModel,
        user_id: user_domain.Id,
    ) -> "UserPolicy":
        return cls(
            user_id=user_id.value,
            bot_id=domain_model.bot_id.value,
            action=domain_model.action.to_str(),
        )

    def to_domain(self) -> PolicyDomainModel:
        bot_id = BotId(value=self.bot_id)
        action = Action.from_str(self.action)
        return PolicyDomainModel(bot_id=bot_id, action=action)
