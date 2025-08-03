from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.domain.models import tenant as tenant_domain
from api.domain.models.tenant import tenant_alert as tenant_alert_domain
from api.libs.exceptions import NotFound

from .models.tenant_alert import TenantAlert as TenantAlertModel


class TenantAlertRepository(tenant_alert_domain.ITenantAlertRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_tenant_id(self, tenant_id: tenant_domain.Id) -> tenant_alert_domain.TenantAlert:
        tenant_alerts = (
            self.session.execute(select(TenantAlertModel).where(TenantAlertModel.tenant_id == tenant_id.value))
            .scalars()
            .first()
        )

        if tenant_alerts is None:
            raise NotFound(f"TenantAlert not found. tenant_id: {tenant_id.value}")

        return tenant_alerts.to_domain()

    def create(
        self,
        tenant_alert: tenant_alert_domain.TenantAlert,
    ) -> None:
        postgres_tenant_alert = TenantAlertModel.from_domain(tenant_alert)

        try:
            self.session.add(postgres_tenant_alert)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update(
        self,
        tenant_alert: tenant_alert_domain.TenantAlert,
    ) -> None:
        postgres_tenant_alert = TenantAlertModel.from_domain(tenant_alert)

        try:
            self.session.execute(
                update(TenantAlertModel)
                .where(TenantAlertModel.tenant_id == postgres_tenant_alert.tenant_id)
                .values(
                    last_token_alerted_at=postgres_tenant_alert.last_token_alerted_at,
                    last_token_alerted_threshold=postgres_tenant_alert.last_token_alerted_threshold,
                    last_storage_alerted_at=postgres_tenant_alert.last_storage_alerted_at,
                    last_storage_alerted_threshold=postgres_tenant_alert.last_storage_alerted_threshold,
                    # TODO: DELETE OCR
                    last_ocr_alerted_at=postgres_tenant_alert.last_ocr_alerted_at,
                    last_ocr_alerted_threshold=postgres_tenant_alert.last_ocr_alerted_threshold,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
