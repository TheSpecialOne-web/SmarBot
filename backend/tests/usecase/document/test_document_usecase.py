from datetime import datetime, timezone
from unittest.mock import Mock, call
import uuid

from pydantic_core import Url
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
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.libs.exceptions import BadRequest, NotFound
from api.usecase.document import DocumentUseCase
from api.usecase.document.document import (
    CreateDocumentsInput,
    CreateOrUpdateDocumentFeedbackInput,
    GetDocumentDetailOutput,
)
from api.usecase.document.types import DocumentWithCreator


class TestDocumentUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.user_repo = Mock()
        self.bot_repo = Mock()
        self.document_repo = Mock()
        self.document_folder_repo = Mock()
        self.cognitive_search_service = Mock()
        self.blob_storage_service = Mock()
        self.queue_storage_service = Mock()
        self.conversation_repo = Mock()
        self.msgraph_service = Mock()
        self.document_usecase = DocumentUseCase(
            tenant_repo=self.tenant_repo,
            user_repo=self.user_repo,
            bot_repo=self.bot_repo,
            document_repo=self.document_repo,
            document_folder_repo=self.document_folder_repo,
            cognitive_search_service=self.cognitive_search_service,
            blob_storage_service=self.blob_storage_service,
            queue_storage_service=self.queue_storage_service,
            msgraph_service=self.msgraph_service,
        )

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock(return_value=False)
        monkeypatch.setattr("api.usecase.document.document.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def dummy_tenant(self):
        return tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="Test Tenant"),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-index"),
            status=tenant_domain.Status.TRIAL,
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit(
                free_user_seat=50,
                additional_user_seat=10,
                free_token=10000000,
                additional_token=0,
                free_storage=1000000000,
                additional_storage=0,
                document_intelligence_page=8000,
            ),
            container_name=ContainerName(root="test-container"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def dummy_bot_with_tenant(self, bot_id: bot_domain.Id):
        return bot_domain.BotWithTenant(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            tenant=self.dummy_tenant(),
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def dummy_bot(self, bot_id: bot_domain.Id):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
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

    def dummy_document(
        self,
        id: document_domain.Id | None = None,
        name: document_domain.Name | None = None,
        memo: document_domain.Memo | None = None,
        file_extension: document_domain.FileExtension | None = None,
        status: document_domain.Status | None = None,
        created_at: document_domain.CreatedAt | None = None,
        storage_usage: document_domain.StorageUsage | None = None,
        creator_id: user_domain.Id | None = None,
        document_folder_id: document_folder_domain.Id | None = None,
    ):
        return document_domain.Document(
            id=id if id is not None else document_domain.Id(value=1),
            name=name if name is not None else document_domain.Name(value="test_document_name"),
            memo=memo,
            file_extension=file_extension if file_extension is not None else document_domain.FileExtension.PDF,
            status=status if status is not None else document_domain.Status.COMPLETED,
            created_at=created_at
            if created_at is not None
            else document_domain.CreatedAt(value=datetime.now(timezone.utc)),
            storage_usage=storage_usage if storage_usage is not None else document_domain.StorageUsage(root=100),
            creator_id=creator_id if creator_id is not None else user_domain.Id(value=1),
            document_folder_id=document_folder_id
            if document_folder_id is not None
            else document_folder_domain.Id(root=uuid.uuid4()),
        )

    def dummy_document_folder(
        self,
        id: document_folder_domain.Id,
    ):
        return document_folder_domain.DocumentFolder(
            id=id,
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

    def test_create_documents(self, setup, mock_get_feature_flag):
        """ドキュメント作成テスト"""

        mock_get_feature_flag.return_value = True

        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_folder_context = document_folder_domain.DocumentFolderContext(id=document_folder_id, is_root=False)
        documents_for_create = [
            document_domain.DocumentForCreate(
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                data=b"test1",
                creator_id=user_domain.Id(value=1),
            ),
            document_domain.DocumentForCreate(
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                data=b"test2",
                creator_id=user_domain.Id(value=1),
            ),
        ]

        self.document_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        if mock_get_feature_flag.return_value:
            self.document_usecase.tenant_repo.find_by_id.return_value = self.dummy_tenant()
        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name.return_value = None
        if document_folder_id is not None:
            self.document_usecase.document_folder_repo.find_by_id_and_bot_id.return_value = (
                document_folder_domain.DocumentFolder(
                    id=document_folder_id,
                    name=document_folder_domain.Name(root="test-folder"),
                    created_at=document_folder_domain.CreatedAt(root=datetime.now()),
                )
            )
        self.document_usecase.document_repo.create.side_effect = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.PENDING,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.PENDING,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
        ]
        if mock_get_feature_flag.return_value:
            self.document_usecase.blob_storage_service.upload_blob_v2.return_value = None
        else:
            self.document_usecase.blob_storage_service.upload_blob.return_value = None
        self.document_usecase.queue_storage_service.send_messages_to_documents_process_queue.return_value = (
            self.dummy_tenant()
        )

        inputs = CreateDocumentsInput(
            parent_document_folder_id=document_folder_id,
            documents_for_create=documents_for_create,
        )
        self.document_usecase.create_documents(
            tenant=tenant,
            bot_id=bot_id,
            input=inputs,
        )

        self.document_usecase.document_repo.create.assert_has_calls(
            [
                call(
                    bot_id=bot_id,
                    parent_document_folder_id=document_folder_id,
                    document=document_domain.DocumentForCreate(
                        name=document_domain.Name(value="test1"),
                        memo=document_domain.Memo(value="test-memo"),
                        file_extension=document_domain.FileExtension.PDF,
                        data=b"test1",
                        creator_id=user_domain.Id(value=1),
                    ),
                ),
                call(
                    bot_id=bot_id,
                    parent_document_folder_id=document_folder_id,
                    document=document_domain.DocumentForCreate(
                        name=document_domain.Name(value="test2"),
                        memo=document_domain.Memo(value="test-memo"),
                        file_extension=document_domain.FileExtension.PDF,
                        data=b"test2",
                        creator_id=user_domain.Id(value=1),
                    ),
                ),
            ]
        )
        if mock_get_feature_flag.return_value:
            self.document_usecase.blob_storage_service.upload_blob_v2.assert_has_calls(
                [
                    call(
                        container_name=ContainerName(root="test-container"),
                        bot_id=bot_id,
                        document_folder_context=document_folder_context,
                        document_for_create=document_domain.DocumentForCreate(
                            name=document_domain.Name(value="test1"),
                            memo=document_domain.Memo(value="test-memo"),
                            file_extension=document_domain.FileExtension.PDF,
                            data=b"test1",
                            creator_id=user_domain.Id(value=1),
                        ),
                    ),
                    call(
                        container_name=ContainerName(root="test-container"),
                        bot_id=bot_id,
                        document_folder_context=document_folder_context,
                        document_for_create=document_domain.DocumentForCreate(
                            name=document_domain.Name(value="test2"),
                            memo=document_domain.Memo(value="test-memo"),
                            file_extension=document_domain.FileExtension.PDF,
                            data=b"test2",
                            creator_id=user_domain.Id(value=1),
                        ),
                    ),
                ]
            )
        else:
            self.document_usecase.blob_storage_service.upload_blob.assert_has_calls(
                [
                    call(
                        container_name=ContainerName(root="test-container"),
                        document_folder_context=document_folder_context,
                        document_for_create=document_domain.DocumentForCreate(
                            name=document_domain.Name(value="test1"),
                            memo=document_domain.Memo(value="test-memo"),
                            file_extension=document_domain.FileExtension.PDF,
                            data=b"test1",
                            creator_id=user_domain.Id(value=1),
                        ),
                    ),
                    call(
                        container_name=ContainerName(root="test-container"),
                        document_folder_context=document_folder_context,
                        document_for_create=document_domain.DocumentForCreate(
                            name=document_domain.Name(value="test2"),
                            memo=document_domain.Memo(value="test-memo"),
                            file_extension=document_domain.FileExtension.PDF,
                            data=b"test2",
                            creator_id=user_domain.Id(value=1),
                        ),
                    ),
                ]
            )
        self.document_usecase.queue_storage_service.send_messages_to_documents_process_queue.assert_called_once_with(
            tenant.id,
            bot_id,
            [
                document_domain.Id(value=1),
                document_domain.Id(value=2),
            ],
        )

    def test_get_documents_with_parent_folder(self, setup):
        """親フォルダ指定でドキュメント取得テスト"""
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_id,
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        want = [
            DocumentWithCreator(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=document_folder_id,
            ),
            DocumentWithCreator(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=document_folder_id,
            ),
        ]

        test_user = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test-user"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        test_documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
        ]

        self.document_usecase.user_repo.find_by_tenant_id.return_value = [test_user]
        self.document_usecase.document_folder_repo.find_by_id_and_bot_id.return_value = document_folder

        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id.return_value = test_documents

        got = self.document_usecase.get_documents(tenant_id, bot_id, document_folder_id)

        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id.assert_called_once_with(
            bot_id, document_folder_id
        )
        self.document_usecase.user_repo.find_by_tenant_id.assert_called_once_with(tenant_id)

        for g, e in zip(got.documents, want):
            g_dict = g.model_dump(exclude={"created_at"})
            e_dict = e.model_dump(exclude={"created_at"})
            assert g_dict == e_dict

    def test_get_documents_without_parent_folder(self, setup):
        """親フォルダ指定なしでドキュメント取得テスト"""
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        root_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        root_document_folder = document_folder_domain.DocumentFolder(
            id=root_document_folder_id,
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        want = [
            DocumentWithCreator(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=root_document_folder_id,
            ),
            DocumentWithCreator(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=root_document_folder_id,
            ),
        ]

        test_user = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test-user"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        test_documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=root_document_folder_id,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=root_document_folder_id,
            ),
        ]

        self.document_usecase.user_repo.find_by_tenant_id.return_value = [test_user]
        self.document_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            root_document_folder
        )

        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id.return_value = test_documents

        got = self.document_usecase.get_documents(tenant_id, bot_id, None)

        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id.assert_called_once_with(
            bot_id, root_document_folder_id
        )
        self.document_usecase.user_repo.find_by_tenant_id.assert_called_once_with(tenant_id)

        for g, e in zip(got.documents, want):
            g_dict = g.model_dump(exclude={"created_at"})
            e_dict = e.model_dump(exclude={"created_at"})
            assert g_dict == e_dict

    def test_get_all_documents(self, setup):
        """アシスタントのドキュメント全取得テスト"""

        # Input
        bot_id = bot_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        document_folder_id1 = document_folder_domain.Id(root=uuid.uuid4())
        document_folder_id2 = document_folder_domain.Id(root=uuid.uuid4())

        want = [
            DocumentWithCreator(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=document_folder_id1,
            ),
            DocumentWithCreator(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                creator_name=user_domain.Name(value="test-user"),
                document_folder_id=document_folder_id2,
            ),
        ]

        test_user = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test-user"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        test_documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id1,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id2,
            ),
        ]

        # Mock
        self.document_usecase.user_repo.find_by_tenant_id = Mock(return_value=[test_user])
        self.document_usecase.document_repo.find_by_bot_id = Mock(return_value=test_documents)

        # Execute
        got = self.document_usecase.get_all_documents(tenant_id, bot_id)

        # Test
        self.document_usecase.user_repo.find_by_tenant_id.assert_called_once_with(tenant_id)

        for g, e in zip(got.documents, want):
            g_dict = g.model_dump(exclude={"created_at"})
            e_dict = e.model_dump(exclude={"created_at"})
            assert g_dict == e_dict

    def test_get_document_detail(self, setup, mock_get_feature_flag):
        """ドキュメント詳細取得テスト"""

        test_user = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test-user"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        # Input
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        root_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )
        document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=root_folder.id,
        )
        find_with_ancestors_by_id_and_bot_id_return_value = document_folder_domain.DocumentFolderWithAncestors(
            id=root_folder.id,
            name=root_folder.name,
            created_at=root_folder.created_at,
            ancestor_folders=[],
        )

        # Expected
        expected_output = GetDocumentDetailOutput(
            # DocumentWithCreator props
            id=document.id,
            name=document.name,
            memo=document.memo,
            file_extension=document.file_extension,
            status=document.status,
            created_at=document.created_at,
            storage_usage=document.storage_usage,
            creator_id=document.creator_id,
            creator_name=user_domain.Name(value="test-user"),
            document_folder_id=document.document_folder_id,
            signed_url_original=document_domain.SignedUrl(value="https://test.com"),
            signed_url_pdf=None,
            document_folder_name=root_folder.name,
            document_folder_created_at=root_folder.created_at,
            document_folder_ancestor_folders=[],
        )

        # Mock
        mock_get_feature_flag.return_value = True
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.document_usecase.user_repo.find_by_id_and_tenant_id = Mock(return_value=test_user)
        self.document_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=find_with_ancestors_by_id_and_bot_id_return_value
        )
        self.document_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(return_value=root_folder)
        if mock_get_feature_flag.return_value:
            self.document_usecase.blob_storage_service.create_blob_sas_url_v2 = Mock(
                return_value=document_domain.SignedUrl(value="https://test.com")
            )
        else:
            self.document_usecase.blob_storage_service.create_blob_sas_url = Mock(
                return_value=document_domain.SignedUrl(value="https://test.com")
            )

        # Execute
        output = self.document_usecase.get_document_detail(tenant, bot_id, document.id)

        # Test
        assert output == expected_output

    def test_get_external_document_detail(self, setup, mock_get_feature_flag):
        """外部データ連携ドキュメント詳細取得テスト"""

        test_user = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test-user"),
            email=user_domain.Email(value="test@test.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        # Input
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        external_data_connection = external_data_connection_domain.ExternalDataConnection(
            tenant_id=tenant_domain.Id(value=1),
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            id=external_data_connection_domain.Id(root=uuid.uuid4()),
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={"client_id": "test", "client_secret": "test", "tenant_id": "test"},
            ).encrypt(),
        )
        external_url = external_data_connection_domain.ExternalUrl(root=Url("https://test.com"))
        document_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
            external_id=external_data_connection_domain.ExternalId(root="drive_id:testtest,drive_item_id:testtest"),
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        )
        document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder.id,
            external_id=external_data_connection_domain.ExternalId(root="drive_id:testtest,drive_item_id:testtest"),
        )
        find_with_ancestors_by_id_and_bot_id_return_value = document_folder_domain.DocumentFolderWithAncestors(
            id=document_folder.id,
            name=document_folder.name,
            created_at=document_folder.created_at,
            ancestor_folders=[],
            external_id=document_folder.external_id,
            external_type=document_folder.external_type,
        )
        root_folder = document_folder_domain.DocumentFolder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root="test-folder"),
            created_at=document_folder_domain.CreatedAt(root=datetime.now()),
        )

        # Expected
        expected_output = GetDocumentDetailOutput(
            id=document.id,
            name=document.name,
            memo=document.memo,
            file_extension=document.file_extension,
            status=document.status,
            created_at=document.created_at,
            storage_usage=document.storage_usage,
            creator_id=document.creator_id,
            creator_name=user_domain.Name(value="test-user"),
            document_folder_id=document.document_folder_id,
            signed_url_original=document_domain.SignedUrl(value="https://test.com"),
            signed_url_pdf=None,
            external_url=external_url,
            document_folder_name=document_folder.name,
            document_folder_created_at=document_folder.created_at,
            document_folder_ancestor_folders=[],
        )

        # Mock
        mock_get_feature_flag.return_value = True
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.document_usecase.user_repo.find_by_id_and_tenant_id = Mock(return_value=test_user)
        self.document_usecase.document_folder_repo.find_with_ancestors_by_id_and_bot_id = Mock(
            return_value=find_with_ancestors_by_id_and_bot_id_return_value
        )
        self.document_usecase.document_folder_repo.find_root_document_folder_by_bot_id = Mock(return_value=root_folder)
        self.document_usecase.blob_storage_service.create_external_blob_sas_url = Mock(
            return_value=document_domain.SignedUrl(value="https://test.com")
        )
        self.document_usecase.tenant_repo.get_external_data_connection_by_tenant_id_and_type = Mock(
            return_value=external_data_connection
        )

        async def mock_get_external_document_url(*args, **kwargs):
            return external_url

        self.document_usecase.msgraph_service.get_external_document_url = Mock(
            side_effect=mock_get_external_document_url
        )

        # Execute
        output = self.document_usecase.get_document_detail(tenant, bot_id, document.id)

        # Test
        assert output == expected_output

    def test_delete_document(self, setup, mock_get_feature_flag):
        """ドキュメント削除テスト"""

        mock_get_feature_flag.return_value = True

        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_folder_context = document_folder_domain.DocumentFolderContext(id=document_folder_id, is_root=False)
        document_id = document_domain.Id(value=1)
        document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
        )
        tenant = self.dummy_tenant()

        self.document_usecase.bot_repo.find_by_id.return_value = self.dummy_bot_with_tenant(bot_id)
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document
        self.document_usecase.cognitive_search_service.delete_documents_from_index_by_document_id.return_value = None
        if mock_get_feature_flag.return_value:
            self.document_usecase.blob_storage_service.delete_document_blob_v2.return_value = None
        else:
            self.document_usecase.blob_storage_service.delete_document_blob.return_value = None
        self.document_usecase.document_repo.delete.return_value = None

        self.document_usecase.delete_document(tenant, bot_id, document_id)

        self.document_usecase.bot_repo.find_by_id.assert_called_once_with(bot_id)
        self.document_usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(
            id=document_id, bot_id=bot_id
        )
        self.document_usecase.cognitive_search_service.delete_documents_from_index_by_document_id.assert_called_once_with(
            endpoint=tenant.search_service_endpoint, index_name=tenant.index_name, document_id=document_id
        )
        if mock_get_feature_flag.return_value:
            self.document_usecase.blob_storage_service.delete_document_blob_v2.assert_called_once_with(
                container_name=ContainerName(root="test-container"),
                bot_id=bot_id,
                document_folder_context=document_folder_context,
                blob_name=document.blob_name_v2,
            )
        else:
            self.document_usecase.blob_storage_service.delete_document_blob.assert_called_once_with(
                container_name=ContainerName(root="test-container"),
                document_folder_context=document_folder_context,
                blob_name=document.blob_name,
            )
        self.document_usecase.document_repo.delete.assert_called_once_with(document_id)

    def test_delete_document_pending(self, setup, mock_get_feature_flag):
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_id = document_domain.Id(value=1)
        document = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.PENDING,
            created_at=document_domain.CreatedAt(value=datetime.now()),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
        )

        self.document_usecase.bot_repo.find_by_id.return_value = self.dummy_bot_with_tenant(bot_id)
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document

        with pytest.raises(BadRequest):
            self.document_usecase.delete_document(tenant, bot_id, document_id)

    def test_update_document(self, setup):
        """ドキュメント更新テスト"""
        now = datetime.now()
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_id = document_domain.Id(value=1)
        self.document_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=now),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
        )
        self.document_usecase.document_repo.update.return_value = None

        input = document_domain.DocumentForUpdate(
            basename=None,
            memo=document_domain.Memo(value="test-memo-update"),
        )

        self.document_usecase.update_document(bot_id, document_id, input)

        self.document_usecase.bot_repo.find_by_id.assert_called_once_with(bot_id)
        self.document_usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo-update"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=now),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            )
        )

    def test_update_document_v2_memo(self, setup):
        """ドキュメント更新テスト (メモ)"""
        now = datetime.now()
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_id = document_domain.Id(value=1)

        self.document_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document_domain.Document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo"),
            file_extension=document_domain.FileExtension.PDF,
            status=document_domain.Status.COMPLETED,
            created_at=document_domain.CreatedAt(value=now),
            storage_usage=document_domain.StorageUsage(root=100),
            creator_id=user_domain.Id(value=1),
            document_folder_id=document_folder_id,
        )
        self.document_usecase.document_repo.update.return_value = None

        input = document_domain.DocumentForUpdate(
            basename=document_domain.Name(value="test1"),
            memo=document_domain.Memo(value="test-memo-update"),
        )

        self.document_usecase.update_document_v2(tenant, bot_id, document_id, input)

        self.document_usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo-update"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=now),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            )
        )

    def test_update_document_v2_name(self, setup):
        """ドキュメント更新テスト (名前)"""
        # Input
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        old_document_name = document_domain.Name(value="old_document_name")
        new_document_name = document_domain.Name(value="new_document_name")
        document = self.dummy_document(name=old_document_name)
        input = document_domain.DocumentForUpdate(
            basename=new_document_name,
            memo=None,
        )

        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=document.document_folder_id,
            is_root=False,
        )

        # Mock
        self.document_usecase.bot_repo.find_by_id = Mock(return_value=self.dummy_bot(bot_id))
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(return_value=document)
        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name = Mock(
            side_effect=NotFound("Bot not found")
        )
        self.document_usecase.document_repo.update = Mock(return_value=None)

        # # Execute
        self.document_usecase.update_document_v2(tenant, bot_id, document.id, input)

        # Assert
        self.document_usecase.blob_storage_service.update_document_blob_name.assert_called_once_with(
            container_name=tenant.container_name,
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            old_blob_name=old_document_name.to_displayable_blob_name(document.file_extension),
            new_blob_name=new_document_name.to_displayable_blob_name(document.file_extension),
        )

        self.document_usecase.queue_storage_service.send_message_to_sync_document_name_queue.assert_called_once_with(
            tenant.id, bot_id, document.id
        )

    def test_delete_documents(self, setup):
        """複数ドキュメント削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_ids = [document_domain.Id(value=1), document_domain.Id(value=2)]
        now = datetime.now()
        documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=now),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=now),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
        ]
        self.document_usecase.bot_repo.find_with_tenant_by_id.return_value = self.dummy_bot_with_tenant(bot_id)
        self.document_usecase.document_repo.find_by_ids_and_bot_id.return_value = documents
        self.document_usecase.document_repo.update.return_value = None
        self.document_usecase.queue_storage_service.send_message_to_delete_multiple_documents_queue.return_value = None

        self.document_usecase.delete_documents(bot_id, document_ids)
        self.document_usecase.bot_repo.find_with_tenant_by_id.assert_called_once_with(bot_id)
        self.document_usecase.document_repo.find_by_ids_and_bot_id.assert_called_once_with(bot_id, document_ids)
        self.document_usecase.document_repo.update.assert_has_calls(
            [
                call(
                    document_domain.Document(
                        id=document_domain.Id(value=1),
                        name=document_domain.Name(value="test1"),
                        memo=document_domain.Memo(value="test-memo"),
                        file_extension=document_domain.FileExtension.PDF,
                        status=document_domain.Status.DELETING,
                        created_at=document_domain.CreatedAt(value=now),
                        storage_usage=document_domain.StorageUsage(root=100),
                        creator_id=user_domain.Id(value=1),
                        document_folder_id=document_folder_id,
                    )
                ),
                call(
                    document_domain.Document(
                        id=document_domain.Id(value=2),
                        name=document_domain.Name(value="test2"),
                        memo=document_domain.Memo(value="test-memo"),
                        file_extension=document_domain.FileExtension.PDF,
                        status=document_domain.Status.DELETING,
                        created_at=document_domain.CreatedAt(value=now),
                        storage_usage=document_domain.StorageUsage(root=200),
                        creator_id=user_domain.Id(value=1),
                        document_folder_id=document_folder_id,
                    )
                ),
            ]
        )
        self.document_usecase.queue_storage_service.send_message_to_delete_multiple_documents_queue.assert_called_once_with(
            tenant_id, bot_id, document_ids
        )

    def test_delete_documents_pending(self, setup):
        bot_id = bot_domain.Id(value=1)
        document_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        document_ids = [document_domain.Id(value=1), document_domain.Id(value=2)]

        documents = [
            document_domain.Document(
                id=document_domain.Id(value=1),
                name=document_domain.Name(value="test1"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.PENDING,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
            document_domain.Document(
                id=document_domain.Id(value=2),
                name=document_domain.Name(value="test2"),
                memo=document_domain.Memo(value="test-memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=200),
                creator_id=user_domain.Id(value=1),
                document_folder_id=document_folder_id,
            ),
        ]
        self.document_usecase.bot_repo.find_with_tenant_by_id.return_value = self.dummy_bot_with_tenant(bot_id)
        self.document_usecase.document_repo.find_by_ids_and_bot_id.return_value = documents

        with pytest.raises(BadRequest):
            self.document_usecase.delete_documents(bot_id, document_ids)

    def test_create_or_update_document_feedback_case_create(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        input = CreateOrUpdateDocumentFeedbackInput(
            bot_id=bot_id,
            document_id=document_id,
            user_id=user_id,
            evaluation=document_feedback_domain.Evaluation.GOOD,
        )

        # Mock
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(
            return_value=document_domain.Document(
                id=document_id,
                document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_domain.Name(value="test"),
                memo=document_domain.Memo(value="test"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
            )
        )
        self.document_usecase.document_repo.find_feedback_by_id_and_user_id = Mock(side_effect=NotFound("Not found"))
        self.document_usecase.document_repo.create_feedback = Mock(return_value=None)

        # Execute
        self.document_usecase.create_or_update_document_feedback(input=input)

        # Assert
        self.document_usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(
            input.document_id, input.bot_id
        )
        self.document_usecase.document_repo.find_feedback_by_id_and_user_id.assert_called_once_with(
            input.document_id, input.user_id
        )
        self.document_usecase.document_repo.create_feedback.assert_called_once_with(
            document_feedback_domain.DocumentFeedback(
                user_id=input.user_id,
                document_id=input.document_id,
                evaluation=input.evaluation,
            ),
        )

    def test_create_or_update_document_feedback_case_update(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        input = CreateOrUpdateDocumentFeedbackInput(
            bot_id=bot_id,
            document_id=document_id,
            user_id=user_id,
            evaluation=document_feedback_domain.Evaluation.GOOD,
        )

        # Mock
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(
            return_value=document_domain.Document(
                id=document_id,
                document_folder_id=document_folder_domain.Id(root=uuid.uuid4()),
                name=document_domain.Name(value="test"),
                memo=document_domain.Memo(value="test"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                created_at=document_domain.CreatedAt(value=datetime.now()),
                storage_usage=document_domain.StorageUsage(root=100),
                creator_id=user_domain.Id(value=1),
            )
        )
        self.document_usecase.document_repo.find_feedback_by_id_and_user_id = Mock(
            return_value=document_feedback_domain.DocumentFeedback(
                user_id=user_id,
                document_id=document_id,
                evaluation=document_feedback_domain.Evaluation.BAD,
            )
        )
        self.document_usecase.document_repo.update_feedback = Mock(return_value=None)

        # Execute
        self.document_usecase.create_or_update_document_feedback(input=input)

        # Assert
        self.document_usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(
            input.document_id, input.bot_id
        )
        self.document_usecase.document_repo.find_feedback_by_id_and_user_id.assert_called_once_with(
            input.document_id, input.user_id
        )
        self.document_usecase.document_repo.update_feedback.assert_called_once_with(
            document_feedback_domain.DocumentFeedback(
                user_id=input.user_id,
                document_id=input.document_id,
                evaluation=input.evaluation,
            ),
        )

    def test_create_or_update_document_feedback_case_document_not_found(self, setup):
        # Input
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        input = CreateOrUpdateDocumentFeedbackInput(
            bot_id=bot_id,
            document_id=document_id,
            user_id=user_id,
            evaluation=document_feedback_domain.Evaluation.GOOD,
        )

        # Mock
        self.document_usecase.document_repo.find_by_id_and_bot_id = Mock(side_effect=NotFound("Not found"))

        # Execute
        with pytest.raises(NotFound):
            self.document_usecase.create_or_update_document_feedback(input=input)

        # Assert
        self.document_usecase.document_repo.find_by_id_and_bot_id.assert_called_once_with(
            input.document_id, input.bot_id
        )

    def test_move_document(self, setup):
        # Input
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        new_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # Mock
        old_document_folder = self.dummy_document_folder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
        )
        bot = self.dummy_bot(bot_id=bot_id)
        document = self.dummy_document(id=document_id)

        self.document_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document
        self.document_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            self.dummy_document_folder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
            )
        )
        self.document_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(
            side_effect=[old_document_folder, self.dummy_document_folder(id=new_document_folder_id)]
        )
        self.document_usecase.document_folder_repo.find_by_id_and_bot_id.return_value = self.dummy_document_folder(
            id=new_document_folder_id,
        )
        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name = Mock(
            side_effect=NotFound("Bot not found")
        )

        # Execute
        self.document_usecase.move_document(tenant, bot.id, document.id, new_document_folder_id)

        # Assert
        self.document_usecase.document_repo.update.assert_called_once_with(
            document_domain.Document(
                id=document_id,
                name=document.name,
                memo=document.memo,
                file_extension=document.file_extension,
                storage_usage=document.storage_usage,
                creator_id=document.creator_id,
                created_at=document.created_at,
                document_folder_id=new_document_folder_id,
                status=document_domain.Status.PENDING,
            )
        )
        self.document_usecase.blob_storage_service.update_document_folder_path.assert_called_once_with(
            container_name=tenant.container_name,
            bot_id=bot.id,
            old_document_folder_context=document_folder_domain.DocumentFolderContext(
                id=old_document_folder.id, is_root=False
            ),
            new_document_folder_context=document_folder_domain.DocumentFolderContext(
                id=new_document_folder_id, is_root=False
            ),
            blob_name=document.name.to_displayable_blob_name(document.file_extension),
        )

    def test_move_document_same_name_file_in_new_folder(self, setup):
        # Input
        tenant = self.dummy_tenant()
        bot_id = bot_domain.Id(value=1)
        document_id = document_domain.Id(value=1)
        new_document_folder_id = document_folder_domain.Id(root=uuid.uuid4())

        # Mock
        old_document_folder = self.dummy_document_folder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
        )
        bot = self.dummy_bot(bot_id=bot_id)
        document = self.dummy_document(id=document_id)

        self.document_usecase.bot_repo.find_by_id_and_tenant_id.return_value = bot
        self.document_usecase.document_repo.find_by_id_and_bot_id.return_value = document
        self.document_usecase.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            self.dummy_document_folder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
            )
        )
        self.document_usecase.document_folder_repo.find_by_id_and_bot_id = Mock(
            side_effect=[old_document_folder, self.dummy_document_folder(id=new_document_folder_id)]
        )
        self.document_usecase.document_folder_repo.find_by_id_and_bot_id.return_value = self.dummy_document_folder(
            id=new_document_folder_id,
        )
        self.document_usecase.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name.return_value = (
            self.dummy_document()
        )

        # Assert
        with pytest.raises(BadRequest):
            self.document_usecase.move_document(tenant, bot.id, document.id, new_document_folder_id)
