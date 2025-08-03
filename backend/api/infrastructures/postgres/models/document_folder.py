from datetime import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    document_folder as document_folder_domain,
)
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.tenant import external_data_connection as external_data_connection_domain

from .base import BaseModel
from .conversation_turn import ConversationTurn
from .document import Document
from .document_folder_path import DocumentFolderPath


class DocumentFolder(BaseModel):
    __tablename__ = "document_folders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # columns for external data integrations
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_type: Mapped[str | None] = mapped_column(
        Enum("sharepoint", "box", "google_drive"), name="external_type", nullable=True
    )
    external_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_schedule: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_sync_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    bot = relationship("Bot", back_populates="document_folders")

    ancestors: Mapped[list[DocumentFolderPath]] = relationship(
        "DocumentFolderPath",
        foreign_keys="DocumentFolderPath.descendant_document_folder_id",
        back_populates="descendant",
    )

    descendants: Mapped[list[DocumentFolderPath]] = relationship(
        "DocumentFolderPath", foreign_keys="DocumentFolderPath.ancestor_document_folder_id", back_populates="ancestor"
    )

    conversation_turns: Mapped[list["ConversationTurn"]] = relationship(
        "ConversationTurn",
        back_populates="document_folder",
    )

    documents: Mapped[list[Document]] = relationship("Document", back_populates="document_folder")

    @classmethod
    def from_domain(
        cls,
        domain_model: (
            document_folder_domain.DocumentFolderForCreate | document_folder_domain.RootDocumentFolderForCreate
        ),
        bot_id: bot_domain.Id,
    ) -> "DocumentFolder":
        return cls(
            id=domain_model.id.root,
            bot_id=bot_id.value,
            name=domain_model.name.root if domain_model.name is not None else None,
        )

    @classmethod
    def from_external_domain(
        cls,
        domain_model: document_folder_domain.ExternalDocumentFolderForCreate,
        bot_id: bot_domain.Id,
    ) -> "DocumentFolder":
        return cls(
            id=domain_model.id.root,
            bot_id=bot_id.value,
            name=domain_model.name.root if domain_model.name is not None else None,
            external_id=domain_model.external_id.root,
            external_type=domain_model.external_type.value,
            external_updated_at=domain_model.external_updated_at.root
            if domain_model.external_updated_at is not None
            else None,
            last_synced_at=domain_model.external_updated_at.root
            if domain_model.external_updated_at is not None
            else None,
            sync_schedule=domain_model.sync_schedule.root if domain_model.sync_schedule is not None else None,
            external_sync_metadata=domain_model.external_sync_metadata.root,
        )

    def to_domain(self) -> document_folder_domain.DocumentFolder:
        id = document_folder_domain.Id(root=self.id)
        name = document_folder_domain.Name(root=self.name) if self.name else None
        created_at = document_folder_domain.CreatedAt(root=self.created_at)
        external_id = external_data_connection_domain.ExternalId(root=self.external_id) if self.external_id else None
        external_type = (
            external_data_connection_domain.ExternalDataConnectionType(self.external_type)
            if self.external_type
            else None
        )
        external_updated_at = (
            external_data_connection_domain.ExternalUpdatedAt(root=self.external_updated_at)
            if self.external_updated_at
            else None
        )
        sync_schedule = (
            external_data_connection_domain.SyncSchedule(root=self.sync_schedule) if self.sync_schedule else None
        )
        last_synced_at = (
            external_data_connection_domain.LastSyncedAt(root=self.last_synced_at) if self.last_synced_at else None
        )

        return document_folder_domain.DocumentFolder(
            id=id,
            name=name,
            created_at=created_at,
            external_id=external_id,
            external_type=external_type,
            external_updated_at=external_updated_at,
            sync_schedule=sync_schedule,
            last_synced_at=last_synced_at,
        )

    def to_domain_with_order(self, param_order: int) -> document_folder_domain.DocumentFolderWithOrder:
        id = document_folder_domain.Id(root=self.id)
        name = document_folder_domain.Name(root=self.name) if self.name else None
        created_at = document_folder_domain.CreatedAt(root=self.created_at)
        order = document_folder_domain.Order(root=param_order)
        external_id = external_data_connection_domain.ExternalId(root=self.external_id) if self.external_id else None
        external_type = (
            external_data_connection_domain.ExternalDataConnectionType(self.external_type)
            if self.external_type
            else None
        )
        external_updated_at = (
            external_data_connection_domain.ExternalUpdatedAt(root=self.external_updated_at)
            if self.external_updated_at
            else None
        )
        sync_schedule = (
            external_data_connection_domain.SyncSchedule(root=self.sync_schedule) if self.sync_schedule else None
        )
        last_synced_at = (
            external_data_connection_domain.LastSyncedAt(root=self.last_synced_at) if self.last_synced_at else None
        )
        return document_folder_domain.DocumentFolderWithOrder(
            id=id,
            name=name,
            created_at=created_at,
            external_id=external_id,
            external_type=external_type,
            external_updated_at=external_updated_at,
            sync_schedule=sync_schedule,
            last_synced_at=last_synced_at,
            order=order,
        )

    def to_external_domain(self) -> external_document_folder_domain.ExternalDocumentFolder:
        name = document_folder_domain.Name(root=self.name) if self.name else None
        external_id = external_data_connection_domain.ExternalId(root=self.external_id) if self.external_id else None
        external_type = (
            external_data_connection_domain.ExternalDataConnectionType(self.external_type)
            if self.external_type
            else None
        )
        external_updated_at = (
            external_data_connection_domain.ExternalUpdatedAt(root=self.external_updated_at)
            if self.external_updated_at
            else None
        )

        if name is None or external_id is None or external_type is None or external_updated_at is None:
            raise ValueError("ExternalDocumentFolder is missing required fields")
        return external_document_folder_domain.ExternalDocumentFolder(
            name=name,
            external_id=external_id,
            external_type=external_type,
            external_updated_at=external_updated_at,
        )
