from datetime import datetime

from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models.metering import Quantity
from api.domain.models.search import StorageUsage
from api.domain.models.tenant import tenant as tenant_domain
from api.domain.models.tenant.tenant_alert import tenant_alert as tenant_alert_domain
from api.infrastructures.postgres.models.tenant_alert import (
    TenantAlert as TenantAlertModel,
)
from api.infrastructures.postgres.tenant import TenantRepository
from api.infrastructures.postgres.tenant_alert import TenantAlertRepository

TenantAlertSeed = tenant_alert_domain.TenantAlert


class TestTenantAlertRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.tenant_repo = TenantRepository(self.session)
        self.tenant_alert_repo = TenantAlertRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_by_tenant_id(self, tenant_alert_seed: TenantAlertSeed):
        tenant_alert = tenant_alert_seed

        found_tenant_alert = self.tenant_alert_repo.find_by_tenant_id(tenant_id=tenant_alert.tenant_id)

        assert tenant_alert == found_tenant_alert

    def test_create(self):
        tenant_for_create = tenant_domain.TenantForCreate(
            name=tenant_domain.Name(value="TestTenantForTenantAlert"),
            alias=tenant_domain.Alias(root="test-tenant-alert"),
            allow_foreign_region=tenant_domain.AllowForeignRegion(root=True),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            search_service_endpoint=tenant_domain.Endpoint(root="https://test-search-service-endpoint.com"),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
        )
        new_tenant = self.tenant_repo.create(tenant_for_create)

        alerts = [
            tenant_alert_domain.Alert(
                type=tenant_alert_domain.AlertType.STORAGE,
                usage=StorageUsage(root=100),
                limit=tenant_alert_domain.Limit(root=100),
            ),
        ]
        tenant_alert = tenant_alert_domain.TenantAlert.from_alerts(
            tenant_id=new_tenant.id,
            alerts=alerts,
            datetime=datetime.now(),
        )

        self.tenant_alert_repo.create(tenant_alert)

        found_tenant_alert = self.tenant_alert_repo.find_by_tenant_id(tenant_id=new_tenant.id)
        assert tenant_alert == found_tenant_alert

    def test_update(self, tenant_alert_seed: TenantAlertSeed):
        tenant_alert = tenant_alert_seed

        alerts = [
            tenant_alert_domain.Alert(
                usage=Quantity(root=100),
                limit=tenant_alert_domain.Limit(root=100),
                type=tenant_alert_domain.AlertType.OCR,
            ),
        ]
        tenant_alert.update_by_alerts(alerts=alerts, datetime=datetime.now())

        self.tenant_alert_repo.update(tenant_alert)

        found_tenant_alert = (
            self.session.execute(
                select(TenantAlertModel).where(TenantAlertModel.tenant_id == tenant_alert.tenant_id.value)
            )
            .scalars()
            .first()
        )

        assert found_tenant_alert is not None
        assert tenant_alert == found_tenant_alert.to_domain()
