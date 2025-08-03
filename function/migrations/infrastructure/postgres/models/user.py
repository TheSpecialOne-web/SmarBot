from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user_group import UserGroup

if TYPE_CHECKING:
    from .tenant import Tenant


class User(BaseModel):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    auth0_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")

    user_groups: Mapped[list["UserGroup"]] = relationship("UserGroup", back_populates="user")
