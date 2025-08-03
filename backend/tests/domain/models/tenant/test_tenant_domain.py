import pytest

from api.domain.models import (
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.llm.platform import Platform
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.text_2_image_model import Text2ImageModelFamily
from api.libs.exceptions import BadRequest


class TestTenantDomain:
    def dummy_tenant(
        self,
        id: tenant_domain.Id,
        allowed_model_families: list[ModelFamily | Text2ImageModelFamily] | None = None,
        allow_foreign_region: AllowForeignRegion | None = None,
        additional_platforms: tenant_domain.AdditionalPlatformList | None = None,
    ):
        return tenant_domain.Tenant(
            id=id,
            name=tenant_domain.Name(value="Test Tenant"),
            alias=tenant_domain.Alias(root="test-tenant"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-index"),
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=allow_foreign_region
            if allow_foreign_region is not None
            else AllowForeignRegion(root=False),
            additional_platforms=additional_platforms
            if additional_platforms is not None
            else tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-tenant"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=allowed_model_families
            if allowed_model_families is not None
            else [
                ModelFamily.GPT_35_TURBO,
                ModelFamily.GPT_4,
            ],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def test_update_valid_foreign_region(self):
        """
        海外リージョンの利用をOFFにすることができる
        """
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            allow_foreign_region=AllowForeignRegion(root=True),
        )
        tenant_for_update = tenant_domain.TenantForUpdate(
            name=tenant.name,
            status=tenant.status,
            allowed_ips=tenant.allowed_ips,
            is_sensitive_masked=tenant.is_sensitive_masked,
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant.additional_platforms,
            enable_document_intelligence=tenant.enable_document_intelligence,
            enable_url_scraping=tenant.enable_url_scraping,
            enable_llm_document_reader=tenant.enable_llm_document_reader,
            usage_limit=tenant.usage_limit,
            enable_api_integrations=tenant.enable_api_integrations,
            enable_basic_ai_web_browsing=tenant.enable_basic_ai_web_browsing,
            basic_ai_pdf_parser=tenant.basic_ai_pdf_parser,
            max_attachment_token=tenant.max_attachment_token,
            enable_external_data_integrations=tenant.enable_external_data_integrations,
        )
        tenant.update(tenant_for_update)

    def test_update_invalid_foreign_region(self):
        """
        海外リージョンの利用をOFFにしようとしたが、許可モデルファミリーに海外リージョンのモデルファミリーが含まれているため削除できない
        """
        foreign_region_model_families = [mf for mf in ModelFamily if not mf.has_jp_region() and not mf.is_legacy()]
        for index, mf in enumerate(foreign_region_model_families):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                allow_foreign_region=AllowForeignRegion(root=True),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allowed_model_families=[ModelFamily.GPT_35_TURBO, ModelFamily.GPT_4, mf],
            )
            tenant_for_update = tenant_domain.TenantForUpdate(
                name=tenant.name,
                status=tenant.status,
                allowed_ips=tenant.allowed_ips,
                is_sensitive_masked=tenant.is_sensitive_masked,
                allow_foreign_region=AllowForeignRegion(root=False),
                additional_platforms=tenant.additional_platforms,
                enable_document_intelligence=tenant.enable_document_intelligence,
                enable_url_scraping=tenant.enable_url_scraping,
                enable_llm_document_reader=tenant.enable_llm_document_reader,
                usage_limit=tenant.usage_limit,
                enable_api_integrations=tenant.enable_api_integrations,
                enable_basic_ai_web_browsing=tenant.enable_basic_ai_web_browsing,
                basic_ai_pdf_parser=tenant.basic_ai_pdf_parser,
                max_attachment_token=tenant.max_attachment_token,
                enable_external_data_integrations=tenant.enable_external_data_integrations,
            )
            assert tenant.allowed_model_families == [ModelFamily.GPT_35_TURBO, ModelFamily.GPT_4, mf]
            with pytest.raises(BadRequest):
                tenant.update(tenant_for_update)

    def test_update_valid_additional_platforms(self):
        """
        GCPを削除することができる
        """
        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
        )
        tenant_for_update = tenant_domain.TenantForUpdate(
            name=tenant.name,
            status=tenant.status,
            allowed_ips=tenant.allowed_ips,
            is_sensitive_masked=tenant.is_sensitive_masked,
            allow_foreign_region=tenant.allow_foreign_region,
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([]),
            enable_document_intelligence=tenant.enable_document_intelligence,
            enable_url_scraping=tenant.enable_url_scraping,
            enable_llm_document_reader=tenant.enable_llm_document_reader,
            usage_limit=tenant.usage_limit,
            enable_api_integrations=tenant.enable_api_integrations,
            enable_basic_ai_web_browsing=tenant.enable_basic_ai_web_browsing,
            basic_ai_pdf_parser=tenant.basic_ai_pdf_parser,
            max_attachment_token=tenant.max_attachment_token,
            enable_external_data_integrations=tenant.enable_external_data_integrations,
        )
        tenant.update(tenant_for_update)

    def test_update_invalid_additional_platforms(self):
        """
        GCPを削除しようとしたが許可モデルファミリーにGCPにしかないモデルファミリーが含まれているため削除できない
        """
        gcp_model_families = [mf for mf in ModelFamily if Platform.GCP in mf.get_platforms() and not mf.is_legacy()]
        for index, mf in enumerate(gcp_model_families):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                allow_foreign_region=AllowForeignRegion(root=True),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allowed_model_families=[ModelFamily.GPT_35_TURBO, ModelFamily.GPT_4, mf],
            )
            tenant_for_update = tenant_domain.TenantForUpdate(
                name=tenant.name,
                status=tenant.status,
                allowed_ips=tenant.allowed_ips,
                is_sensitive_masked=tenant.is_sensitive_masked,
                allow_foreign_region=tenant.allow_foreign_region,
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([]),
                enable_document_intelligence=tenant.enable_document_intelligence,
                enable_url_scraping=tenant.enable_url_scraping,
                enable_llm_document_reader=tenant.enable_llm_document_reader,
                usage_limit=tenant.usage_limit,
                enable_api_integrations=tenant.enable_api_integrations,
                enable_basic_ai_web_browsing=tenant.enable_basic_ai_web_browsing,
                basic_ai_pdf_parser=tenant.basic_ai_pdf_parser,
                max_attachment_token=tenant.max_attachment_token,
                enable_external_data_integrations=tenant.enable_external_data_integrations,
            )
            assert tenant.allowed_model_families == [ModelFamily.GPT_35_TURBO, ModelFamily.GPT_4, mf]
            with pytest.raises(BadRequest):
                tenant.update(tenant_for_update)

    def test_add_valid_model_family(self):
        """
        モデルファミリーを追加することができる
        """
        is_allowed = True
        for index, mf in enumerate(ModelFamily):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allow_foreign_region=AllowForeignRegion(root=True),
                allowed_model_families=[],
            )
            if mf.is_legacy():
                with pytest.raises(BadRequest):
                    tenant.update_allowed_model_family(
                        model_family=mf, is_allowed=is_allowed, existing_bot_model_families=[]
                    )
            else:
                tenant.update_allowed_model_family(
                    model_family=mf, is_allowed=is_allowed, existing_bot_model_families=[]
                )

    def test_add_invalid_model_family_with_foreign_region_off(self):
        """
        海外のモデルファミリーを追加しようとしたが、海外フラグがOFFになっているため追加できない
        """
        is_allowed = True
        foreign_region_model_families = [mf for mf in ModelFamily if not mf.has_jp_region() and not mf.is_legacy()]
        for index, mf in enumerate(foreign_region_model_families):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allow_foreign_region=AllowForeignRegion(root=False),
                allowed_model_families=[],
            )
            with pytest.raises(BadRequest):
                tenant.update_allowed_model_family(
                    model_family=mf, is_allowed=is_allowed, existing_bot_model_families=[]
                )

    def test_add_invalid_model_family_without_gcp(self):
        """
        GCPにしかないモデルファミリーを追加しようとしたが、GCPがプラットフォームに設定されていないため追加できない
        """
        is_allowed = True
        gcp_model_families = [mf for mf in ModelFamily if Platform.GCP in mf.get_platforms() and not mf.is_legacy()]
        for index, mf in enumerate(gcp_model_families):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([]),
                allow_foreign_region=AllowForeignRegion(root=True),
                allowed_model_families=[],
            )
            with pytest.raises(BadRequest):
                tenant.update_allowed_model_family(
                    model_family=mf, is_allowed=is_allowed, existing_bot_model_families=[]
                )

    def test_delete_valid_model_family(self):
        """
        モデルファミリーを削除することができる
        """
        model_families = [mf for mf in ModelFamily if not mf.is_legacy()]
        is_allowed = False
        for index, mf in enumerate(model_families):
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allow_foreign_region=AllowForeignRegion(root=True),
                allowed_model_families=[mf],
            )
            tenant.update_allowed_model_family(model_family=mf, is_allowed=is_allowed, existing_bot_model_families=[])

    def test_delete_invalid_model_family(self):
        """
        モデルファミリーを削除しようとしたが、既存のアシスタントまたは基盤モデルがそのモデルファミリーを使用しているため削除できない
        """
        is_allowed = False
        model_families = [mf for mf in ModelFamily if not mf.is_legacy()]
        for index, mf in enumerate(model_families):
            existing_bot_model_families: list[ModelFamily | Text2ImageModelFamily] = [mf]
            tenant = self.dummy_tenant(
                id=tenant_domain.Id(value=index),
                additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
                allow_foreign_region=AllowForeignRegion(root=True),
                allowed_model_families=[mf],
            )
            with pytest.raises(BadRequest):
                tenant.update_allowed_model_family(
                    model_family=mf, is_allowed=is_allowed, existing_bot_model_families=existing_bot_model_families
                )

    def test_available_model_families_with_gcp_and_with_foreign_region(self):
        """
        海外リージョンの利用をON、GCPをプラットフォームに設定した場合に選択できるモデルファミリーを出力することができる
        """
        model_families = set()
        model_families.update([mf for mf in ModelFamily if not mf.is_legacy()])
        model_families.update(list(Text2ImageModelFamily))

        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
            allow_foreign_region=AllowForeignRegion(root=True),
            allowed_model_families=[],
        )
        assert set(tenant.available_model_families) == set(model_families)

    def test_available_model_families_with_gcp_and_without_foreign_region(self):
        """
        海外リージョンの利用をOFF、GCPをプラットフォームに設定した場合に選択できるモデルファミリーを出力することができる
        """
        model_families = set()
        model_families.update([mf for mf in ModelFamily if mf.has_jp_region() and not mf.is_legacy()])

        model_families.update([mf for mf in Text2ImageModelFamily if mf.has_jp_region()])

        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([Platform.GCP]),
            allow_foreign_region=AllowForeignRegion(root=False),
            allowed_model_families=[],
        )
        assert set(tenant.available_model_families) == set(model_families)

    def test_available_model_families_without_gcp_and_with_foreign_region(self):
        """
        海外リージョンの利用をON、GCPをプラットフォームに設定していない場合に選択できるモデルファミリーを出力することができる
        """
        model_families = set()
        model_families.update([mf for mf in ModelFamily if Platform.GCP not in mf.get_platforms()])
        model_families.update([mf for mf in Text2ImageModelFamily if Platform.GCP not in mf.get_platforms()])

        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([]),
            allow_foreign_region=AllowForeignRegion(root=True),
            allowed_model_families=[],
        )
        assert set(tenant.available_model_families) == set(model_families)

    def test_available_model_families_without_gcp_and_without_foreign_region(self):
        """
        海外リージョンの利用をOFF、GCPをプラットフォームに設定していない場合に選択できるモデルファミリーを出力することができる
        """
        model_families = set()
        model_families.update(
            [
                mf
                for mf in ModelFamily
                if Platform.GCP not in mf.get_platforms() and mf.has_jp_region() and not mf.is_legacy()
            ]
        )
        model_families.update(
            [mf for mf in Text2ImageModelFamily if Platform.GCP not in mf.get_platforms() and mf.has_jp_region()]
        )

        tenant = self.dummy_tenant(
            id=tenant_domain.Id(value=1),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values([]),
            allow_foreign_region=AllowForeignRegion(root=False),
            allowed_model_families=[],
        )
        assert set(tenant.available_model_families) == set(model_families)
