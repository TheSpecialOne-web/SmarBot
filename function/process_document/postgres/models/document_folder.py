import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .document_folder_path import DocumentFolderPath


class DocumentFolder(BaseModel):
    __tablename__ = "document_folders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    ancestors: Mapped[list[DocumentFolderPath]] = relationship(
        "DocumentFolderPath",
        foreign_keys="DocumentFolderPath.descendant_document_folder_id",
        back_populates="descendant",
    )

    descendants: Mapped[list[DocumentFolderPath]] = relationship(
        "DocumentFolderPath", foreign_keys="DocumentFolderPath.ancestor_document_folder_id", back_populates="ancestor"
    )
