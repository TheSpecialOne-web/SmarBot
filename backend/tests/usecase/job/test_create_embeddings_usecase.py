from datetime import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion, BasicAiPdfParser, ModelFamily
from api.domain.models.llm.pdf_parser import PdfParser
from api.domain.models.search import DocumentChunk, Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.usecase.job.create_embeddings import CreateEmbeddingsUseCase


class TestCreateEmbeddingsUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.bot_repo = Mock()
        self.document_repo = Mock()
        self.queue_storage_service = Mock()
        self.llm_service = Mock()
        self.cognitive_search_service = Mock()
        self.usecase = CreateEmbeddingsUseCase(
            self.tenant_repo,
            self.bot_repo,
            self.document_repo,
            self.queue_storage_service,
            self.llm_service,
            self.cognitive_search_service,
        )

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock(return_value=False)
        monkeypatch.setattr("api.usecase.job.create_embeddings.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def dummy_tenant(self, id: tenant_domain.Id) -> tenant_domain.Tenant:
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
            basic_ai_pdf_parser=BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_bot(self, id: bot_domain.Id):
        return bot_domain.Bot(
            id=id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#000000"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_document(
        self, id: document_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> document_domain.Document:
        return document_domain.Document(
            id=id,
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.PENDING,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=None,
            document_folder_id=document_folder_id,
        )

    def dummy_document_folder_with_ancestors(
        self, id: document_folder_domain.Id
    ) -> document_folder_domain.DocumentFolderWithAncestors:
        return document_folder_domain.DocumentFolderWithAncestors(
            id=id,
            name=document_folder_domain.Name(root="dummy_folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder_domain.Id(root=uuid.uuid4()),
                    name=document_folder_domain.Name(root="descendant_folder1"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
                    order=document_folder_domain.Order(root=1),
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder_domain.Id(root=uuid.uuid4()),
                    name=document_folder_domain.Name(root="descendant_folder2"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.utcnow()),
                    order=document_folder_domain.Order(root=2),
                ),
            ],
        )

    def dummy_document_chunks(
        self,
        bot_id: int,
        data_source_id: str,
        document_id: int,
        content: str,
        blob_path: str,
        file_name: str,
        file_extension: str,
        page_number: int,
        document_folder_id: str,
    ) -> DocumentChunk:
        return DocumentChunk(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            data_source_id=data_source_id,
            document_id=document_id,
            document_folder_id=document_folder_id,
            content=content,
            blob_path=blob_path,
            file_name=file_name,
            file_extension=file_extension,
            page_number=page_number,
            is_vectorized=False,
            title_vector=None,
            content_vector=None,
            external_id=None,
            parent_external_id=None,
        )

    def test_create_or_update_embeddings_to_index_documents(self, setup):
        bot_id = 1
        data_source_id = "00000000-0000-0000-0000-000000000000"
        document_id = 1
        document_folder_id = "00000000-0000-0000-0000-000000000001"
        blob_path = "test.pdf"
        file_name = "test"
        file_extension = "pdf"
        chunks = [
            self.dummy_document_chunks(
                bot_id=bot_id,
                data_source_id=data_source_id,
                document_id=document_id,
                content=f"[folder1/folder2/test.pdf]:test content{i}",
                blob_path=blob_path,
                file_name=file_name,
                file_extension=file_extension,
                page_number=i,
                document_folder_id=document_folder_id,
            )
            for i in range(5)
        ]
        search_method = bot_domain.SearchMethod.SEMANTIC_HYBRID
        use_foreign_region = False

        self.usecase.llm_service.generate_embeddings = Mock(return_value=[0.1, 0.2, 0.3])

        index_documents, is_error = self.usecase._create_or_update_embeddings_to_index_documents(
            chunks, search_method, use_foreign_region
        )

        # for chunk in chunks:
        #     chunk.add_content_vector([0.1, 0.2, 0.3])
        #     chunk.update_is_vectorized_true()
        want = [
            DocumentChunk(
                **chunk.model_dump(
                    exclude=(
                        "is_vectorized",
                        "content_vector",
                    )
                ),
                is_vectorized=True,
                content_vector=[0.1, 0.2, 0.3],
            )
            for chunk in chunks
        ]

        assert is_error is False
        assert index_documents == want

    def test_create_embeddings(self, setup, mock_get_feature_flag):
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        data_source_id = str(uuid.uuid4())
        document_id = document_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        tenant = self.dummy_tenant(id=tenant_id)
        bot = self.dummy_bot(id=bot_id)
        document = self.dummy_document(id=document_id, document_folder_id=document_folder_id)
        chunks = [
            self.dummy_document_chunks(
                bot_id=bot_id.value,
                data_source_id=data_source_id,
                document_id=document_id.value,
                content=f"[folder1/folder2/test.pdf]:test content{i}",
                blob_path="test.pdf",
                file_name="test",
                file_extension="pdf",
                page_number=i,
                document_folder_id=str(document_folder_id.root),
            )
            for i in range(5)
        ]
        vectorized_chunks = [
            DocumentChunk(
                **chunk.model_dump(
                    exclude=(
                        "is_vectorized",
                        "content_vector",
                    )
                ),
                is_vectorized=True,
                content_vector=[0.1, 0.2, 0.3],
            )
            for chunk in chunks
        ]

        self.usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.usecase.cognitive_search_service.get_document_count_without_vectors = Mock(return_value=5)
        self.usecase.cognitive_search_service.get_documents_without_vectors = Mock(return_value=chunks)
        self.usecase._create_or_update_embeddings_to_index_documents = Mock(return_value=(vectorized_chunks, False))
        self.usecase.cognitive_search_service.create_or_update_document_chunks = Mock()
        self.usecase.document_repo.update = Mock()
        self.usecase.queue_storage_service.send_message_to_calculate_storage_usage_queue = Mock()

        self.usecase.create_embeddings(tenant_id=tenant_id, bot_id=bot_id, document_id=document_id, dequeue_count=1)

        self.usecase.tenant_repo.find_by_id.assert_called_once_with(id=tenant_id)
        self.usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(id=document_id, bot_id=bot_id)
        self.usecase.cognitive_search_service.get_document_count_without_vectors.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )
        self.usecase.cognitive_search_service.get_documents_without_vectors.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
            limit=100,
        )
        self.usecase._create_or_update_embeddings_to_index_documents.assert_called_once_with(
            index_documents=chunks,
            search_method=bot.search_method,
            use_foreign_region=False,
        )
        self.usecase.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            documents=vectorized_chunks,
        )
        self.usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                **document.model_dump(exclude=("status",)), status=document_domain.Status.COMPLETED
            )
        )
        self.usecase.queue_storage_service.send_message_to_calculate_storage_usage_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_id=document_id
        )

    def test_create_embeddings_continue(self, setup, mock_get_feature_flag):
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        data_source_id = str(uuid.uuid4())
        document_id = document_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        tenant = self.dummy_tenant(id=tenant_id)
        bot = self.dummy_bot(id=bot_id)
        document = self.dummy_document(id=document_id, document_folder_id=document_folder_id)
        chunks = [
            self.dummy_document_chunks(
                bot_id=bot_id.value,
                data_source_id=data_source_id,
                document_id=document_id.value,
                content=f"[folder1/folder2/test.pdf]:test content{i}",
                blob_path="test.pdf",
                file_name="test",
                file_extension="pdf",
                page_number=i,
                document_folder_id=str(document_folder_id.root),
            )
            for i in range(100)
        ]
        vectorized_chunks = [
            DocumentChunk(
                **chunk.model_dump(
                    exclude=(
                        "is_vectorized",
                        "content_vector",
                    )
                ),
                is_vectorized=True,
                content_vector=[0.1, 0.2, 0.3],
            )
            for chunk in chunks
        ]

        self.usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.usecase.cognitive_search_service.get_document_count_without_vectors = Mock(return_value=105)
        self.usecase.cognitive_search_service.get_documents_without_vectors = Mock(return_value=chunks)
        self.usecase._create_or_update_embeddings_to_index_documents = Mock(return_value=(vectorized_chunks, False))
        self.usecase.cognitive_search_service.create_or_update_document_chunks = Mock()
        self.usecase.queue_storage_service.send_message_to_create_embeddings_queue = Mock()

        self.usecase.create_embeddings(tenant_id=tenant_id, bot_id=bot_id, document_id=document_id, dequeue_count=1)

        self.usecase.tenant_repo.find_by_id.assert_called_once_with(id=tenant_id)
        self.usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(id=document_id, bot_id=bot_id)
        self.usecase.cognitive_search_service.get_document_count_without_vectors.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )
        self.usecase.cognitive_search_service.get_documents_without_vectors.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
            limit=100,
        )
        self.usecase._create_or_update_embeddings_to_index_documents.assert_called_once_with(
            index_documents=chunks,
            search_method=bot.search_method,
            use_foreign_region=False,
        )
        self.usecase.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            documents=vectorized_chunks,
        )
        self.usecase.queue_storage_service.send_message_to_create_embeddings_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_id=document_id
        )

    def test_create_embeddings_no_documents_without_vectors(self, setup, mock_get_feature_flag):
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        tenant = self.dummy_tenant(id=tenant_id)
        bot = self.dummy_bot(id=bot_id)
        document = self.dummy_document(id=document_id, document_folder_id=document_folder_id)

        self.usecase.tenant_repo.find_by_id = Mock(return_value=tenant)
        self.usecase.bot_repo.find_by_id_and_tenant_id = Mock(return_value=bot)
        self.usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.usecase.cognitive_search_service.get_document_count_without_vectors = Mock(return_value=0)
        self.usecase.document_repo.update = Mock()

        self.usecase.create_embeddings(tenant_id=tenant_id, bot_id=bot_id, document_id=document_id, dequeue_count=1)

        self.usecase.tenant_repo.find_by_id.assert_called_once_with(id=tenant_id)
        self.usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(id=bot_id, tenant_id=tenant_id)
        self.usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(id=document_id, bot_id=bot_id)
        self.usecase.cognitive_search_service.get_document_count_without_vectors.assert_called_once_with(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot_id,
            document_id=document_id,
        )
        self.usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                **document.model_dump(exclude=("status",)), status=document_domain.Status.COMPLETED
            )
        )

    def test_create_embeddings_exceed_max_dequeue_count(self, setup):
        document = self.dummy_document(document_domain.Id(value=1), document_folder_domain.Id(root=uuid.uuid4()))

        self.usecase._create_embeddings = Mock(side_effect=Exception("test"))
        self.usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.usecase.document_repo.update = Mock()

        with pytest.raises(Exception):
            self.usecase.create_embeddings(
                tenant_id=tenant_domain.Id(value=1),
                bot_id=bot_domain.Id(value=1),
                document_id=document_domain.Id(value=1),
                dequeue_count=3,
            )

        self.usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(
            id=document_domain.Id(value=1), bot_id=bot_domain.Id(value=1)
        )
        self.usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                **document.model_dump(exclude=("status",)),
                status=document_domain.Status.FAILED,
            )
        )
