from datetime import datetime, timedelta
from unittest.mock import MagicMock
import uuid

import pytest

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.infrastructures.blob_storage.blob_storage import IBlobStorageService
from api.infrastructures.queue_storage.queue_storage import IQueueStorageService
from api.usecase.job.delete_attachments import DeleteAttachmentUseCase


class TestJobDeleteAttachmentUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = MagicMock(spec=bot_domain.IBotRepository)
        self.attachment_repo_mock = MagicMock(spec=attachment_domain.IAttachmentRepository)
        self.blob_storage_service_mock = MagicMock(spec=IBlobStorageService)
        self.queue_storage_service = MagicMock(spec=IQueueStorageService)

        self.use_case = DeleteAttachmentUseCase(
            self.tenant_repo_mock,
            self.bot_repo_mock,
            self.attachment_repo_mock,
            self.blob_storage_service_mock,
            self.queue_storage_service,
        )

    def test_delete_attachment_success(self, setup):
        # Mock data
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )
        bot_ids = [
            bot_domain.Bot(
                id=bot_id,
                group_id=group_domain.Id(value=1),
                name=bot_domain.Name(value="Test Bot"),
                description=bot_domain.Description(value="This is a test bot."),
                created_at=bot_domain.CreatedAt(root=datetime.now()),
                index_name=None,
                container_name=ContainerName(root="test-container"),
                approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
                pdf_parser=llm_domain.PdfParser.PYPDF,
                example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                search_method=None,
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                approach_variables=[],
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                status=bot_domain.Status.ACTIVE,
                icon_url=None,
                icon_color=bot_domain.IconColor(root="#AA68FF"),
                endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
                max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            )
        ]
        attachments = [
            attachment_domain.Attachment(
                id=attachment_domain.Id(root=uuid.uuid4()),
                name=attachment_domain.Name(root="test1"),
                file_extension=attachment_domain.FileExtension.PDF,
                created_at=attachment_domain.CreatedAt(root=datetime.now() - timedelta(hours=25)),
                is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
            )
        ]

        # Set up mock behavior
        self.tenant_repo_mock.find_by_id.return_value = tenant
        self.bot_repo_mock.find_all_by_tenant_id.return_value = bot_ids
        self.attachment_repo_mock.get_attachments_by_bot_id_after_24_hours.return_value = attachments
        self.blob_storage_service_mock.delete_attachment_blob.return_value = None
        self.attachment_repo_mock.update_blob_deleted.return_value = None

        # Call the method
        self.use_case.delete_attachments(tenant_id)

        # Assertions
        self.tenant_repo_mock.find_by_id.assert_called_once_with(tenant_id)
        self.bot_repo_mock.find_all_by_tenant_id.assert_called_once_with(tenant_id)
        self.blob_storage_service_mock.delete_attachment_blob.assert_called_with(
            container_name=tenant.container_name, bot_id=bot_ids[0].id, blob_name=attachments[0].blob_name
        )
        self.attachment_repo_mock.update_blob_deleted.assert_called_once_with(attachments[0].id)
