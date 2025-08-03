from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .conversation import Conversation
    from .group import Group
    from .tenant import Tenant


# Botモデルの更新
class Bot(BaseModel):
    __tablename__ = "bots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    index_name: Mapped[str] = mapped_column(String(255), nullable=True)
    container_name: Mapped[str] = mapped_column(String(255), nullable=False)
    approach: Mapped[str] = mapped_column(String(255), nullable=False)
    example_questions: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    search_method: Mapped[str] = mapped_column(String(255), nullable=True, default="default")
    query_generator_model: Mapped[str] = mapped_column(String(255), nullable=True, default="gpt-3.5-turbo")
    response_generator_model: Mapped[str] = mapped_column(String(255), nullable=True, default="gpt-3.5-turbo")
    pdf_parser: Mapped[str] = mapped_column(String(255), nullable=True, default="pypdf")
    enable_web_browsing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enable_follow_up_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)
    icon_color: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="bots")
    group: Mapped["Group"] = relationship("Group", back_populates="bots")

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="bot",
    )
