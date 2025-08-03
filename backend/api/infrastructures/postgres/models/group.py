from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    group as group_domain,
    tenant as tenant_domain,
)

from .base import BaseModel
from .bot import Bot
from .user_group import UserGroup
from .workflow import Workflow


# Groupモデルの更新
class Group(BaseModel):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    is_general: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    tenant = relationship(
        "Tenant",
        back_populates="groups",
    )

    bots: Mapped[list[Bot]] = relationship("Bot", back_populates="group")

    group_users: Mapped[list[UserGroup]] = relationship("UserGroup", back_populates="group")
    workflows: Mapped[list[Workflow]] = relationship("Workflow", back_populates="group")

    @classmethod
    def from_domain(
        cls, name: group_domain.Name, tenant_id: tenant_domain.Id, is_general: group_domain.IsGeneral
    ) -> "Group":
        return cls(
            name=name.value,
            tenant_id=tenant_id.value,
            is_general=is_general.root,
        )

    def to_domain(self) -> group_domain.Group:
        id = group_domain.Id(value=self.id)
        name = group_domain.Name(value=self.name)
        created_at = group_domain.CreatedAt(value=self.created_at)
        is_general = group_domain.IsGeneral(root=self.is_general)

        return group_domain.Group(
            id=id,
            name=name,
            created_at=created_at,
            is_general=is_general,
        )
