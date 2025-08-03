from datetime import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily
from api.domain.models.search import DocumentChunk, Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.usecase.job.sync_document_name import SyncDocumentNameUseCase


class TestJobSyncDocumentNameUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = Mock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = Mock(spec=bot_domain.IBotRepository)
        self.document_folder_repo = Mock(spec=document_folder_domain.IDocumentFolderRepository)
        self.document_repo_mock = Mock(spec=document_domain.IDocumentRepository)
        self.cognitive_search_service_mock = Mock(spec=ICognitiveSearchService)
        self.queue_storage_service_mock = Mock(spec=IQueueStorageService)

        self.use_case = SyncDocumentNameUseCase(
            self.tenant_repo_mock,
            self.bot_repo_mock,
            self.document_folder_repo,
            self.document_repo_mock,
            self.cognitive_search_service_mock,
            self.queue_storage_service_mock,
        )

        # Mock data
        self.tenant_id = tenant_domain.Id(value=1)
        self.bot_id = bot_domain.Id(value=1)
        self.document_id = document_domain.Id(value=1)

        self.tenant = tenant_domain.Tenant(
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
        self.bot = bot_domain.Bot(
            id=self.bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test"),
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
        self.root_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=None,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        self.parent_document_folder_name = document_folder_domain.Name(root="test_parent_document_folder_name")
        self.parent_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=self.parent_document_folder_name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        self.document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            id=self.parent_document_folder.id,
            name=self.parent_document_folder_name,
            created_at=self.parent_document_folder.created_at,
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    **self.root_document_folder.model_dump(), order=document_folder_domain.Order(root=0)
                )
            ],
        )

        self.old_document_name = document_domain.Name(value="old_name")
        self.new_document_name = document_domain.Name(value="new_name")

        self.document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=self.new_document_name,
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=self.parent_document_folder.id,
        )

        self.document_with_ancestor_folders = document_domain.DocumentWithAncestorFolders(
            **self.document.model_dump(),
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    **self.root_document_folder.model_dump(), order=document_folder_domain.Order(root=0)
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    **self.parent_document_folder.model_dump(), order=document_folder_domain.Order(root=1)
                ),
            ],
        )

        self.document_chunks = [
            DocumentChunk(
                id=str(uuid.uuid4()),
                bot_id=self.bot.id.value,
                data_source_id=str(uuid.uuid4()),
                document_id=self.document.id.value,
                document_folder_id=str(self.parent_document_folder.id.root),
                content=f"[{self.parent_document_folder_name.root}/{self.old_document_name.value}]:test_content",
                blob_path=f"{self.bot.id.value}/{self.parent_document_folder.id.root}/{self.old_document_name.value}.{self.document.file_extension.value}",
                file_name=self.old_document_name.value,
                file_extension=self.document.file_extension.value,
                page_number=1,
                is_vectorized=False,
                title_vector=None,
                content_vector=None,
                external_id=None,
                parent_external_id=None,
            )
        ]

    def test_sync_document_name(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_id = self.document_id

        # Mock
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.bot_repo.find_by_id_and_tenant_id = Mock(return_value=self.bot)
        self.use_case.document_repo.find_with_ancestor_folders_by_id = Mock(
            return_value=self.document_with_ancestor_folders
        )

        self.use_case.cognitive_search_service.find_index_documents_by_bot_id_and_document_id = Mock(
            return_value=self.document_chunks
        )
        self.use_case.cognitive_search_service.create_or_update_document_chunks = Mock(return_value=True)
        self.use_case.queue_storage_service.send_message_to_create_embeddings_queue = Mock(return_value=None)

        # Call the method
        self.use_case.sync_document_name(tenant_id, bot_id, document_id)

        # Assertions
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.use_case.document_repo.find_with_ancestor_folders_by_id.assert_called_once_with(bot_id, document_id)

        self.use_case.cognitive_search_service.find_index_documents_by_bot_id_and_document_id.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )

        self.use_case.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            documents=self.document_chunks,
        )

        self.use_case.queue_storage_service.send_message_to_create_embeddings_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_id=document_id
        )

        assert (
            self.document_chunks[0].content
            == f"[{self.parent_document_folder_name.root}/{self.new_document_name.value}]:test_content"
        )
        assert (
            self.document_chunks[0].blob_path
            == f"{self.bot.id.value}/{self.parent_document_folder.id.root}/{self.new_document_name.value}.{self.document.file_extension.value}"
        )
        assert self.document_chunks[0].file_name == self.document.name.value
        assert self.document_chunks[0].is_vectorized is False

    def test_sync_document_name_in_root_folder(self, setup):
        # Input
        tenant_id = self.tenant_id
        bot_id = self.bot_id
        document_id = self.document_id

        # Mock
        self.use_case.tenant_repo.find_by_id = Mock(return_value=self.tenant)
        self.use_case.bot_repo.find_by_id_and_tenant_id = Mock(return_value=self.bot)
        self.use_case.document_repo.find_with_ancestor_folders_by_id = Mock(
            return_value=self.document_with_ancestor_folders
        )

        self.use_case.cognitive_search_service.find_index_documents_by_bot_id_and_document_id = Mock(
            return_value=self.document_chunks
        )
        self.use_case.cognitive_search_service.create_or_update_document_chunks = Mock(return_value=True)
        self.use_case.queue_storage_service.send_message_to_create_embeddings_queue = Mock(return_value=None)
        self.use_case.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=document_folder_domain.DocumentFolder(
                id=self.document_with_ancestor_folders.document_folder_id,
                name=None,
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            )
        )

        # Call the method
        self.use_case.sync_document_name(tenant_id, bot_id, document_id)

        # Assertions
        self.use_case.tenant_repo.find_by_id.assert_called_once_with(tenant_id)
        self.use_case.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.use_case.document_repo.find_with_ancestor_folders_by_id.assert_called_once_with(bot_id, document_id)

        self.use_case.cognitive_search_service.find_index_documents_by_bot_id_and_document_id.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )

        self.use_case.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            documents=self.document_chunks,
        )

        self.use_case.queue_storage_service.send_message_to_create_embeddings_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_id=document_id
        )

        assert (
            self.document_chunks[0].content
            == f"[{self.parent_document_folder_name.root}/{self.new_document_name.value}]:test_content"
        )
        assert (
            self.document_chunks[0].blob_path
            == f"{self.bot.id.value}/{self.new_document_name.value}.{self.document.file_extension.value}"
        )
        assert self.document_chunks[0].file_name == self.document.name.value
        assert self.document_chunks[0].is_vectorized is False
