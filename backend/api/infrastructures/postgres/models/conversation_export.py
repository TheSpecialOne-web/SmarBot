from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    conversation_export as conversation_export_domain,
    user as user_domain,
)

from .base import BaseModel

if TYPE_CHECKING:
    from api.infrastructures.postgres.models.user import User


class ConversationExport(BaseModel):
    __tablename__ = "conversation_exports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(
        Enum("processing", "active", "deleted", "error", name="conversation_export_status"),
        nullable=False,
        default="processing",
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    start_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    target_bot_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bots.id"), nullable=True)
    target_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="conversation_exports")

    @classmethod
    def from_domain(
        cls,
        conversation_export: conversation_export_domain.ConversationExportForCreate,
    ):
        return cls(
            user_id=conversation_export.user_id.value,
            start_date_time=conversation_export.start_date_time.root,
            end_date_time=conversation_export.end_date_time.root,
            target_user_id=(conversation_export.target_user_id.value if conversation_export.target_user_id else None),
            target_bot_id=(conversation_export.target_bot_id.value if conversation_export.target_bot_id else None),
        )

    def to_domain(self) -> conversation_export_domain.ConversationExport:
        return conversation_export_domain.ConversationExport(
            id=conversation_export_domain.Id(root=self.id),
            status=conversation_export_domain.Status(self.status),
            user_id=user_domain.Id(value=self.user_id),
            start_date_time=conversation_export_domain.StartDateTime(root=self.start_date_time),
            end_date_time=conversation_export_domain.EndDateTime(root=self.end_date_time),
            target_bot_id=bot_domain.Id(value=self.target_bot_id) if self.target_bot_id is not None else None,
            target_user_id=user_domain.Id(value=self.target_user_id) if self.target_user_id is not None else None,
        )

    def to_domain_with_user(self) -> conversation_export_domain.ConversationExportWithUser:
        return conversation_export_domain.ConversationExportWithUser(
            id=conversation_export_domain.Id(root=self.id),
            user=self.user.to_domain(),
            status=conversation_export_domain.Status(self.status),
            created_at=conversation_export_domain.CreateAt(root=self.created_at),
        )
