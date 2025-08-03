from datetime import datetime
from unittest.mock import ANY, Mock, call
import uuid

import pytest

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.usecase.attachment import AttachmentUseCase


class TestAttachmentUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.attachment_repo = Mock()
        self.blob_storage_service = Mock()
        self.attachment_usecase = AttachmentUseCase(
            bot_repo=self.bot_repo,
            attachment_repo=self.attachment_repo,
            blob_storage_service=self.blob_storage_service,
        )

    def dummy_tenant(
        self,
        id: tenant_domain.Id,
        basic_ai_pdf_parser: llm_domain.BasicAiPdfParser = llm_domain.BasicAiPdfParser.PYPDF,
    ):
        return tenant_domain.Tenant(
            id=id,
            name=tenant_domain.Name(value="Test Tenant"),
            alias=tenant_domain.Alias(root="test-tenant"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-index"),
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-tenant"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=basic_ai_pdf_parser,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_bot(
        self,
        id: bot_domain.Id,
        approach: bot_domain.Approach = bot_domain.Approach.NEOLLM,
        pdf_parser: llm_domain.PdfParser = llm_domain.PdfParser.PYPDF,
    ):
        return bot_domain.Bot(
            id=id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=approach,
            pdf_parser=pdf_parser,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_attachment(
        self,
        id: attachment_domain.Id | None = None,
        file_extension: attachment_domain.FileExtension = attachment_domain.FileExtension.PDF,
    ):
        return attachment_domain.Attachment(
            id=id if id is not None else attachment_domain.Id(root=uuid.uuid4()),
            name=attachment_domain.Name(root="test"),
            file_extension=file_extension,
            created_at=attachment_domain.CreatedAt(root=datetime.now()),
            is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
        )

    def test_is_pdf_parser_valid(self, setup):
        """ドキュメント読み取りオプションの有効性検証テスト"""
        cases = [
            {
                # 画像が含まれていない場合
                "tenant": self.dummy_tenant(
                    id=tenant_domain.Id(value=1),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
                ),
                "bot": self.dummy_bot(
                    id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.NEOLLM,
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                ),
                "attachments_for_create": [
                    self.dummy_attachment(file_extension=attachment_domain.FileExtension.PDF),
                ],
                "expected": True,
            },
            {
                # 画像が含まれている場合
                # 基盤モデルの場合は、テナントの設定を確認
                "tenant": self.dummy_tenant(
                    id=tenant_domain.Id(value=1),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE,
                ),
                "bot": self.dummy_bot(
                    id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
                    pdf_parser=llm_domain.PdfParser.DOCUMENT_INTELLIGENCE,
                ),
                "attachments_for_create": [
                    self.dummy_attachment(file_extension=attachment_domain.FileExtension.JPEG),
                ],
                "expected": True,
            },
            {
                # 画像が含まれている場合
                # 基盤モデルの場合は、テナントの設定を確認
                "tenant": self.dummy_tenant(
                    id=tenant_domain.Id(value=1),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
                ),
                "bot": self.dummy_bot(
                    id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
                    pdf_parser=llm_domain.PdfParser.LLM_DOCUMENT_READER,
                ),
                "attachments_for_create": [
                    self.dummy_attachment(file_extension=attachment_domain.FileExtension.JPEG),
                ],
                "expected": False,
            },
            {
                # 画像が含まれている場合
                # 基盤モデル以外の場合は、ボットの設定を確認
                "tenant": self.dummy_tenant(
                    id=tenant_domain.Id(value=1),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
                ),
                "bot": self.dummy_bot(
                    id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.NEOLLM,
                    pdf_parser=llm_domain.PdfParser.LLM_DOCUMENT_READER,
                ),
                "attachments_for_create": [
                    self.dummy_attachment(file_extension=attachment_domain.FileExtension.JPEG),
                ],
                "expected": True,
            },
            {
                # 画像が含まれている場合
                # 基盤モデル以外の場合は、ボットの設定を確認
                "tenant": self.dummy_tenant(
                    id=tenant_domain.Id(value=1),
                    basic_ai_pdf_parser=llm_domain.BasicAiPdfParser.PYPDF,
                ),
                "bot": self.dummy_bot(
                    id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.NEOLLM,
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                ),
                "attachments_for_create": [
                    self.dummy_attachment(file_extension=attachment_domain.FileExtension.JPEG),
                ],
                "expected": False,
            },
        ]
        for case in cases:
            assert (
                self.attachment_usecase._is_pdf_parser_valid(
                    case["tenant"],
                    case["bot"],
                    case["attachments_for_create"],
                )
                == case["expected"]
            )

    def test_create_attachment(self, setup):
        """アタッチメント作成テスト"""
        tenant = self.dummy_tenant(id=tenant_domain.Id(value=1))
        bot_id = bot_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        container_name = ContainerName(root="test-container")

        self.attachment_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        self.attachment_usecase.attachment_repo.create.side_effect = [
            attachment_domain.Attachment(
                id=attachment_domain.Id(root=uuid.uuid4()),
                name=attachment_domain.Name(root="test1"),
                file_extension=attachment_domain.FileExtension.PDF,
                created_at=attachment_domain.CreatedAt(root=datetime.now()),
                is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
            ),
            attachment_domain.Attachment(
                id=attachment_domain.Id(root=uuid.uuid4()),
                name=attachment_domain.Name(root="test2"),
                file_extension=attachment_domain.FileExtension.PDF,
                created_at=attachment_domain.CreatedAt(root=datetime.now()),
                is_blob_deleted=attachment_domain.IsBlobDeleted(root=False),
            ),
        ]
        self.attachment_usecase.blob_storage_service.upload_blob.return_value = None

        self.attachment_usecase.create_attachment(
            tenant=tenant,
            bot_id=bot_id,
            user_id=user_id,
            container_name=container_name,
            attachments_for_create=[
                attachment_domain.AttachmentForCreate(
                    name=attachment_domain.Name(root="test1"),
                    file_extension=attachment_domain.FileExtension(value="pdf"),
                    id=attachment_domain.Id(root=uuid.uuid4()),
                    data=b"test1",
                ),
                attachment_domain.AttachmentForCreate(
                    name=attachment_domain.Name(root="test2"),
                    file_extension=attachment_domain.FileExtension(value="pdf"),
                    id=attachment_domain.Id(root=uuid.uuid4()),
                    data=b"test2",
                ),
            ],
        )

        self.attachment_usecase.attachment_repo.create.assert_has_calls(
            [
                call(
                    bot_id,
                    user_id,
                    ANY,
                ),
            ]
        )
        self.attachment_usecase.blob_storage_service.upload_attachment.assert_has_calls(
            [
                call(
                    container_name=container_name,
                    bot_id=bot_id,
                    user_id=user_id,
                    attachment_for_create=ANY,
                ),
            ]
        )

    def test_get_attachment_signed_url(self, setup):
        tenant = self.dummy_tenant(id=tenant_domain.Id(value=1))
        bot_id = bot_domain.Id(value=1)
        attachment_id = attachment_domain.Id(root=uuid.uuid4())

        sas_url = attachment_domain.SignedUrl(root="https://test.com")

        self.attachment_usecase.attachment_repo.find_by_id = Mock(return_value=self.dummy_attachment(attachment_id))
        self.attachment_usecase.blob_storage_service.create_attachment_blob_sas_url = Mock(return_value=sas_url)

        got = self.attachment_usecase.get_attachment_signed_url(tenant, bot_id, attachment_id)
        assert got == sas_url
        self.attachment_usecase.attachment_repo.find_by_id.assert_called_once_with(attachment_id)
        self.attachment_usecase.blob_storage_service.create_attachment_blob_sas_url.assert_called_once_with(
            tenant.container_name, bot_id, self.dummy_attachment(attachment_id).blob_name
        )
