import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion, Platform
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import (
    TenantForCreate,
    external_data_connection as external_data_connection_domain,
)
from api.domain.models.tenant.statistics import UserCount
from api.infrastructures.postgres.models.external_data_connection import ExternalDataConnection
from api.infrastructures.postgres.tenant import (
    Tenant as TenantModel,
    TenantRepository,
)
from api.libs.exceptions import NotFound

TenantSeed = tenant_domain.Tenant
ExternalDataConnectionsSeed = tuple[list[external_data_connection_domain.ExternalDataConnection], tenant_domain.Id]
ExternalDataConnectionSeed = tuple[external_data_connection_domain.ExternalDataConnection, tenant_domain.Id]


class TestTenantRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.tenant_repo = TenantRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self):
        # テスト用のテナント作成データを用意
        tenant_for_create = TenantForCreate(
            name=tenant_domain.Name(value="TestTenant"),
            alias=tenant_domain.Alias(root="test-alias"),
            allow_foreign_region=AllowForeignRegion(root=True),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
        )
        new_tenant = self.tenant_repo.create(tenant_for_create)

        # 作成されたテナントが正しいか確認
        assert new_tenant == tenant_domain.Tenant(
            id=new_tenant.id,
            name=tenant_for_create.name,
            alias=tenant_for_create.alias,
            search_service_endpoint=tenant_for_create.search_service_endpoint,
            index_name=IndexName(root=tenant_for_create.alias.root),
            container_name=ContainerName(root=tenant_for_create.alias.root),
            allow_foreign_region=tenant_for_create.allow_foreign_region,
            additional_platforms=tenant_for_create.additional_platforms,
            allowed_model_families=tenant_for_create.allowed_model_families,
            enable_document_intelligence=tenant_for_create.enable_document_intelligence,
            basic_ai_max_conversation_turns=tenant_for_create.basic_ai_max_conversation_turns,
            usage_limit=tenant_for_create.usage_limit,
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        # データベースにテナントが保存されているか確認
        saved_tenant = self.tenant_repo.find_by_id(new_tenant.id)
        assert saved_tenant == new_tenant

    def test_create_with_document_intelligence_disabled(self):
        # テスト用のテナント作成データを用意
        tenant_for_create = TenantForCreate(
            name=tenant_domain.Name(value="TestTenant"),
            alias=tenant_domain.Alias(root="test-alias-2"),
            allow_foreign_region=AllowForeignRegion(root=True),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
        )
        new_tenant = self.tenant_repo.create(tenant_for_create)

        # 作成されたテナントが正しいか確認
        assert new_tenant == tenant_domain.Tenant(
            id=new_tenant.id,
            name=tenant_for_create.name,
            alias=tenant_for_create.alias,
            search_service_endpoint=tenant_for_create.search_service_endpoint,
            index_name=IndexName(root=tenant_for_create.alias.root),
            container_name=ContainerName(root=tenant_for_create.alias.root),
            allow_foreign_region=tenant_for_create.allow_foreign_region,
            additional_platforms=tenant_for_create.additional_platforms,
            allowed_model_families=tenant_for_create.allowed_model_families,
            enable_document_intelligence=tenant_for_create.enable_document_intelligence,
            basic_ai_max_conversation_turns=tenant_for_create.basic_ai_max_conversation_turns,
            usage_limit=tenant_for_create.usage_limit,
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        # データベースにテナントが保存されているか確認
        saved_tenant = self.tenant_repo.find_by_id(new_tenant.id)
        assert saved_tenant == new_tenant

    def test_find_by_id(self, tenant_seed: TenantSeed):
        # 既存のテナントIDを想定
        existing_tenant = tenant_seed
        tenant = self.tenant_repo.find_by_id(existing_tenant.id)

        assert tenant == existing_tenant

    def test_find_by_nonexistent_id(self):
        # idが存在しない
        nonexistent_tenant_id = tenant_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.tenant_repo.find_by_id(nonexistent_tenant_id)

    def test_find_all(self):
        tenants = self.tenant_repo.find_all()
        assert len(tenants) > 0

    def test_update(self, tenant_seed: TenantSeed):
        # 更新するテナントの情報を設定
        existing_tenant = tenant_seed
        updated_tenant = tenant_domain.Tenant(
            id=existing_tenant.id,
            name=tenant_domain.Name(value="UpdatedName"),
            alias=existing_tenant.alias,
            status=tenant_domain.Status("suspended"),
            allowed_ips=tenant_domain.AllowedIPs(
                root=[
                    tenant_domain.AllowedIP(cidr="0.0.0.0/24"),
                ]
            ),
            search_service_endpoint=existing_tenant.search_service_endpoint,
            index_name=existing_tenant.index_name,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(
                root=[tenant_domain.AdditionalPlatform(root=Platform.GCP)]
            ),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            logo_url=tenant_domain.LogoUrl(root="https://updated_example.com/logo.png"),
            container_name=existing_tenant.container_name,
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=tenant_seed.allowed_model_families,
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=10),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        self.tenant_repo.update(updated_tenant)

        # 更新後のテナントを取得して検証
        tenant = self.tenant_repo.find_by_id(updated_tenant.id)
        assert tenant == updated_tenant

    def test_delete(self):
        tenant_for_create = TenantForCreate(
            name=tenant_domain.Name(value="TestDeleteTenant"),
            alias=tenant_domain.Alias(root="test-delete-alias"),
            allow_foreign_region=AllowForeignRegion(root=True),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
        )
        new_tenant = self.tenant_repo.create(tenant_for_create)

        self.tenant_repo.delete(new_tenant.id)

        # 削除後にテナントが存在しないことを検証
        with pytest.raises(NotFound):
            self.tenant_repo.find_by_id(new_tenant.id)

    def test_delete_nonexistent(self):
        # IDが存在しない
        nonexistent_id = tenant_domain.Id(value=9999)
        with pytest.raises(NotFound):
            self.tenant_repo.delete(nonexistent_id)

    @pytest.mark.parametrize("tenant_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete(self, tenant_seed: TenantSeed):
        existing_tenant = tenant_seed

        self.tenant_repo.delete(existing_tenant.id)
        self.tenant_repo.hard_delete(existing_tenant.id)

        tenant = (
            self.session.execute(
                select(TenantModel)
                .where(TenantModel.id == existing_tenant.id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )
        assert tenant is None

    def test_update_masked(self, tenant_seed: TenantSeed):
        # 更新するテナントの情報を設定
        existing_tenant = tenant_seed
        is_sensitive_masked = tenant_domain.IsSensitiveMasked(root=True)

        self.tenant_repo.update_masked(existing_tenant.id, is_sensitive_masked=is_sensitive_masked)

        saved_tenant = self.tenant_repo.find_by_id(existing_tenant.id)
        assert saved_tenant.is_sensitive_masked == is_sensitive_masked

    def test_get_user_count(self, tenant_seed: TenantSeed):
        existing_tenant = tenant_seed
        user_count = self.tenant_repo.get_user_count(existing_tenant.id)
        assert user_count == UserCount(root=0)

    def test_get_usage_limit(self, tenant_seed: TenantSeed):
        existing_tenant = tenant_seed
        usage_limit = self.tenant_repo.get_usage_limit(existing_tenant.id)
        print(existing_tenant)
        assert usage_limit == tenant_domain.UsageLimit.from_optional(
            free_user_seat=50,
            additional_user_seat=0,
            free_token=5000000,
            additional_token=0,
            free_storage=5368709120,
            additional_storage=0,
            document_intelligence_page=0,
        )

    def test_get_external_data_connections(self, external_data_connection_seed: ExternalDataConnectionSeed):
        external_data_connection, tenant_id = external_data_connection_seed

        external_data_connections = self.tenant_repo.get_external_data_connections(tenant_id)
        assert external_data_connections == [external_data_connection]

    def test_create_sharepoint_connection(self, tenant_seed: TenantSeed):
        tenant = tenant_seed

        self.tenant_repo.create_external_data_connection(
            external_data_connection=external_data_connection_domain.ExternalDataConnectionForCreate(
                tenant_id=tenant.id,
                external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                decrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                    type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                    raw={
                        "client_id": "test-client-id",
                        "client_secret": "test-client-secret",
                        "tenant_id": "test-tenant-id",
                    },
                ),
            )
        )

        external_data_connection = (
            self.session.execute(
                select(ExternalDataConnection)
                .where(ExternalDataConnection.tenant_id == tenant.id.value)
                .where(
                    ExternalDataConnection.external_type
                    == external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT.value
                )
            )
            .scalars()
            .first()
        )
        assert external_data_connection is not None

    def test_create_box_connection(self, tenant_seed: TenantSeed):
        tenant = tenant_seed

        self.tenant_repo.create_external_data_connection(
            external_data_connection=external_data_connection_domain.ExternalDataConnectionForCreate(
                tenant_id=tenant.id,
                external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
                decrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                    type=external_data_connection_domain.ExternalDataConnectionType.BOX,
                    raw={
                        "client_id": "test-client-id",
                        "client_secret": "test-client-secret",
                        "enterprise_id": "test-enterprise-id",
                    },
                ),
            )
        )

        external_data_connection = (
            self.session.execute(
                select(ExternalDataConnection)
                .where(ExternalDataConnection.tenant_id == tenant.id.value)
                .where(
                    ExternalDataConnection.external_type
                    == external_data_connection_domain.ExternalDataConnectionType.BOX.value
                )
            )
            .scalars()
            .first()
        )
        assert external_data_connection is not None

    def test_get_external_data_connection_by_tenant_id_and_type(
        self, external_data_connections_seed: ExternalDataConnectionsSeed
    ):
        external_data_connections, tenant_id = external_data_connections_seed
        expected_output = external_data_connections[0]
        output = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        )

        assert output == expected_output

    @pytest.mark.parametrize("tenant_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_external_data_connection(self, external_data_connection_seed: ExternalDataConnectionSeed):
        external_data_connection, tenant_id = external_data_connection_seed

        self.tenant_repo.hard_delete_external_data_connection(tenant_id, external_data_connection.id)

        got_external_data_connection = (
            self.session.execute(
                select(ExternalDataConnection)
                .where(ExternalDataConnection.tenant_id == tenant_id.value)
                .where(
                    ExternalDataConnection.external_type
                    == external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT.value
                )
                .execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )
        assert got_external_data_connection is None
