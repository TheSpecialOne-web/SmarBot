import datetime
from unittest.mock import MagicMock, Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.bot import approach_variable as approach_variable_domain
from api.domain.models.llm.allow_foreign_region import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.llm.pdf_parser import BasicAiPdfParser, PdfParser
from api.domain.models.search.chunk import DocumentChunk
from api.domain.models.search.endpoint import Endpoint
from api.domain.models.search.index_name import IndexName
from api.domain.models.storage.container_name import ContainerName
from api.domain.services import (
    box as box_service,
    cognitive_search as cognitive_search_service,
    msgraph as msgraph_service,
    queue_storage as queue_storage_service,
)
from api.usecase.job.document import DocumentUseCase


class TestUpdateDocumentByAncestorFolderPathUseCase:
    MAX_PROCESS_CHUNK_COUNT = 10000

    def dummy_bot(self, bot_id: bot_domain.Id, approach: bot_domain.Approach = bot_domain.Approach.NEOLLM):
        return bot_domain.Bot(
            id=bot_id,
            name=bot_domain.Name(value="test"),
            description=bot_domain.Description(value="test"),
            created_at=bot_domain.CreatedAt(root=datetime.datetime.now()),
            index_name=IndexName(root="test"),
            container_name=ContainerName(root="test"),
            approach=approach,
            pdf_parser=PdfParser.PYPDF,
            example_questions=[],
            search_method=(
                bot_domain.SearchMethod.URSA_SEMANTIC
                if approach == bot_domain.Approach.URSA
                else bot_domain.SearchMethod.SEMANTIC_HYBRID
            ),
            response_generator_model_family=ModelFamily.GPT_4O,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#000000"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            group_id=group_domain.Id(value=1),
            status=bot_domain.Status.ACTIVE,
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            approach_variables=[
                approach_variable_domain.ApproachVariable(
                    name=approach_variable_domain.Name(value="search_service_endpoint"),
                    value=approach_variable_domain.Value(value="test"),
                ),
            ],
        )

    def dummy_document(
        self,
        id: document_domain.Id,
        name: document_domain.Name,
        document_folder_id: document_folder_domain.Id,
    ):
        return document_domain.Document(
            id=id,
            name=name,
            memo=document_domain.Memo(value="test"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
            created_at=document_domain.CreatedAt(value=datetime.datetime.now()),
        )

    def dummy_document_folder_with_order(self, order: int):
        return document_folder_domain.DocumentFolderWithOrder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root=f"test{order}"),
            created_at=document_folder_domain.CreatedAt(root=datetime.datetime.now()),
            order=document_folder_domain.Order(root=order),
        )

    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.bot_repo_mock = MagicMock(spec=bot_domain.IBotRepository)
        self.document_repo_mock = MagicMock(spec=document_domain.IDocumentRepository)
        self.document_folder_repo_mock = MagicMock(spec=document_folder_domain.IDocumentFolderRepository)
        self.cognitive_search_service_mock = MagicMock(spec=cognitive_search_service.ICognitiveSearchService)
        self.queue_storage_service_mock = MagicMock(spec=queue_storage_service.IQueueStorageService)
        self.msgraph_service_mock = MagicMock(spec=msgraph_service.IMsgraphService)
        self.box_service_mock = MagicMock(spec=box_service.IBoxService)

        self.use_case = DocumentUseCase(
            tenant_repo=self.tenant_repo_mock,
            bot_repo=self.bot_repo_mock,
            document_repo=self.document_repo_mock,
            document_folder_repo=self.document_folder_repo_mock,
            cognitive_search_service=self.cognitive_search_service_mock,
            queue_storage_service=self.queue_storage_service_mock,
            msgraph_service=self.msgraph_service_mock,
            box_service=self.box_service_mock,
        )

        # Mock
        self.tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            status=tenant_domain.Status.TRIAL,
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
            basic_ai_pdf_parser=BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    #  10000個以下のチャンクを処理する
    def test_sync_document_path(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_ids = [document_domain.Id(value=1), document_domain.Id(value=2)]

        # チャンクカウントの設定
        def mock_get_chunk_count(endpoint, index_name, bot_id, document_id: document_domain.Id):
            return 3000

        self.use_case.cognitive_search_service.get_document_chunk_count_by_document_id.side_effect = (
            mock_get_chunk_count
        )
        # Mock
        self.use_case.bot_repo.find_by_id_and_tenant_id.return_value = self.dummy_bot(bot_id=bot_id)
        self.use_case.document_folder_repo.find_by_id_and_bot_id = Mock(
            return_value=self.dummy_document_folder_with_order(order=1)
        )
        document_folder_with_order1 = self.dummy_document_folder_with_order(order=1)
        document_folder_with_order2 = self.dummy_document_folder_with_order(order=2)
        self.use_case.document_repo.find_documents_with_ancestor_folders_by_ids.return_value = [
            document_domain.DocumentWithAncestorFolders(
                **self.dummy_document(
                    id=document_ids[0],
                    name=document_domain.Name(value="test"),
                    document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
                ).model_dump(),
                ancestor_folders=[
                    document_folder_with_order1,
                ],
            ),
        ]

        updated_documents = [
            self.dummy_document(
                id=document_ids[0],
                name=document_domain.Name(value="test"),
                document_folder_id=document_folder_with_order1.id,
            ),
            self.dummy_document(
                id=document_ids[1],
                name=document_domain.Name(value="test2"),
                document_folder_id=document_folder_with_order2.id,
            ),
        ]
        self.use_case.document_repo.find_by_ids_and_bot_id.return_value = updated_documents

        # Execute
        self.use_case.sync_document_path(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder_with_order1.id,
            document_ids=document_ids,
        )

        # Assert
        self.use_case.document_repo.bulk_update.assert_called_once_with(updated_documents)

    # 10000件を超える
    def test_sync_document_path_over_MAX_PROCESS_CHUNK_COUNT(self, setup):
        """
        MAX_PROCESS_CHUNK_COUNTを超えるドキュメントの処理をテスト
        - document_id=1 (6000チャンク) -> 処理される
        - document_id=2 (5000チャンク) -> キューに送られる
        """
        # Arrange
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_ids = [document_domain.Id(value=1), document_domain.Id(value=2)]

        # チャンクカウントの設定
        def mock_get_chunk_count(endpoint, index_name, bot_id, document_id: document_domain.Id):
            return 6000 if document_id.value == 1 else 5000

        self.use_case.cognitive_search_service.get_document_chunk_count_by_document_id.side_effect = (
            mock_get_chunk_count
        )

        # 処理対象のドキュメントの設定
        document_folder = self.dummy_document_folder_with_order(order=1)
        document1 = document_domain.DocumentWithAncestorFolders(
            **self.dummy_document(
                id=document_ids[0],
                name=document_domain.Name(value="test"),
                document_folder_id=document_folder.id,
            ).model_dump(),
            ancestor_folders=[document_folder],
        )

        # Mockの設定
        self.use_case.bot_repo.find_by_id_and_tenant_id.return_value = self.dummy_bot(bot_id=bot_id)
        self.use_case.document_folder_repo.find_by_id_and_bot_id = Mock(return_value=document_folder)
        self.use_case.document_repo.find_documents_with_ancestor_folders_by_ids.return_value = [document1]
        updated_document = self.dummy_document(
            id=document_ids[0],
            name=document_domain.Name(value="test"),
            document_folder_id=document_folder.id,
        )
        self.use_case.document_repo.find_by_ids_and_bot_id.return_value = [updated_document]
        document_chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            bot_id=bot_id.value,
            data_source_id=str(uuid.uuid4()),
            document_id=document_ids[0].value,
            document_folder_id=str(document_folder.id.root),
            content="test",
            blob_path="test",
            file_name="test",
            file_extension="test",
            page_number=1,
            is_vectorized=True,
            title_vector=[1, 2, 3],
            content_vector=[4, 5, 6],
            external_id=None,
            parent_external_id=None,
        )

        self.use_case.tenant_repo.find_by_id.return_value = self.tenant
        self.use_case.cognitive_search_service.find_index_documents_by_document_ids.return_value = [document_chunk]

        # Act
        self.use_case.sync_document_path(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder.id,
            document_ids=document_ids,  # 全てのドキュメントIDを渡す
        )

        # Assert
        # 1. ドキュメントの検索が正しく行われることを確認
        self.use_case.document_repo.find_documents_with_ancestor_folders_by_ids.assert_called_once_with(
            bot_id=bot_id,
            ids=[document_ids[0]],  # document_id=1のみが処理対象
        )

        # チャンクカウントの取得回数を確認
        assert self.use_case.cognitive_search_service.get_document_chunk_count_by_document_id.call_count == 2

        # チャンクの取得
        self.use_case.cognitive_search_service.find_index_documents_by_document_ids.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            document_ids=[document_ids[0]],
            document_chunk_count=6000,
        )

        # チャンクの更新
        self.use_case.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            documents=[document_chunk],
        )

        # ドキュメントの更新が正しく行われることを確認
        self.use_case.document_repo.bulk_update.assert_called_once_with([updated_document])

        # 残りのドキュメントがキューに送られることを確認
        self.use_case.queue_storage_service.send_message_to_sync_document_path_queue.assert_called_once_with(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder.id,
            document_ids=[document_ids[1]],  # document_id=2のみがキューに送られる
        )

    # Ursaの場合のdocument更新
    def test_sync_ursa_document_path(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_ids = [document_domain.Id(value=1), document_domain.Id(value=2)]

        # チャンクカウントの設定
        def mock_get_chunk_count(endpoint, index_name, bot_id, document_id: document_domain.Id):
            return 3000

        # Mock
        self.use_case.cognitive_search_service.get_document_chunk_count_by_document_id.side_effect = (
            mock_get_chunk_count
        )
        self.use_case.cognitive_search_service.get_ursa_document_chunk_count_by_document_id.side_effect = (
            mock_get_chunk_count
        )
        self.use_case.bot_repo.find_by_id_and_tenant_id.return_value = self.dummy_bot(
            bot_id=bot_id, approach=bot_domain.Approach.URSA
        )
        document_folder_with_order1 = self.dummy_document_folder_with_order(order=1)
        document_folder_with_order2 = self.dummy_document_folder_with_order(order=2)
        self.use_case.document_folder_repo.find_by_id_and_bot_id = Mock(return_value=document_folder_with_order1)
        self.use_case.document_repo.find_documents_with_ancestor_folders_by_ids.return_value = [
            document_domain.DocumentWithAncestorFolders(
                **self.dummy_document(
                    id=document_ids[0],
                    name=document_domain.Name(value="test"),
                    document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
                ).model_dump(),
                ancestor_folders=[
                    document_folder_with_order1,
                ],
            ),
        ]

        updated_documents = [
            self.dummy_document(
                id=document_ids[0],
                name=document_domain.Name(value="test"),
                document_folder_id=document_folder_with_order1.id,
            ),
            self.dummy_document(
                id=document_ids[1],
                name=document_domain.Name(value="test2"),
                document_folder_id=document_folder_with_order2.id,
            ),
        ]
        self.use_case.document_repo.find_by_ids_and_bot_id.return_value = updated_documents

        # Execute
        self.use_case.sync_document_path(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder_with_order1.id,
            document_ids=document_ids,
        )

        # Assert
        self.use_case.document_repo.bulk_update.assert_called_once_with(updated_documents)
