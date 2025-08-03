from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm.allow_foreign_region import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily

from .base import BaseModel
from .tenant_alert import TenantAlert

if TYPE_CHECKING:
    from .bot import Bot
    from .group import Group
    from .guideline import Guideline
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
    enable_external_data_integrations: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

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

    alerts: Mapped[list[TenantAlert]] = relationship(
        "TenantAlert",
        back_populates="tenant",
    )

    guidelines: Mapped[list["Guideline"]] = relationship(
        "Guideline",
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

    @classmethod
    def from_domain(
        cls,
        domain_model: tenant_domain.TenantForCreate,
    ) -> "Tenant":
        if domain_model.search_service_endpoint is None:
            raise Exception("search_service_endpoint is required")
        return cls(
            name=domain_model.name.value,
            alias=domain_model.alias.root,
            search_service_endpoint=domain_model.search_service_endpoint.root,
            index_name=domain_model.index_name.root,
            container_name=domain_model.container_name.root,
            allow_foreign_region=domain_model.allow_foreign_region.root,
            allowed_model_families=[model_family.value for model_family in domain_model.allowed_model_families],
            additional_platforms=domain_model.additional_platforms.get_values(),
            enable_document_intelligence=domain_model.enable_document_intelligence.root,
            basic_ai_max_conversation_turns=domain_model.basic_ai_max_conversation_turns.root,
            free_user_seat_limit=domain_model.usage_limit.free_user_seat,
            additional_user_seat_limit=domain_model.usage_limit.additional_user_seat,
            free_token_limit=domain_model.usage_limit.free_token,
            additional_token_limit=domain_model.usage_limit.additional_token,
            free_storage_limit=domain_model.usage_limit.free_storage,
            additional_storage_limit=domain_model.usage_limit.additional_storage,
            document_intelligence_page_limit=domain_model.usage_limit.document_intelligence_page,
        )

    def to_domain(self) -> tenant_domain.Tenant:
        id = tenant_domain.Id(value=self.id)
        name = tenant_domain.Name(value=self.name)
        alias = tenant_domain.Alias(root=self.alias) if self.alias is not None else tenant_domain.Alias(root="")
        status = tenant_domain.Status(self.status)
        allowed_ips = [tenant_domain.AllowedIP(cidr=ip) for ip in self.allowed_ips]
        search_service_endpoint = Endpoint(root=self.search_service_endpoint)
        index_name = IndexName(root=self.index_name) if self.index_name is not None else IndexName(root="")
        is_sensitive_masked = tenant_domain.IsSensitiveMasked(root=self.is_sensitive_masked)
        allow_foreign_region = AllowForeignRegion(root=self.allow_foreign_region)
        additional_platforms = (
            tenant_domain.AdditionalPlatformList.from_values(self.additional_platforms)
            if self.additional_platforms is not None
            else tenant_domain.AdditionalPlatformList(root=[])
        )
        enable_document_intelligence = tenant_domain.EnableDocumentIntelligence(root=self.enable_document_intelligence)
        enable_url_scraping = tenant_domain.EnableUrlScraping(root=self.enable_url_scraping)
        enable_llm_document_reader = tenant_domain.EnableLLMDocumentReader(root=self.enable_llm_document_reader)
        logo_url = tenant_domain.LogoUrl(root=self.logo_url) if self.logo_url is not None else None
        container_name = (
            ContainerName(root=self.container_name) if self.container_name is not None else ContainerName(root="")
        )
        enable_api_integrations = tenant_domain.EnableApiIntegrations(root=self.enable_api_integrations)
        enable_basic_ai_web_browsing = tenant_domain.EnableBasicAiWebBrowsing(root=self.enable_basic_ai_web_browsing)
        basic_ai_pdf_parser = llm_domain.BasicAiPdfParser(self.basic_ai_pdf_parser)
        max_attachment_token = tenant_domain.MaxAttachmentToken(root=self.max_attachment_token)
        basic_ai_max_conversation_turns = (
            tenant_domain.BasicAiMaxConversationTurns(root=self.basic_ai_max_conversation_turns)
            if self.basic_ai_max_conversation_turns is not None
            else None
        )
        enable_external_data_integrations = tenant_domain.EnableExternalDataIntegrations(
            root=self.enable_external_data_integrations
        )
        return tenant_domain.Tenant(
            id=id,
            name=name,
            alias=alias,
            status=status,
            allowed_ips=tenant_domain.AllowedIPs(root=allowed_ips),
            search_service_endpoint=search_service_endpoint,
            index_name=index_name,
            is_sensitive_masked=is_sensitive_masked,
            allow_foreign_region=allow_foreign_region,
            additional_platforms=additional_platforms,
            enable_document_intelligence=enable_document_intelligence,
            enable_url_scraping=enable_url_scraping,
            enable_llm_document_reader=enable_llm_document_reader,
            usage_limit=tenant_domain.UsageLimit.from_optional(
                free_user_seat=self.free_user_seat_limit,
                additional_user_seat=self.additional_user_seat_limit,
                free_token=self.free_token_limit,
                additional_token=self.additional_token_limit,
                free_storage=self.free_storage_limit,
                additional_storage=self.additional_storage_limit,
                document_intelligence_page=self.document_intelligence_page_limit,
            ),
            logo_url=logo_url,
            container_name=container_name,
            enable_api_integrations=enable_api_integrations,
            enable_basic_ai_web_browsing=enable_basic_ai_web_browsing,
            basic_ai_pdf_parser=basic_ai_pdf_parser,
            max_attachment_token=max_attachment_token,
            allowed_model_families=(
                [
                    (
                        Text2ImageModelFamily(model_family)
                        if model_family == Text2ImageModelFamily.DALL_E_3.value
                        else ModelFamily(model_family)
                    )
                    for model_family in self.allowed_model_families
                ]
                if self.allowed_model_families is not None
                else []
            ),
            basic_ai_max_conversation_turns=basic_ai_max_conversation_turns,
            enable_external_data_integrations=enable_external_data_integrations,
        )
