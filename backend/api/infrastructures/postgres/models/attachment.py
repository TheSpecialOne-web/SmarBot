import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    user as user_domain,
)

from .base import BaseModel


class Attachment(BaseModel):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_turn_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("conversation_turns.id"))
    basename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(255), nullable=False)
    is_blob_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    bot = relationship(
        "Bot",
        back_populates="attachments",
    )
    user = relationship(
        "User",
        back_populates="attachments",
    )
    conversation_turn = relationship(
        "ConversationTurn",
        back_populates="attachments",
    )

    @classmethod
    def from_domain(
        cls,
        attachment: attachment_domain.AttachmentForCreate,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
    ) -> "Attachment":
        return cls(
            id=attachment.id.root,
            basename=attachment.name.root,
            file_extension=attachment.file_extension.value,
            bot_id=bot_id.value,
            user_id=user_id.value,
        )

    def to_domain(self) -> attachment_domain.Attachment:
        id = attachment_domain.Id(root=self.id)
        name = attachment_domain.Name(root=self.basename)
        created_at = attachment_domain.CreatedAt(root=self.created_at)
        file_extension = attachment_domain.FileExtension(self.file_extension)
        is_blob_deleted = attachment_domain.IsBlobDeleted(root=self.is_blob_deleted)

        return attachment_domain.Attachment(
            id=id,
            name=name,
            created_at=created_at,
            file_extension=file_extension,
            is_blob_deleted=is_blob_deleted,
        )
