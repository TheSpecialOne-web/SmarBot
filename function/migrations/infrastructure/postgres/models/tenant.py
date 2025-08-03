from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .bot import Bot
    from .group import Group
    from .user import User


class Tenant(BaseModel):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, server_default="trial")
    allowed_ips: Mapped[list] = mapped_column(ARRAY(String(255)), nullable=False, server_default="{}")
    search_service_endpoint: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    index_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_sensitive_masked: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default="false")
    allow_foreign_region: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    additional_platforms: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=True)
    enable_document_intelligence: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default="false")
    enable_url_scraping: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    free_user_seat_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    additional_user_seat_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    free_token_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    additional_token_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    free_storage_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    additional_storage_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    document_intelligence_page_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    logo_url: Mapped[str] = mapped_column(String(255), nullable=True)
    container_name: Mapped[str] = mapped_column(String(255), nullable=True)
    enable_llm_document_reader: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default="false")
    enable_api_integrations: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    enable_basic_ai_web_browsing: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    basic_ai_pdf_parser: Mapped[str] = mapped_column(String(511), nullable=False, server_default="pypdf")
    max_attachment_token: Mapped[int] = mapped_column(Integer, nullable=False, server_default="8000")
    allowed_model_families: Mapped[list] = mapped_column(ARRAY(String(255)), nullable=False, server_default="{}")
    basic_ai_max_conversation_turns: Mapped[int | None] = mapped_column(Integer, nullable=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
    )

    bots: Mapped[list["Bot"]] = relationship(
        "Bot",
        back_populates="tenant",
    )
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        back_populates="tenant",
    )

    __table_args__ = (
        # Partial unique index on alias where deleted_at is NULL
        Index(
            "tenant_alias_unique_idx",
            "alias",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        # Partial unique index on index_name where deleted_at is NULL
        Index(
            "tenant_index_name_unique_idx",
            "index_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        # Partial unique index on container_name where deleted_at is NULL
        Index(
            "tenant_container_name_unique_idx",
            "container_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
