from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import tenant as tenant_domain
from api.domain.models.tenant import tenant_alert as tenant_alert_domain

from .base import BaseModel

if TYPE_CHECKING:
    from .tenant import Tenant


class TenantAlert(BaseModel):
    __tablename__ = "tenant_alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    last_token_alerted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_token_alerted_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_storage_alerted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_storage_alerted_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # TODO: delete ocr columns
    last_ocr_alerted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_ocr_alerted_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="alerts",
    )

    @classmethod
    def from_domain(cls, tenant_alert: tenant_alert_domain.TenantAlert) -> "TenantAlert":
        return cls(
            tenant_id=tenant_alert.tenant_id.value,
            last_token_alerted_at=(
                tenant_alert.last_token_alerted_at.root if tenant_alert.last_token_alerted_at else None
            ),
            last_storage_alerted_at=(
                tenant_alert.last_storage_alerted_at.root if tenant_alert.last_storage_alerted_at else None
            ),
            last_ocr_alerted_at=(tenant_alert.last_ocr_alerted_at.root if tenant_alert.last_ocr_alerted_at else None),
            last_token_alerted_threshold=(
                tenant_alert.last_token_alerted_threshold.root if tenant_alert.last_token_alerted_threshold else None
            ),
            last_storage_alerted_threshold=(
                tenant_alert.last_storage_alerted_threshold.root
                if tenant_alert.last_storage_alerted_threshold
                else None
            ),
            last_ocr_alerted_threshold=(
                tenant_alert.last_ocr_alerted_threshold.root if tenant_alert.last_ocr_alerted_threshold else None
            ),
        )

    def to_domain(self):
        return tenant_alert_domain.TenantAlert(
            tenant_id=tenant_domain.Id(value=self.tenant_id),
            last_token_alerted_at=(
                tenant_alert_domain.LastTokenAlertedAt(root=self.last_token_alerted_at)
                if self.last_token_alerted_at
                else None
            ),
            last_storage_alerted_at=(
                tenant_alert_domain.LastStorageAlertedAt(root=self.last_storage_alerted_at)
                if self.last_storage_alerted_at
                else None
            ),
            last_ocr_alerted_at=(
                tenant_alert_domain.LastOcrAlertedAt(root=self.last_ocr_alerted_at)
                if self.last_ocr_alerted_at
                else None
            ),
            last_token_alerted_threshold=(
                tenant_alert_domain.LastTokenAlertedThreshold(root=self.last_token_alerted_threshold)
                if self.last_token_alerted_threshold
                else None
            ),
            last_storage_alerted_threshold=(
                tenant_alert_domain.LastStorageAlertedThreshold(root=self.last_storage_alerted_threshold)
                if self.last_storage_alerted_threshold
                else None
            ),
            last_ocr_alerted_threshold=(
                tenant_alert_domain.LastOcrAlertedThreshold(root=self.last_ocr_alerted_threshold)
                if self.last_ocr_alerted_threshold
                else None
            ),
        )
