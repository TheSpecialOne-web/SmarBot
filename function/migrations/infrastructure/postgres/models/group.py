from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user_group import UserGroup

if TYPE_CHECKING:
    from .bot import Bot
    from .tenant import Tenant


# Groupモデルの更新
class Group(BaseModel):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    is_general: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="groups")
    bots: Mapped[list["Bot"]] = relationship(
        "Bot",
        back_populates="group",
    )
    group_users: Mapped[list["UserGroup"]] = relationship("UserGroup", back_populates="group")
