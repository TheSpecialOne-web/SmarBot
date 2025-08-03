from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .document_folder import DocumentFolder


class DocumentFolderPath(BaseModel):
    __tablename__ = "document_folder_paths"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ancestor_document_folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_folders.id"), nullable=False
    )
    descendant_document_folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_folders.id"), nullable=False
    )
    path_length: Mapped[int] = mapped_column(Integer, nullable=False)

    ancestor: Mapped["DocumentFolder"] = relationship(
        "DocumentFolder", foreign_keys=[ancestor_document_folder_id], back_populates="descendants"
    )
    descendant: Mapped["DocumentFolder"] = relationship(
        "DocumentFolder", foreign_keys=[descendant_document_folder_id], back_populates="ancestors"
    )
