import datetime
import re
from unittest.mock import MagicMock
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
from api.domain.models.search.chunk import DocumentChunk, UrsaDocumentChunk
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
                    value=approach_variable_domain.Value(value="https://test-search-service-endpoint.com"),
                ),
            ],
        )

    def dummy_document(
        self,
        id: document_domain.Id,
        name: document_domain.Name,
        document_folder_id: document_folder_domain.Id,
        memo: document_domain.Memo | None = None,
    ):
        return document_domain.Document(
            id=id,
            name=name,
            memo=memo,
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

    def dummy_document_folder_with_ursa_name(self, name: str, order: int):
        return document_folder_domain.DocumentFolderWithOrder(
            id=document_folder_domain.Id(root=uuid.uuid4()),
            name=document_folder_domain.Name(root=name),
            created_at=document_folder_domain.CreatedAt(root=datetime.datetime.now()),
            order=document_folder_domain.Order(root=order),
        )

    def dummy_document_chunk(
        self,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document_folder_id: document_folder_domain.Id,
        content: str,
        blob_path: str,
    ):
        return DocumentChunk(
            id=str(uuid.uuid4()),
            bot_id=bot_id.value,
            data_source_id=str(uuid.uuid4()),
            document_id=document_id.value,
            document_folder_id=str(document_folder_id.root),
            content=content,
            blob_path=blob_path,
            file_name="test",
            file_extension="pdf",
            page_number=1,
            is_vectorized=False,
            title_vector=None,
            content_vector=None,
            external_id=None,
            parent_external_id=None,
        )

    def dummy_ursa_document_chunk(
        self,
        document_id: document_domain.Id,
        document_folder_id: document_folder_domain.Id,
        memo_str: str,
    ):
        # 設備工事のみ対応なので、他ドキュメントは注意
        # 例：Z:\\共有ドライブ\\長崎\\設備工事\\2020年度R02\\【村川】53_管内電気所社内電話整備（長崎支社：２０２０）\\03 工事計画・伺書\\01 伺書\\【まとめ】伺書_xdw.pdf
        delimiter = "\\" if "\\" in memo_str else "/"
        test_branch = memo_str.split(delimiter)[2]
        test_file_name = memo_str.split(delimiter)[-1]
        test_construction = memo_str.split(delimiter)[5]
        test_author = ""
        author_match = re.findall(r"【(.*?)】", test_construction)
        if author_match:
            test_author = author_match[0]
        test_interpolation_path = delimiter.join(memo_str.split(delimiter)[6:-1])
        test_year = 0
        try:
            year_match = re.search(r"\d{4}", memo_str.split(delimiter)[4])
            if year_match:
                test_year = int(year_match.group(0))
        except Exception:
            pass
        test_extension = memo_str.split(".")[-1]
        return UrsaDocumentChunk(
            id=str(uuid.uuid4()),
            content="test",
            file_name=test_file_name,
            construction_name=test_construction,
            author=test_author,
            year=test_year,
            branch=test_branch,
            document_type="",
            interpolation_path=test_interpolation_path,
            full_path=memo_str,
            extension=test_extension,
            source_file="",
            sourceid="",
            document_id=document_id.value,
            document_folder_id=str(document_folder_id.root),
            external_id=None,
            parent_external_id=None,
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

    def test_sync_document_location(self, setup):
        # dummy data
        self.use_case.tenant_repo.find_by_id.return_value = self.tenant
        bot = self.dummy_bot(bot_id=bot_domain.Id(value=1))
        self.use_case.bot_repo.find_by_id_and_tenant_id.return_value = bot

        old_document_parent_folder_id = document_folder_domain.Id(root=uuid.uuid4())
        new_document_parent_folder = self.dummy_document_folder_with_order(order=3)
        document = self.dummy_document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value="test"),
            document_folder_id=new_document_parent_folder.id,
        )
        self.use_case.document_repo.find_by_id_and_bot_id.return_value = document
        self.use_case.document_repo.find_with_ancestor_folders_by_id.return_value = (
            document_domain.DocumentWithAncestorFolders(
                **self.dummy_document(
                    id=document_domain.Id(value=1),
                    name=document_domain.Name(value="test"),
                    document_folder_id=new_document_parent_folder.id,
                ).model_dump(),
                ancestor_folders=[
                    self.dummy_document_folder_with_order(order=1),
                    self.dummy_document_folder_with_order(order=2),
                    new_document_parent_folder,
                ],
            )
        )
        self.use_case.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            document_folder_domain.DocumentFolder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=None,
                created_at=document_folder_domain.CreatedAt(root=datetime.datetime.now()),
            )
        )
        document_chunk = self.dummy_document_chunk(
            bot_id=bot_domain.Id(value=1),
            document_id=document_domain.Id(value=1),
            document_folder_id=new_document_parent_folder.id,
            content="[test1/test2/test]:test",
            blob_path=f"{bot.id.value}/{old_document_parent_folder_id.root}/{document.name.value}.{document.file_extension.value}",
        )

        self.use_case.cognitive_search_service.find_index_documents_by_document_ids.return_value = [document_chunk]
        # execute
        self.use_case.sync_document_location(
            tenant_id=tenant_domain.Id(value=1),
            bot_id=bot_domain.Id(value=1),
            document_id=document_domain.Id(value=1),
        )
        self.use_case.document_repo.update.assert_called_once_with(document)
        self.use_case.cognitive_search_service.create_or_update_document_chunks.assert_called_once_with(
            endpoint=self.tenant.search_service_endpoint,
            index_name=self.tenant.index_name,
            documents=[
                DocumentChunk(
                    id=document_chunk.id,
                    bot_id=bot.id.value,
                    data_source_id=document_chunk.data_source_id,
                    document_id=document.id.value,
                    file_name=document.name.value,
                    file_extension=document.file_extension.value,
                    page_number=document_chunk.page_number,
                    is_vectorized=document_chunk.is_vectorized,
                    title_vector=document_chunk.title_vector,
                    content_vector=document_chunk.content_vector,
                    content="[test1/test2/test3/test]:test",
                    blob_path=f"{bot.id.value}/{new_document_parent_folder.id.root}/{document.name.value}.{document.file_extension.value}",
                    document_folder_id=str(new_document_parent_folder.id.root),
                    created_at=document_chunk.created_at,
                    updated_at=document_chunk.updated_at,
                    external_id=document_chunk.external_id,
                    parent_external_id=document_chunk.parent_external_id,
                )
            ],
        )

    def test_sync_ursa_document_location(self, setup):
        # dummy data
        self.use_case.tenant_repo.find_by_id.return_value = self.tenant
        bot = self.dummy_bot(bot_id=bot_domain.Id(value=1), approach=bot_domain.Approach.URSA)
        self.use_case.bot_repo.find_by_id_and_tenant_id.return_value = bot

        old_memo_str = "Z:\\共有ドライブ\\長崎\\設備工事\\2020年度R02\\【村川】53_管内電気所社内電話整備（長崎支社：２０２０）\\03 工事計画・伺書\\01 伺書\\【まとめ】伺書_xdw.pdf"
        new_memo_str = "Z:\\共有ドライブ\\長崎\\設備工事\\2020年度R02\\【村川】53_管内電気所社内電話整備（長崎支社：２０２０）\\50 作業票（入所関係）\\03 入所手続き\\02 新設工事\\【まとめ】伺書_xdw.pdf"
        delimiter = "\\" if "\\" in old_memo_str else "/"
        file_basename = old_memo_str.split(delimiter)[-1].split(".")[0]

        old_document_parent_folder_id = document_folder_domain.Id(root=uuid.uuid4())  # 原田メモ：移動する前のフォルダ
        new_document_parent_folder = self.dummy_document_folder_with_ursa_name(name="02 新設工事", order=8)
        document = self.dummy_document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value=file_basename),
            document_folder_id=new_document_parent_folder.id,
            memo=document_domain.Memo(value=old_memo_str),
        )  # 原田メモ：更新する対象のドキュメントのDBに入るレコード
        self.use_case.document_repo.find_by_id_and_bot_id.return_value = document
        self.use_case.document_repo.find_with_ancestor_folders_by_id.return_value = (
            document_domain.DocumentWithAncestorFolders(
                **self.dummy_document(
                    id=document_domain.Id(value=1),
                    name=document_domain.Name(value=file_basename),
                    document_folder_id=new_document_parent_folder.id,
                    memo=document_domain.Memo(value=new_memo_str),
                ).model_dump(),
                ancestor_folders=[
                    self.dummy_document_folder_with_ursa_name(name="共有ドライブ", order=1),
                    self.dummy_document_folder_with_ursa_name(name="長崎", order=2),
                    self.dummy_document_folder_with_ursa_name(name="設備工事", order=3),
                    self.dummy_document_folder_with_ursa_name(name="2020年度R02", order=4),
                    self.dummy_document_folder_with_ursa_name(
                        name="【村川】53_管内電気所社内電話整備（長崎支社：２０２０）", order=5
                    ),
                    self.dummy_document_folder_with_ursa_name(name="50 作業票（入所関係）", order=6),
                    self.dummy_document_folder_with_ursa_name(name="03 入所手続き", order=7),
                    new_document_parent_folder,
                ],
            )
        )

        self.use_case.document_folder_repo.find_root_document_folder_by_bot_id.return_value = (
            document_folder_domain.DocumentFolder(
                id=document_folder_domain.Id(root=uuid.uuid4()),
                name=None,
                created_at=document_folder_domain.CreatedAt(root=datetime.datetime.now()),
            )
        )  # これはursaで使わないので無視

        document_chunk = self.dummy_ursa_document_chunk(
            document_id=document_domain.Id(value=1),
            document_folder_id=old_document_parent_folder_id,
            memo_str=old_memo_str,
        )  # 変更前のドキュメントから取って来られるAI Searchのドキュメント

        self.use_case.cognitive_search_service.find_ursa_index_documents_by_document_ids.return_value = [
            document_chunk
        ]

        updated_document = self.dummy_document(
            id=document_domain.Id(value=1),
            name=document_domain.Name(value=file_basename),
            document_folder_id=new_document_parent_folder.id,
            memo=document_domain.Memo(value=new_memo_str),
        )
        updated_document.created_at = document.created_at

        # execute
        self.use_case.sync_document_location(
            tenant_id=tenant_domain.Id(value=1),
            bot_id=bot_domain.Id(value=1),
            document_id=document_domain.Id(value=1),
        )
        self.use_case.document_repo.update.assert_called_once_with(updated_document)
