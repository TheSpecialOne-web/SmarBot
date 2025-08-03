from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion_export as chat_completion_export_domain,
    user as user_domain,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class ChatCompletionExport(BaseModel):
    __tablename__ = "chat_completion_exports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(
        Enum("processing", "active", "deleted", "error", name="chat_completion_export_status"),
        nullable=False,
        server_default="processing",
    )
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    start_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    target_bot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("bots.id"), nullable=True)
    target_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="chat_completion_exports")

    @classmethod
    def from_domain(
        cls,
        chat_completion_export: chat_completion_export_domain.ChatCompletionExportForCreate,
    ):
        return cls(
            creator_id=chat_completion_export.creator_id.value,
            start_date_time=chat_completion_export.start_date_time.root,
            end_date_time=chat_completion_export.end_date_time.root,
            target_bot_id=(
                chat_completion_export.target_bot_id.value
                if chat_completion_export.target_bot_id is not None
                else None
            ),
            target_api_key_id=(
                chat_completion_export.target_api_key_id.root
                if chat_completion_export.target_api_key_id is not None
                else None
            ),
        )

    def to_domain(self) -> chat_completion_export_domain.ChatCompletionExport:
        return chat_completion_export_domain.ChatCompletionExport(
            id=chat_completion_export_domain.Id(root=self.id),
            status=chat_completion_export_domain.Status(self.status),
            creator_id=user_domain.Id(value=self.creator_id),
            start_date_time=chat_completion_export_domain.StartDateTime(root=self.start_date_time),
            end_date_time=chat_completion_export_domain.EndDateTime(root=self.end_date_time),
            target_bot_id=bot_domain.Id(value=self.target_bot_id) if self.target_bot_id is not None else None,
            target_api_key_id=(
                api_key_domain.Id(root=self.target_api_key_id) if self.target_api_key_id is not None else None
            ),
        )

    def to_domain_with_user(self) -> chat_completion_export_domain.ChatCompletionExportWithUser:
        chat_completion_export = self.to_domain()
        return chat_completion_export_domain.ChatCompletionExportWithUser(
            id=chat_completion_export.id,
            creator=self.creator.to_domain(),
            status=chat_completion_export.status,
            created_at=chat_completion_export_domain.CreatedAt(root=self.created_at),
        )
