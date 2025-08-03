from datetime import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.llm.allow_foreign_region import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.llm.pdf_parser import BasicAiPdfParser
from api.domain.models.search.endpoint import Endpoint
from api.domain.models.search.index_name import IndexName
from api.domain.models.storage.container_name import ContainerName
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.models.tenant.additional_platform import AdditionalPlatformList
from api.domain.models.tenant.enable_llm_document_reader import EnableLLMDocumentReader
from api.libs.exceptions import BadRequest, Conflict
from api.usecase.document_folder.document_folder import (
    CreateDocumentFolderInput,
    DocumentFolderUseCase,
    StartExternalDataConnectionInput,
)


class TestCommonPromptTemplateUsecase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.bot_repo = Mock()
        self.document_repo = Mock()
        self.document_folder_repo = Mock()
        self.queue_storage_service = Mock()
        self.msgraph_service = Mock()
        box_service = Mock()
        self.document_folder_usecase = DocumentFolderUseCase(
            tenant_repo=self.tenant_repo,
            bot_repo=self.bot_repo,
            document_repo=self.document_repo,
            document_folder_repo=self.document_folder_repo,
            queue_storage_service=self.queue_storage_service,
            msgraph_service=self.msgraph_service,
            box_service=box_service,
        )

    def dummy_tenant(self, tenant_id: tenant_domain.Id):
        return tenant_domain.Tenant(
            id=tenant_id,
            name=tenant_domain.Name(value="test_tenant_name"),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="test_search_service_endpoint"),
            index_name=IndexName(root="test-index"),
            status=tenant_domain.Status.SUBSCRIBED,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-container"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=False),
            basic_ai_pdf_parser=BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=0),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=0),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def test_get_document_folders_by_parent_document_folder_id_with_parent_document_folder_id(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # mock
        parent_document_folder = document_folder_domain.DocumentFolder(
            id=parent_document_folder_id,
            name=document_folder_domain.Name(root="test_parent_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        want_document_folders = [
            document_folder_domain.DocumentFolderWithDocumentProcessingStats(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_folder_domain.Name(root="test_document_folder_name"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            ),
            document_folder_domain.DocumentFolderWithDocumentProcessingStats(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_folder_domain.Name(root="test_document_folder_name2"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            ),
        ]

        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id.return_value = parent_document_folder
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id.return_value = (
            want_document_folders
        )

        # Execute
        got = self.document_folder_usecase.get_document_folders_by_parent_document_folder_id(
            bot_id, parent_document_folder_id
        )
        # test
        assert got == want_document_folders

        # assert call
        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(
            parent_document_folder_id, bot_id
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id.assert_called_once_with(
            bot_id, parent_document_folder_id
        )

    def test_get_document_folders_by_parent_document_folder_id_with_no_parent_document_folder_id(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        parent_document_folder_id = None

        # mock
        root_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_root_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        want_document_folders = [
            document_folder_domain.DocumentFolderWithDocumentProcessingStats(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_folder_domain.Name(root="test_document_folder_name"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            ),
        ]
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            root_document_folder
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id.return_value = (
            want_document_folders
        )

        # Execute
        got = self.document_folder_usecase.get_document_folders_by_parent_document_folder_id(
            bot_id, parent_document_folder_id
        )

        # test
        assert got == want_document_folders

        # assert call method
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.assert_called_once_with(
            bot_id
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id.assert_called_once_with(
            bot_id, root_document_folder.id
        )

    def test_create_document_folder(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        parent_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_parent_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        input = CreateDocumentFolderInput(
            document_folder_for_create=document_folder_domain.DocumentFolderForCreate(
                name=document_folder_domain.Name(root="test_create_document_folder_name"),
            ),
            parent_document_folder_id=parent_document_folder.id,
        )

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=input.document_folder_for_create.id,
            name=input.document_folder_for_create.name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        # Mock
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=parent_document_folder
        )
        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(
            return_value=parent_document_folder
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_folder_repo.create = Mock(
            return_value=document_folder_domain.DocumentFolder(
                id=input.document_folder_for_create.id,
                name=input.document_folder_for_create.name,
                created_at=expected_output.created_at,
            )
        )

        # Execute
        output = self.document_folder_usecase.create_document_folder(bot_id, input)

        # Test
        self.document_folder_usecase.document_folder_repo.create.assert_called_once_with(
            bot_id, input.parent_document_folder_id, input.document_folder_for_create
        )
        assert output == expected_output

    def test_get_root_document_folder_by_bot_id(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            expected_output
        )

        # Execute
        got = self.document_folder_usecase.get_root_document_folder_by_bot_id(bot_id)

        assert got == expected_output

    def test_get_with_ancestors_by_id_and_bot_id(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # Expected
        expected_output = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder_id,
                    name=document_folder_domain.Name(root="test_document_folder_name"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.now()),
                    order=document_folder_domain.Order(root=0),
                )
            ],
            id=document_folder_id,
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        self.document_folder_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id.return_value = (
            expected_output
        )

        # Execute
        got = self.document_folder_usecase.get_with_ancestors_by_id_and_bot_id(bot_id, document_folder_id)

        assert got == expected_output

    def test_update_document_folder(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document_folder_for_update = document_folder_domain.DocumentFolderForUpdate(
            name=document_folder_domain.Name(root="test_update_document_folder_name")
        )
        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder.id,
            name=document_folder_for_update.name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        # Mock
        document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder.id,
                    name=document_folder.name,
                    created_at=document_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                )
            ],
            id=document_folder.id,
            name=document_folder.name,
            created_at=document_folder.created_at,
        )
        self.document_folder_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=document_folder_with_ancestors
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_folder_repo.update = Mock(return_value=expected_output)

        # Execute
        output = self.document_folder_usecase.update_document_folder(
            bot_id, document_folder.id, document_folder_for_update
        )

        # Test
        self.document_folder_usecase.document_folder_repo.update.assert_called_once_with(
            bot_id,
            document_folder_domain.DocumentFolderWithAncestors(
                id=document_folder.id,
                name=document_folder_for_update.name,
                created_at=document_folder.created_at,
                ancestor_folders=document_folder_with_ancestors.ancestor_folders,
            ),
        )
        assert output == expected_output

    def test_update_document_folder_v2(self, setup):
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        bot_id = bot_domain.Id(value=1)
        now = datetime.now()
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=now),
        )
        document_folder_for_update = document_folder_domain.DocumentFolderForUpdate(
            name=document_folder_domain.Name(root="test_update_document_folder_v2_name")
        )

        # Expected
        expected_output = document_folder_domain.DocumentFolder(
            id=document_folder.id,
            name=document_folder_for_update.name,
            created_at=document_folder_domain.CreatedAt(root=now),
        )

        # Mock
        document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=document_folder.id,
                    name=document_folder.name,
                    created_at=document_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                )
            ],
            id=document_folder.id,
            name=document_folder.name,
            created_at=document_folder.created_at,
        )
        descendant_documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document_name"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder.id,
                created_at=document_domain.CreatedAt(value=datetime.now()),
            ),
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document_name"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=2),
                document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
                created_at=document_domain.CreatedAt(value=datetime.now()),
            ),
        ]
        self.document_folder_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=document_folder_with_ancestors
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_repo.find_all_descendants_documents_by_ancestor_folder_id = Mock(
            return_value=descendant_documents
        )
        self.document_folder_usecase.document_folder_repo.update = Mock(return_value=expected_output)

        # Execute
        output = self.document_folder_usecase.update_document_folder_v2(
            tenant=tenant,
            bot_id=bot_id,
            document_folder_id=document_folder.id,
            document_folder_for_update=document_folder_for_update,
        )

        # Test
        self.document_folder_usecase.document_folder_repo.update.assert_called_once_with(
            bot_id,
            document_folder_domain.DocumentFolderWithAncestors(
                id=document_folder.id,
                name=document_folder_for_update.name,
                created_at=document_folder.created_at,
                ancestor_folders=document_folder_with_ancestors.ancestor_folders,
            ),
        )
        assert output == expected_output

    def test_update_document_folder_with_root_folder(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document_folder_for_update = document_folder_domain.DocumentFolderForUpdate(
            name=document_folder_domain.Name(root="test_update_document_folder_name")
        )

        # Mock
        document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[],
            id=document_folder.id,
            name=document_folder.name,
            created_at=document_folder.created_at,
        )
        self.document_folder_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=document_folder_with_ancestors
        )

        # Execute
        with pytest.raises(BadRequest):
            self.document_folder_usecase.update_document_folder(
                bot_id=bot_id,
                document_folder_id=document_folder.id,
                document_folder_for_update=document_folder_for_update,
            )

    def test_update_document_folder_with_root_folder_v2(self, setup):
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        bot_id = bot_domain.Id(value=1)
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document_folder_for_update = document_folder_domain.DocumentFolderForUpdate(
            name=document_folder_domain.Name(root="test_update_document_folder_name")
        )

        # Mock
        document_folder_with_ancestors = document_folder_domain.DocumentFolderWithAncestors(
            ancestor_folders=[],
            id=document_folder.id,
            name=document_folder.name,
            created_at=document_folder.created_at,
        )
        self.document_folder_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=document_folder_with_ancestors
        )

        # Execute
        with pytest.raises(BadRequest):
            self.document_folder_usecase.update_document_folder_v2(
                tenant=tenant,
                bot_id=bot_id,
                document_folder_id=document_folder.id,
                document_folder_for_update=document_folder_for_update,
            )

    def test_delete_document_folder(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        input = document_folder_domain.Id(root=uuid.uuid4())

        # Mock
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(return_value=[])
        self.document_folder_usecase.document_repo.find_by_parent_document_folder_id = Mock(return_value=[])

        # Execute
        self.document_folder_usecase.delete_document_folder(bot_id, input)

        # Test
        self.document_folder_usecase.document_folder_repo.delete_by_ids.assert_called_once_with(bot_id, [input])

    def test_delete_document_folder_v2(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        root_document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=None,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        descendant_document_folder_id1 = document_folder_domain.Id(root=uuid.uuid4())
        descendant_document_folder_id2 = document_folder_domain.Id(root=uuid.uuid4())
        descendant_folders = [
            document_folder_domain.DocumentFolder(
                id=descendant_document_folder_id1,
                name=document_folder_domain.Name(root="test_document_folder_name1"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            ),
            document_folder_domain.DocumentFolder(
                id=descendant_document_folder_id2,
                name=document_folder_domain.Name(root="test_document_folder_name2"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            ),
        ]

        document_folder_ids_to_delete = [folder.id for folder in descendant_folders] + [document_folder_id]

        # Mock
        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock()
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=root_document_folder
        )
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(
            return_value=descendant_folders
        )
        self.document_folder_usecase.document_repo.delete_by_folder_ids = Mock()
        self.document_folder_usecase.document_folder_repo.delete_by_ids = Mock()
        self.document_folder_usecase.queue_storage_service.send_message_to_delete_document_folders_queue = Mock()

        # Execute
        self.document_folder_usecase.delete_document_folder_v2(tenant_id, bot_id, document_folder_id)

        # Test
        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(
            document_folder_id, bot_id
        )
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.assert_called_once_with(
            bot_id
        )
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id.assert_called_once_with(
            bot_id, document_folder_id
        )
        self.document_folder_usecase.document_repo.delete_by_folder_ids.assert_called_once_with(
            bot_id, document_folder_ids_to_delete
        )
        self.document_folder_usecase.document_folder_repo.delete_by_ids.assert_called_once_with(
            bot_id, document_folder_ids_to_delete
        )
        self.document_folder_usecase.queue_storage_service.send_message_to_delete_document_folders_queue.assert_called_once_with(
            tenant_id, bot_id, document_folder_ids_to_delete
        )

    def test_move_document_folder(self, setup):
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Mock
        descendant_documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document_name"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
                created_at=document_domain.CreatedAt(value=datetime.now()),
            ),
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document_name"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=2),
                document_folder_id=document_folder_id,
                created_at=document_domain.CreatedAt(value=datetime.now()),
            ),
        ]
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(return_value=[])
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_repo.find_all_descendants_documents_by_ancestor_folder_id = Mock(
            return_value=descendant_documents
        )
        self.document_folder_usecase.document_folder_repo.move_document_folder = Mock()

        # Execute
        self.document_folder_usecase.move_document_folder(
            tenant, bot_id, document_folder_id, new_parent_document_folder_id
        )

        # Test
        self.document_folder_usecase.document_folder_repo.move_document_folder.assert_called_once_with(
            bot_id, document_folder_id, new_parent_document_folder_id
        )

    def test_move_document_folder_with_root_folder(self, setup):
        """ルートフォルダを移動しようとした場合のテスト"""
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Mock
        root_folder = document_folder_domain.DocumentFolder(
            id=document_folder_id,
            name=document_folder_domain.Name(root=""),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=root_folder
        )

        # Execute & Assert
        with pytest.raises(BadRequest, match="ルートフォルダは移動できません"):
            self.document_folder_usecase.move_document_folder(
                tenant, bot_id, document_folder_id, new_parent_document_folder_id
            )

    def test_move_document_folder_to_self(self, setup):
        """フォルダを自分自身に移動しようとした場合のテスト"""
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Execute & Assert
        with pytest.raises(BadRequest, match="選択されたフォルダに移動することはできません"):
            self.document_folder_usecase.move_document_folder(tenant, bot_id, document_folder_id, document_folder_id)

    def test_move_document_folder_to_descendant(self, setup):
        """フォルダを自分の子孫フォルダに移動しようとした場合のテスト"""
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Mock
        descendant_folder = document_folder_domain.DocumentFolder(
            id=new_parent_document_folder_id,
            name=document_folder_domain.Name(root="child"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(
            return_value=[descendant_folder]
        )

        # Execute & Assert
        with pytest.raises(BadRequest, match="選択されたフォルダに移動することはできません"):
            self.document_folder_usecase.move_document_folder(
                tenant, bot_id, document_folder_id, new_parent_document_folder_id
            )

    def test_move_document_folder_with_duplicate_name(self, setup):
        """移動先に同名のフォルダが存在する場合のテスト"""
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Mock
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_id,
            name=document_folder_domain.Name(root="test_folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        existing_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(return_value=document_folder)
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=document_folder_domain.DocumentFolder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_folder_domain.Name(root="root"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            )
        )
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(return_value=[])
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[existing_folder]
        )

        # Execute & Assert
        with pytest.raises(Conflict, match="移動先に同一の名前のフォルダが存在します"):
            self.document_folder_usecase.move_document_folder(
                tenant, bot_id, document_folder_id, new_parent_document_folder_id
            )

    def test_move_document_folder_with_pending_documents(self, setup):
        """処理中のドキュメントが含まれる場合のテスト"""
        # Input
        tenant = self.dummy_tenant(tenant_id=tenant_domain.Id(value=1))
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_parent_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        bot_id = bot_domain.Id(value=1)

        # Mock
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_id,
            name=document_folder_domain.Name(root="test_folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        pending_document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test_document"),
            memo=document_domain.Memo(value="test_memo"),
            file_extension=document_domain.FileExtension(value="pdf"),
            status=document_domain.Status.PENDING,
            storage_usage=document_domain.StorageUsage(root=10),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
            created_at=document_domain.CreatedAt(value=datetime.now()),
        )

        self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(return_value=document_folder)
        self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
            return_value=document_folder_domain.DocumentFolder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_folder_domain.Name(root="root"),
                created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            )
        )
        self.document_folder_usecase.document_folder_repo.find_descendants_by_id = Mock(return_value=[])
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_repo.find_all_descendants_documents_by_ancestor_folder_id = Mock(
            return_value=[pending_document]
        )

        # Execute & Assert
        with pytest.raises(BadRequest, match="処理中のドキュメントが含まれています"):
            self.document_folder_usecase.move_document_folder(
                tenant, bot_id, document_folder_id, new_parent_document_folder_id
            )

    def test_get_external_root_document_folder_to_sync_for_sharepoint(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        encrypted_credentials = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            raw={
                "tenant_id": "test_tenant_id",
                "client_id": "test_client_id",
                "client_secret": "test_client",
            },
        ).encrypt()
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            encrypted_credentials=encrypted_credentials,
        )

        # Mock
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )

        async def mock_get_external_document_folder_to_sync(*args, **kwargs):
            return document_folder_domain.ExternalDocumentFolderToSync(
                external_id=external_data_connection_domain.ExternalId(
                    root="drive_id:g3d324d,drive_item_id:34cubuobuo43b"
                ),
                name=document_folder_domain.Name(root="testexternalname"),
                is_valid=True,
            )

        self.document_folder_usecase.msgraph_service.get_external_document_folder_to_sync = Mock(
            side_effect=mock_get_external_document_folder_to_sync
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )

        # Call
        self.document_folder_usecase.get_external_root_document_folder_to_sync(
            tenant_id=tenant_id,
            bot_id=bot_id,
            parent_document_folder_id=None,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_data_shared_url="test_shared_url",
        )

        # Assertion
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id,
            external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        )

    def test_get_external_root_document_folder_to_sync_for_box(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        encrypted_credentials = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            raw={
                "client_id": "test_client_id",
                "client_secret": "test_client",
                "enterprise_id": "test_enterprise_id",
            },
        ).encrypt()
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            encrypted_credentials=encrypted_credentials,
        )

        # Mock
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )

        self.document_folder_usecase.msgraph_service.get_external_document_folder_to_sync = Mock(
            return_value=document_folder_domain.ExternalDocumentFolderToSync(
                external_id=external_data_connection_domain.ExternalId(root="id:g3d324d"),
                name=document_folder_domain.Name(root="testexternalname"),
                is_valid=True,
            )
        )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )

        # Call
        self.document_folder_usecase.get_external_root_document_folder_to_sync(
            tenant_id=tenant_id,
            bot_id=bot_id,
            parent_document_folder_id=None,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            external_data_shared_url="test_shared_url",
        )

        # Assertion
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id,
            external_data_connection_domain.ExternalDataConnectionType.BOX,
        )

    def test_start_external_data_connection_for_sharepoint(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        input = StartExternalDataConnectionInput(
            parent_document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb"
            ),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            sync_schedule=external_data_connection_domain.SyncSchedule(root="* * * * *"),
        )

        # Internal values
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=input.external_type,
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={
                    "tenant_id": "test_tenant_id",
                    "client_id": "drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb",
                    "client_secret": "test_client_secret",
                },
            ).encrypt(),
        )
        credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        ).to_sharepoint_credentials()
        external_root_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=input.external_id,
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        delta_token = "test_delta_token"
        external_document_folder_for_create = document_folder_domain.ExternalDocumentFolderForCreate(
            name=external_root_document_folder.name,
            external_id=input.external_id,
            external_type=input.external_type,
            external_updated_at=external_root_document_folder.external_updated_at,
            sync_schedule=input.sync_schedule,
            external_sync_metadata=external_data_connection_domain.ExternalSyncMetadata(
                root={
                    "delta_token": delta_token,
                }
            ),
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now()),
        )
        parent_document_folder = document_folder_domain.DocumentFolder(
            id=input.parent_document_folder_id
            if input.parent_document_folder_id is not None
            else document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_parent_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document_folder = document_folder_domain.DocumentFolder(
            id=external_document_folder_for_create.id,
            name=external_document_folder_for_create.name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        # Mock
        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id = Mock()
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )

        async def mock_get_document_folder_by_id(*args, **kwargs):
            return external_root_document_folder

        self.document_folder_usecase.msgraph_service.get_document_folder_by_id = Mock(
            side_effect=mock_get_document_folder_by_id
        )

        async def mock_get_document_folder_delta_token_by_id(*args, **kwargs):
            return external_data_connection_domain.ExternalSyncMetadata(root={"delta_token": "test_delta_token"})

        self.document_folder_usecase.msgraph_service.get_document_folder_delta_token_by_id = Mock(
            side_effect=mock_get_document_folder_delta_token_by_id
        )

        if input.parent_document_folder_id is None:
            self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
                return_value=parent_document_folder
            )
        else:
            self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(
                return_value=parent_document_folder
            )

        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_folder_repo.create_external_document_folder = Mock(
            return_value=document_folder
        )
        self.document_folder_usecase.queue_storage_service.send_message_to_start_external_data_connection_queue = (
            Mock()
        )

        # Execute
        self.document_folder_usecase.start_external_data_connection(tenant_id, bot_id, input)

        # Test
        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id, input.external_type
        )
        self.document_folder_usecase.msgraph_service.get_document_folder_by_id.assert_called_once_with(
            credentials,
            external_data_connection_domain.SharepointExternalId.from_external_id(input.external_id),
        )
        self.document_folder_usecase.msgraph_service.get_document_folder_delta_token_by_id.assert_called_once_with(
            credentials,
            external_data_connection_domain.SharepointExternalId.from_external_id(input.external_id),
        )
        if input.parent_document_folder_id is None:
            self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.assert_called_once_with(
                bot_id
            )
        else:
            self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(
                input.parent_document_folder_id, bot_id
            )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name.assert_called_once_with(
            parent_document_folder.id, external_root_document_folder.name
        )

        # external_document_folder_for_create.idが自動生成であるため、呼び出し回数のみ検証
        self.document_folder_usecase.document_folder_repo.create_external_document_folder.assert_called_once()

        self.document_folder_usecase.queue_storage_service.send_message_to_start_external_data_connection_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_folder_id=document_folder.id
        )

    def test_start_external_data_connection_for_box(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        input = StartExternalDataConnectionInput(
            parent_document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
            external_id=external_data_connection_domain.ExternalId(root="id:aaaaaaaaa"),
            external_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            sync_schedule=external_data_connection_domain.SyncSchedule(root="* * * * *"),
        )

        # Internal values
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=input.external_type,
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.BOX,
                raw={
                    "client_id": "id:aaaaaaaaa",
                    "client_secret": "test_client_secret",
                    "enterprise_id": "test_enterprise_id",
                },
            ).encrypt(),
        )
        credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        ).to_box_credentials()
        external_root_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=input.external_id,
            external_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        external_document_folder_for_create = document_folder_domain.ExternalDocumentFolderForCreate(
            name=external_root_document_folder.name,
            external_id=input.external_id,
            external_type=input.external_type,
            external_updated_at=external_root_document_folder.external_updated_at,
            sync_schedule=input.sync_schedule,
            external_sync_metadata=external_data_connection_domain.ExternalSyncMetadata(root={}),
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now()),
        )
        parent_document_folder = document_folder_domain.DocumentFolder(
            id=input.parent_document_folder_id
            if input.parent_document_folder_id is not None
            else document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test_parent_document_folder_name"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document_folder = document_folder_domain.DocumentFolder(
            id=external_document_folder_for_create.id,
            name=external_document_folder_for_create.name,
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        # Mock
        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id = Mock()
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )

        self.document_folder_usecase.box_service.get_document_folder_by_id = Mock(
            return_value=external_root_document_folder
        )

        if input.parent_document_folder_id is None:
            self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(
                return_value=parent_document_folder
            )
        else:
            self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(
                return_value=parent_document_folder
            )

        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name = Mock(
            return_value=[]
        )
        self.document_folder_usecase.document_folder_repo.create_external_document_folder = Mock(
            return_value=document_folder
        )
        self.document_folder_usecase.queue_storage_service.send_message_to_start_external_data_connection_queue = (
            Mock()
        )

        # Execute
        self.document_folder_usecase.start_external_data_connection(tenant_id, bot_id, input)

        # Test
        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id, input.external_type
        )
        self.document_folder_usecase.box_service.get_document_folder_by_id.assert_called_once_with(
            credentials,
            external_data_connection_domain.BoxExternalId.from_external_id(input.external_id),
        )
        if input.parent_document_folder_id is None:
            self.document_folder_usecase.document_folder_repo.find_root_document_folder_by_bot_id.assert_called_once_with(
                bot_id
            )
        else:
            self.document_folder_usecase.document_folder_repo.find_by_id_and_bot_id.assert_called_once_with(
                input.parent_document_folder_id, bot_id
            )
        self.document_folder_usecase.document_folder_repo.find_by_parent_document_folder_id_and_name.assert_called_once_with(
            parent_document_folder.id, external_root_document_folder.name
        )

        # external_document_folder_for_create.idが自動生成であるため、呼び出し回数のみ検証
        self.document_folder_usecase.document_folder_repo.create_external_document_folder.assert_called_once()

        self.document_folder_usecase.queue_storage_service.send_message_to_start_external_data_connection_queue.assert_called_once_with(
            tenant_id=tenant_id, bot_id=bot_id, document_folder_id=document_folder.id
        )

    def test_resync_external_document_folder(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        external_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # Mock
        external_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb"
            ),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={
                    "tenant_id": "test_tenant_id",
                    "client_id": "drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb",
                    "client_secret": "test_client_secret",
                },
            ).encrypt(),
        )
        documents_in_folder = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.COMPLETED,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=1),
                document_folder_id=external_document_folder_id,
                created_at=document_domain.CreatedAt(value=datetime.now()),
            )
        ]

        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id = Mock()
        self.document_folder_usecase.document_folder_repo.find_external_document_folder_by_id_and_bot_id = Mock(
            return_value=external_document_folder
        )
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )
        self.document_folder_usecase.document_repo.find_by_parent_document_folder_id = Mock(
            return_value=documents_in_folder
        )

        async def mock_is_authorized_client(*args, **kwargs):
            return True

        self.document_folder_usecase.msgraph_service.is_authorized_client = Mock(side_effect=mock_is_authorized_client)

        # Execute
        self.document_folder_usecase.resync_external_document_folder(tenant_id, bot_id, external_document_folder_id)

        # Test
        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id.assert_called_once_with(bot_id, tenant_id)
        self.document_folder_usecase.document_folder_repo.find_external_document_folder_by_id_and_bot_id.assert_called_once_with(
            external_document_folder_id, bot_id
        )
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id, external_document_folder.external_type
        )
        self.document_folder_usecase.document_repo.find_by_parent_document_folder_id.assert_called_once_with(
            bot_id, external_document_folder_id
        )
        self.document_folder_usecase.msgraph_service.is_authorized_client.assert_called_once_with(
            external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
                external_data_connection.encrypted_credentials,
                external_data_connection.external_data_connection_type,
            ).to_sharepoint_credentials()
        )

    def test_resync_external_document_folder_with_pending_documents(self, setup):
        # Input
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        external_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # Mock
        external_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb"
            ),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={
                    "tenant_id": "test_tenant_id",
                    "client_id": "drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb",
                    "client_secret": "test_client_secret",
                },
            ).encrypt(),
        )
        documents_in_folder = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test_document"),
                memo=document_domain.Memo(value="test_memo"),
                file_extension=document_domain.FileExtension(value="pdf"),
                status=document_domain.Status.PENDING,
                storage_usage=document_domain.StorageUsage(root=10),
                creator_id=user_domain.Id(value=1),
                document_folder_id=external_document_folder_id,
                created_at=document_domain.CreatedAt(value=datetime.now()),
            )
        ]

        self.document_folder_usecase.bot_repo.find_by_id_and_tenant_id = Mock()
        self.document_folder_usecase.document_folder_repo.find_external_document_folder_by_id_and_bot_id = Mock(
            return_value=external_document_folder
        )
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )
        self.document_folder_usecase.document_repo.find_by_parent_document_folder_id = Mock(
            return_value=documents_in_folder
        )

        # Execute & Assert
        with pytest.raises(BadRequest, match="処理中のドキュメントが含まれています。"):
            self.document_folder_usecase.resync_external_document_folder(
                tenant_id, bot_id, external_document_folder_id
            )

    def test_get_external_document_folder_url_for_sharepoint(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        encrypted_credentials = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            raw={
                "tenant_id": "test_tenant_id",
                "client_id": "drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb",
                "client_secret": "test_client",
            },
        ).encrypt()
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            encrypted_credentials=encrypted_credentials,
        )
        external_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=external_data_connection_domain.ExternalId(
                root="drive_id:aaaaaaaaa,drive_item_id:bbbbbbbbbbb"
            ),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )

        # Mock
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.return_value = (
            external_data_connection
        )
        self.document_folder_usecase.document_folder_repo.find_external_document_folder_by_id_and_bot_id.return_value = external_document_folder

        async def mock_get_external_document_folder_url(*args, **kwargs):
            return "test_url"

        self.document_folder_usecase.msgraph_service.get_external_document_folder_url.side_effect = (
            mock_get_external_document_folder_url
        )

        # Execute
        self.document_folder_usecase.get_external_document_folder_url(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        )

        # Test
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id,
            external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        )

    def test_get_external_document_folder_url_for_box(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        encrypted_credentials = external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            raw={
                "client_id": "test_client_id",
                "client_secret": "test_client",
                "enterprise_id": "test_enterprise_id",
            },
        ).encrypt()
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            tenant_id=tenant_id,
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            encrypted_credentials=encrypted_credentials,
        )
        external_document_folder = external_document_folder_domain.ExternalDocumentFolder(
            name=document_folder_domain.Name(root="test_external_document_folder_name"),
            external_id=external_data_connection_domain.ExternalId(root="id:aaaaaaaaa"),
            external_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
            external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.now()),
        )

        # Mock
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.return_value = (
            external_data_connection
        )
        self.document_folder_usecase.document_folder_repo.find_external_document_folder_by_id_and_bot_id.return_value = external_document_folder
        self.document_folder_usecase.box_service.get_external_document_folder_url.return_value = "test_url"

        # Execute
        self.document_folder_usecase.get_external_document_folder_url(
            tenant_id=tenant_id,
            bot_id=bot_domain.Id(value=1),
            document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.BOX,
        )

        # Test
        self.document_folder_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type.assert_called_once_with(
            tenant_id,
            external_data_connection_domain.ExternalDataConnectionType.BOX,
        )
