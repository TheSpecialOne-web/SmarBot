from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import notification as domain
from api.infrastructures.postgres.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(255), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: domain.NotificationForCreate,
    ) -> "Notification":
        return cls(
            id=domain_model.id.root,
            title=domain_model.title.root,
            content=domain_model.content.root,
            start_date=domain_model.start_date.root,
            end_date=domain_model.end_date.root,
            recipient_type=domain_model.recipient_type.value,
            is_archived=domain_model.is_archived.root,
        )

    def to_domain(self) -> domain.Notification:
        return domain.Notification(
            id=domain.Id(root=self.id),
            title=domain.Title(root=self.title),
            content=domain.Content(root=self.content),
            start_date=domain.StartDate(root=self.start_date),
            end_date=domain.EndDate(root=self.end_date),
            recipient_type=domain.RecipientType(self.recipient_type),
            is_archived=domain.IsArchived(root=self.is_archived),
        )
