from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    group as group_domain,
    user as user_domain,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .group import Group
    from .user import User


class UserGroup(BaseModel):
    __tablename__ = "users_groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("group_viewer", "group_editor", "group_admin", name="group_role"),
        nullable=False,
        server_default="group_viewer",
    )

    user: Mapped["User"] = relationship("User", back_populates="user_groups")
    group: Mapped["Group"] = relationship("Group", back_populates="group_users")

    @classmethod
    def from_domain(
        cls, user_id: user_domain.Id, group_id: group_domain.Id, group_role: group_domain.GroupRole
    ) -> "UserGroup":
        return cls(
            user_id=user_id.value,
            group_id=group_id.value,
            role=group_role.value,
        )
