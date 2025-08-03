import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import (
    bot_template as bot_template_domain,
    common_document_template as cdt_domain,
)

from .base import BaseModel


class CommonDocumentTemplate(BaseModel):
    __tablename__ = "common_document_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bot_templates.id"), nullable=False
    )
    basename: Mapped[str] = mapped_column(String(255), nullable=False)
    memo: Mapped[str] = mapped_column(Text, nullable=True)
    file_extension: Mapped[str] = mapped_column(String(511), nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: cdt_domain.CommonDocumentTemplateForCreate,
        bot_template_id: bot_template_domain.Id,
    ) -> "CommonDocumentTemplate":
        return cls(
            id=domain_model.id.root,
            bot_template_id=bot_template_id.root,
            basename=domain_model.basename.root,
            memo=domain_model.memo.root if domain_model.memo else None,
            file_extension=domain_model.file_extension.value,
        )

    def to_domain(self) -> cdt_domain.CommonDocumentTemplate:
        return cdt_domain.CommonDocumentTemplate(
            id=cdt_domain.Id(root=self.id),
            basename=cdt_domain.Basename(root=self.basename),
            memo=cdt_domain.Memo(root=self.memo) if self.memo else None,
            file_extension=cdt_domain.FileExtension(self.file_extension),
            created_at=cdt_domain.CreatedAt(root=self.created_at),
        )
