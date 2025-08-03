import uuid

from sqlalchemy import UUID, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models.tenant import tenant as tenant_domain
from api.domain.models.tenant.guideline import guideline as guideline_domain

from .base import BaseModel
from .tenant import Tenant


class Guideline(BaseModel):
    __tablename__ = "guidelines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)

    tenant: Mapped[Tenant] = relationship(
        "Tenant",
        back_populates="guidelines",
    )

    __table_args__ = (
        Index(
            "guidelines_tenant_id_filename_unique_idx",
            "tenant_id",
            "filename",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    def to_domain(self) -> guideline_domain.Guideline:
        return guideline_domain.Guideline(
            id=guideline_domain.Id(value=self.id),
            tenant_id=tenant_domain.Id(value=self.tenant_id),
            filename=guideline_domain.Filename.from_str(filename=self.filename),
            created_at=guideline_domain.CreatedAt(value=self.created_at),
        )

    @classmethod
    def from_domain(cls, guideline: guideline_domain.GuidelineForCreate) -> "Guideline":
        return cls(
            tenant_id=guideline.tenant_id.value,
            filename=guideline.filename.value,
        )
