from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.domain.models import tenant as tenant_domain
from api.domain.models.tenant import (
    external_data_connection as external_data_connection_domain,
    guideline as guideline_domain,
)
from api.domain.models.tenant.statistics import UserCount
from api.domain.models.tenant.usage_limit import UsageLimit
from api.infrastructures.postgres.models.external_data_connection import ExternalDataConnection
from api.libs.exceptions import NotFound

from .models.guideline import Guideline
from .models.tenant import Tenant
from .models.user import User


class TenantRepository(tenant_domain.ITenantRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, tenant_for_create: tenant_domain.TenantForCreate) -> tenant_domain.Tenant:
        tenant = Tenant.from_domain(
            domain_model=tenant_for_create,
        )
        self.session.add(tenant)
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return tenant.to_domain()

    def find_by_id(self, id: tenant_domain.Id) -> tenant_domain.Tenant:
        tenant = self.session.execute(select(Tenant).filter_by(id=id.value)).scalars().first()
        if not tenant:
            raise NotFound("テナントが見つかりませんでした。")
        return tenant.to_domain()

    def find_by_alias(self, alias: tenant_domain.Alias) -> tenant_domain.Tenant:
        tenant = self.session.execute(select(Tenant).filter_by(alias=alias.root)).scalars().first()
        if not tenant:
            raise NotFound("テナントが見つかりませんでした。")
        return tenant.to_domain()

    def find_all(self) -> list[tenant_domain.Tenant]:
        tenants = self.session.execute(select(Tenant)).scalars().all()
        return [tenant.to_domain() for tenant in tenants]

    def update(self, tenant: tenant_domain.Tenant) -> None:
        try:
            self.session.execute(
                update(Tenant)
                .where(Tenant.id == tenant.id.value)
                .values(
                    name=tenant.name.value,
                    status=tenant.status.value,
                    allowed_ips=[allowed_ip.cidr for allowed_ip in tenant.allowed_ips.root],
                    is_sensitive_masked=tenant.is_sensitive_masked.root,
                    enable_document_intelligence=tenant.enable_document_intelligence.root,
                    enable_url_scraping=tenant.enable_url_scraping.root,
                    enable_llm_document_reader=tenant.enable_llm_document_reader.root,
                    free_user_seat_limit=tenant.usage_limit.free_user_seat,
                    additional_user_seat_limit=tenant.usage_limit.additional_user_seat,
                    free_token_limit=tenant.usage_limit.free_token,
                    additional_token_limit=tenant.usage_limit.additional_token,
                    free_storage_limit=tenant.usage_limit.free_storage,
                    additional_storage_limit=tenant.usage_limit.additional_storage,
                    document_intelligence_page_limit=tenant.usage_limit.document_intelligence_page,
                    logo_url=tenant.logo_url.root if tenant.logo_url is not None else None,
                    allow_foreign_region=tenant.allow_foreign_region.root,
                    additional_platforms=tenant.additional_platforms.get_values(),
                    enable_api_integrations=tenant.enable_api_integrations.root,
                    enable_basic_ai_web_browsing=tenant.enable_basic_ai_web_browsing.root,
                    basic_ai_pdf_parser=tenant.basic_ai_pdf_parser.value,
                    max_attachment_token=tenant.max_attachment_token.root,
                    allowed_model_families=[amf.value for amf in tenant.allowed_model_families],
                    basic_ai_max_conversation_turns=(
                        tenant.basic_ai_max_conversation_turns.root
                        if tenant.basic_ai_max_conversation_turns is not None
                        else None
                    ),
                    enable_external_data_integrations=tenant.enable_external_data_integrations.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, id: tenant_domain.Id) -> None:
        now = datetime.utcnow()
        tenant = self.session.execute(select(Tenant).filter_by(id=id.value)).scalars().first()
        if not tenant:
            raise NotFound("テナントが見つかりませんでした。")

        tenant.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete(self, id: tenant_domain.Id) -> None:
        try:
            self.session.execute(delete(Tenant).where(Tenant.id == id.value).where(Tenant.deleted_at.isnot(None)))
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update_masked(self, id: tenant_domain.Id, is_sensitive_masked: tenant_domain.IsSensitiveMasked) -> None:
        try:
            self.session.execute(
                update(Tenant).where(Tenant.id == id.value).values(is_sensitive_masked=is_sensitive_masked.root)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_user_count(self, id: tenant_domain.Id) -> UserCount:
        NEOAI_EMAIL_DOMAIN = "neoai.jp"
        users = self.session.execute(select(User).where(User.tenant_id == id.value)).scalars().all()
        if id == tenant_domain.NEOAI_TENANT_ID:
            return UserCount(root=len(users))

        # neoai.jpのメールアドレスはカウントしない
        not_neoai_users = [user for user in users if not user.email.endswith(NEOAI_EMAIL_DOMAIN)]
        return UserCount(root=len(not_neoai_users))

    def get_usage_limit(self, id: tenant_domain.Id) -> UsageLimit:
        tenant = self.session.execute(select(Tenant).where(Tenant.id == id.value)).scalars().first()
        if not tenant:
            raise NotFound("テナントが見つかりませんでした。")
        return UsageLimit.from_optional(
            free_user_seat=tenant.free_user_seat_limit,
            additional_user_seat=tenant.additional_user_seat_limit,
            free_token=tenant.free_token_limit,
            additional_token=tenant.additional_token_limit,
            free_storage=tenant.free_storage_limit,
            additional_storage=tenant.additional_storage_limit,
            document_intelligence_page=tenant.document_intelligence_page_limit,
        )

    def get_guidelines_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[guideline_domain.Guideline]:
        guidelines = (
            self.session.execute(select(Guideline).where(Guideline.tenant_id == tenant_id.value)).scalars().all()
        )

        return [guideline.to_domain() for guideline in guidelines]

    def get_guideline_by_tenant_id_and_filename(
        self, tenant_id: tenant_domain.Id, filename: guideline_domain.Filename
    ) -> guideline_domain.Guideline:
        guideline = self.session.execute(
            select(Guideline).where(Guideline.tenant_id == tenant_id.value).where(Guideline.filename == filename.value)
        ).scalar_one_or_none()

        if guideline is None:
            raise NotFound("ガイドラインが見つかりませんでした。")

        return guideline.to_domain()

    def create_guideline(self, guideline: guideline_domain.GuidelineForCreate) -> guideline_domain.Guideline:
        new_guideline = Guideline.from_domain(guideline=guideline)

        self.session.add(new_guideline)
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return new_guideline.to_domain()

    def get_guideline_by_id_and_tenant_id(
        self, id: guideline_domain.Id, tenant_id: tenant_domain.Id
    ) -> guideline_domain.Guideline:
        guideline = self.session.execute(
            select(Guideline).where(Guideline.id == id.value).where(Guideline.tenant_id == tenant_id.value)
        ).scalar_one_or_none()

        if guideline is None:
            raise NotFound("ガイドラインが見つかりませんでした。")

        return guideline.to_domain()

    def delete_guideline(self, id: guideline_domain.Id, tenant_id: tenant_domain.Id) -> None:
        guideline = self.session.execute(
            select(Guideline).where(Guideline.id == id.value).where(Guideline.tenant_id == tenant_id.value)
        ).scalar_one_or_none()
        if guideline is None:
            raise NotFound("ガイドラインが見つかりませんでした。")

        now = datetime.now()
        try:
            guideline.deleted_at = now
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_external_data_connections(
        self, tenant_id: tenant_domain.Id
    ) -> list[external_data_connection_domain.ExternalDataConnection]:
        data_connections = (
            self.session.execute(
                select(ExternalDataConnection).where(ExternalDataConnection.tenant_id == tenant_id.value)
            )
            .scalars()
            .all()
        )
        return [data_connection.to_domain() for data_connection in data_connections]

    def create_external_data_connection(
        self,
        external_data_connection: external_data_connection_domain.ExternalDataConnectionForCreate,
    ) -> external_data_connection_domain.ExternalDataConnection:
        new_data_connection = ExternalDataConnection.from_external_data_connection_for_create(external_data_connection)

        self.session.add(new_data_connection)
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_data_connection.to_domain()

    def get_external_data_connection_by_tenant_id_and_type(
        self,
        tenant_id: tenant_domain.Id,
        external_data_connection_type: external_data_connection_domain.ExternalDataConnectionType,
    ) -> external_data_connection_domain.ExternalDataConnection:
        data_connection = self.session.execute(
            select(ExternalDataConnection)
            .where(ExternalDataConnection.tenant_id == tenant_id.value)
            .where(ExternalDataConnection.external_type == external_data_connection_type.value)
        ).scalar_one_or_none()

        if data_connection is None:
            raise NotFound("外部データ連携情報が見つかりませんでした。")

        return data_connection.to_domain()

    def hard_delete_external_data_connection(
        self,
        tenant_id: tenant_domain.Id,
        external_data_connection_id: external_data_connection_domain.Id,
    ) -> None:
        try:
            self.session.execute(
                delete(ExternalDataConnection)
                .where(ExternalDataConnection.id == external_data_connection_id.root)
                .where(ExternalDataConnection.tenant_id == tenant_id.value)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
