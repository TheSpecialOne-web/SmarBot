from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    user as user_domain,
)
from api.domain.models.tenant import external_data_connection as external_data_connection_domain

from .base import BaseModel

if TYPE_CHECKING:
    from .conversation_data_point import ConversationDataPoint
    from .document_folder import DocumentFolder
    from .user_document import UserDocument


class Document(BaseModel):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    basename: Mapped[str] = mapped_column(String(255), nullable=False)
    memo: Mapped[str] = mapped_column(String(511), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="pending")
    storage_usage: Mapped[int] = mapped_column(BigInteger, nullable=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    document_folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_folders.id"), nullable=False
    )

    # columns for external data integrations
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    bot = relationship("Bot", back_populates="documents")
    users: Mapped[list["UserDocument"]] = relationship(
        "UserDocument",
        back_populates="document",
    )
    conversation_data_points: Mapped[list["ConversationDataPoint"]] = relationship(
        "ConversationDataPoint",
        back_populates="document",
    )

    document_folder: Mapped["DocumentFolder"] = relationship("DocumentFolder", back_populates="documents")

    @classmethod
    def from_domain(
        cls,
        domain_model: document_domain.DocumentForCreate,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
    ) -> "Document":
        return cls(
            bot_id=bot_id.value,
            basename=domain_model.name.value,
            memo=domain_model.memo.value if domain_model.memo else None,
            file_extension=domain_model.file_extension.value,
            status=domain_model.status.value,
            creator_id=domain_model.creator_id.value if domain_model.creator_id else None,
            document_folder_id=document_folder_id.root,
        )

    @classmethod
    def from_external_domain(
        cls,
        domain_model: document_domain.ExternalDocumentForCreate,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
    ) -> "Document":
        return cls(
            bot_id=bot_id.value,
            basename=domain_model.name.value,
            memo=domain_model.memo.value if domain_model.memo else None,
            file_extension=domain_model.file_extension.value,
            status=domain_model.status.value,
            creator_id=domain_model.creator_id.value if domain_model.creator_id else None,
            document_folder_id=document_folder_id.root,
            external_id=domain_model.external_id.root,
            external_updated_at=domain_model.external_updated_at.root,
        )

    def to_domain(self) -> document_domain.Document:
        id = document_domain.Id(value=self.id)
        name = document_domain.Name(value=self.basename)
        memo = document_domain.Memo(value=self.memo) if self.memo else None
        created_at = document_domain.CreatedAt(value=self.created_at)
        file_extension = document_domain.FileExtension(self.file_extension)
        status = document_domain.Status(self.status)
        storage_usage = (
            document_domain.StorageUsage(root=self.storage_usage) if self.storage_usage is not None else None
        )
        document_folder_id = document_folder_domain.Id(root=self.document_folder_id)
        creator_id = user_domain.Id(value=self.creator_id) if self.creator_id is not None else None
        external_id = external_data_connection_domain.ExternalId(root=self.external_id) if self.external_id else None
        external_updated_at = (
            external_data_connection_domain.ExternalUpdatedAt(root=self.external_updated_at)
            if self.external_updated_at
            else None
        )
        return document_domain.Document(
            id=id,
            name=name,
            memo=memo,
            created_at=created_at,
            file_extension=file_extension,
            status=status,
            storage_usage=storage_usage,
            document_folder_id=document_folder_id,
            creator_id=creator_id,
            external_id=external_id,
            external_updated_at=external_updated_at,
        )
