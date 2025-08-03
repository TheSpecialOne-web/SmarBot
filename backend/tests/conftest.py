from dotenv import load_dotenv

load_dotenv(".env")

import os

os.environ["DB_NAME"] = "test_neosmartchat"

import datetime
import random
import string
from typing import Any, Generator, Tuple
from uuid import uuid4

from alembic.command import upgrade
from alembic.config import Config
import pytest
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from api.database import SessionFactory
from api.domain.models import (
    api_key as api_key_domain,
    attachment as attachment_domain,
    bot as bot_domain,
    bot_template as bot_template_domain,
    chat_completion as chat_completion_domain,
    chat_completion_export as chat_completion_export_domain,
    common_document_template as cdt_domain,
    common_prompt_template as cpt_domain,
    conversation as conversation_domain,
    conversation_export as conversation_export_domain,
    data_point,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    notification as notification_domain,
    prompt_template as prompt_template_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
    term as term_domain,
    token as token_domain,
    user as user_domain,
    workflow as workflow_domain,
    workflow_thread as wf_thread_domain,
)
from api.domain.models.bot import (
    Bot,
    approach_variable as av_domain,
    prompt_template as bot_prompt_template_domain,
)
from api.domain.models.conversation import (
    conversation_data_point as conversation_data_point_domain,
    conversation_turn as conversation_turn_domain,
)
from api.domain.models.conversation.conversation import Id as ConversationId
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.document_folder import external_data_connection as external_document_folder_domain
from api.domain.models.llm import AllowForeignRegion, ModelName
from api.domain.models.llm.model import ModelFamily
from api.domain.models.metering import PDFParserCountType
from api.domain.models.metering.meter import Meter, PdfParserMeterForCreate
from api.domain.models.metering.quantity import Quantity
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import (
    Tenant,
    TenantForCreate,
    external_data_connection as external_data_connection_domain,
)
from api.domain.models.tenant.tenant_alert import tenant_alert as tenant_alert_domain
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.domain.models.workflow_thread import (
    workflow_thread_flow as wf_thread_flow_domain,
    workflow_thread_flow_step as wf_thread_flow_step_domain,
)
from api.infrastructures.postgres.api_key import ApiKeyRepository
from api.infrastructures.postgres.attachment import AttachmentRepository
from api.infrastructures.postgres.bot import BotRepository
from api.infrastructures.postgres.bot_template import BotTemplateRepository
from api.infrastructures.postgres.common_document_template import (
    CommonDocumentTemplateRepository,
)
from api.infrastructures.postgres.common_prompt_template import (
    CommonPromptTemplateRepository,
)
from api.infrastructures.postgres.conversation import ConversationRepository
from api.infrastructures.postgres.document import DocumentRepository
from api.infrastructures.postgres.document_folder import DocumentFolderRepository
from api.infrastructures.postgres.group import GroupRepository
from api.infrastructures.postgres.metering import MeteringRepository
from api.infrastructures.postgres.models.bot_template import BotTemplate
from api.infrastructures.postgres.models.chat_completion import ChatCompletion
from api.infrastructures.postgres.models.chat_completion_data_point import (
    ChatCompletionDataPoint,
)
from api.infrastructures.postgres.models.chat_completion_export import (
    ChatCompletionExport,
)
from api.infrastructures.postgres.models.common_document_template import (
    CommonDocumentTemplate,
)
from api.infrastructures.postgres.models.common_prompt_template import (
    CommonPromptTemplate,
)
from api.infrastructures.postgres.models.conversation import Conversation
from api.infrastructures.postgres.models.conversation_export import ConversationExport
from api.infrastructures.postgres.models.document_folder import DocumentFolder
from api.infrastructures.postgres.models.document_folder_path import DocumentFolderPath
from api.infrastructures.postgres.models.external_data_connection import (
    ExternalDataConnection,
)
from api.infrastructures.postgres.models.metering import Metering
from api.infrastructures.postgres.models.notification import Notification
from api.infrastructures.postgres.models.question_answer import QuestionAnswer
from api.infrastructures.postgres.models.tenant_alert import (
    TenantAlert as TenantAlertModel,
)
from api.infrastructures.postgres.models.term_v2 import TermV2
from api.infrastructures.postgres.models.user_document import UserDocument
from api.infrastructures.postgres.models.user_liked_bots import UserLikedBot
from api.infrastructures.postgres.models.workflow import Workflow
from api.infrastructures.postgres.notification import NotificationRepository
from api.infrastructures.postgres.prompt_template import PromptTemplateRepository
from api.infrastructures.postgres.question_answer import QuestionAnswerRepository
from api.infrastructures.postgres.tenant import TenantRepository
from api.infrastructures.postgres.user import UserRepository
from api.infrastructures.postgres.workflow import WorkflowRepository
from api.infrastructures.postgres.workflow_thread import WorkflowThreadRepository

SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/test_neosmartchat?client_encoding=utf8"

TenantSeed = Tenant
TenantAlertSeed = tenant_alert_domain.TenantAlert
BotsSeed = Tuple[list[bot_domain.Bot], list[dict], tenant_domain.Tenant, group_domain.Group]
ExternalDataConnectionsSeed = tuple[list[external_data_connection_domain.ExternalDataConnection], tenant_domain.Id]
GroupSeed = Tuple[group_domain.Group, group_domain.Name, tenant_domain.Id]
GroupsSeed = Tuple[list[group_domain.Group], tenant_domain.Id]
UserDocumentSeed = Tuple[document_feedback_domain.DocumentFeedback, user_domain.Id, document_domain.Id]
ConversationWithTurnsSeed = tuple[
    conversation_domain.Conversation,
    list[conversation_turn_domain.ConversationTurn],
]
ChatCompletionsSeed = tuple[
    bot_domain.Id,
    list[tuple[api_key_domain.ApiKey, chat_completion_domain.ChatCompletion]],
]
DocumentFolderSeed = Tuple[
    document_folder_domain.DocumentFolder,
    list[document_folder_domain.DocumentFolder],
    list[document_folder_domain.DocumentFolder],
    bot_domain.Id,
]
ExternalDocumentFolderSeed = Tuple[
    external_document_folder_domain.ExternalDocumentFolder,
    document_folder_domain.Id,
    bot_domain.Id,
]
ExternalDataConnectionSeed = tuple[external_data_connection_domain.ExternalDataConnection, tenant_domain.Id]
DocumentSeed = Tuple[document_domain.Document, document_domain.DocumentForCreate, bot_domain.Id]
DocumentsSeed = Tuple[list[document_domain.Document], bot_domain.Id]
UserSeed = Tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]
PdfParserPageMeteringSeed = tuple[
    list[Meter],
    list[Meter],
    datetime.datetime,
    bot_domain.Bot,
]
DocumentsWithAncestorFoldersSeed = Tuple[
    list[document_domain.DocumentWithAncestorFolders],
    bot_domain.Id,
]
WorkflowSeed = tuple[workflow_domain.Workflow, Tenant]
WorkflowListSeed = tuple[list[workflow_domain.Workflow], group_domain.Group, Tenant]
WorkflowThreadSeed = tuple[tenant_domain.Id, workflow_domain.Id, wf_thread_domain.WorkflowThread]
WorkflowThreadFlowStepSeed = tuple[
    tenant_domain.Id,
    workflow_domain.Id,
    wf_thread_domain.Id,
    wf_thread_flow_domain.Id,
    wf_thread_flow_step_domain.WorkflowThreadFlowStep,
]
WorkflowThreadFlowSeed = tuple[
    tenant_domain.Id, workflow_domain.Id, wf_thread_domain.Id, wf_thread_flow_domain.WorkflowThreadFlow
]


def random_string(n: int):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


@pytest.fixture(scope="session")
def test_app():
    # Alembicの設定をロード
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URI)

    # DBが存在する場合は削除
    db_url = SQLALCHEMY_DATABASE_URI
    if database_exists(db_url):
        drop_database(db_url)
    # DBを作成
    create_database(db_url)

    # マイグレーションを最新にする
    upgrade(alembic_cfg, "head")


@pytest.fixture
def get_db_session() -> Generator[Session, Any, None]:
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(params=[{"cleanup_resources": True}])
def tenant_seed(request: pytest.FixtureRequest, get_db_session: Session) -> Generator[TenantSeed, None, None]:
    """初期データのセットアップ"""

    # テナントの作成
    tenant_for_create = TenantForCreate(
        name=tenant_domain.Name(value="TestTenantSeed"),
        alias=tenant_domain.Alias(root=random_string(8)),
        allow_foreign_region=AllowForeignRegion(root=True),
        additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
        search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
        enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
    )

    session = get_db_session
    tenant_repo = TenantRepository(session)

    new_tenant = tenant_repo.create(tenant_for_create)

    yield new_tenant

    if not request.param["cleanup_resources"]:
        return

    tenant_repo.delete(new_tenant.id)


@pytest.fixture
def tenant_alert_seed(tenant_seed: TenantSeed, get_db_session: Session) -> Generator[TenantAlertSeed, None, None]:
    """初期データのセットアップ"""
    tenant = tenant_seed
    last_alerted_at = datetime.datetime(2024, 1, 1, 0, 0, 0)
    tenant_alert = TenantAlertModel(
        tenant_id=tenant.id.value,
        last_token_alerted_at=last_alerted_at,
        last_storage_alerted_at=last_alerted_at,
        last_ocr_alerted_at=None,
        last_token_alerted_threshold=80,
        last_storage_alerted_threshold=100,
        last_ocr_alerted_threshold=None,
    )

    session = get_db_session

    try:
        session.add(tenant_alert)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    yield tenant_alert.to_domain()

    # テスト後処理
    try:
        session.delete(tenant_alert)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


@pytest.fixture
def external_data_connections_seed(
    tenant_seed: TenantSeed, get_db_session: Session
) -> Generator[ExternalDataConnectionsSeed, None, None]:
    """初期データのセットアップ"""
    tenant = tenant_seed

    external_data_connections = [
        ExternalDataConnection(
            id=uuid4(),
            tenant_id=tenant.id.value,
            external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT.value,
            encrypted_credentials=external_data_connection_domain.DecryptedCredentials(
                type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
                raw={
                    "tenant_id": "test_tenant_id",
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                },
            )
            .encrypt()
            .root,
        ),
    ]

    session = get_db_session
    try:
        session.add_all(external_data_connections)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    yield (
        [external_data_connection.to_domain() for external_data_connection in external_data_connections],
        tenant.id,
    )

    # テスト後処理
    try:
        for external_data_connection in external_data_connections:
            session.delete(external_data_connection)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


@pytest.fixture(params=[{"cleanup_resources": True}])
def external_data_connection_seed(
    request, tenant_seed: TenantSeed, get_db_session: Session
) -> Generator[ExternalDataConnectionSeed, None, None]:
    """初期データのセットアップ"""
    tenant = tenant_seed
    external_data_connection = external_data_connection_domain.ExternalDataConnectionForCreate(
        tenant_id=tenant.id,
        external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        decrypted_credentials=external_data_connection_domain.DecryptedCredentials(
            type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
            raw={
                "tenant_id": "test_tenant_id",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        ),
    )

    tenant_repo = TenantRepository(get_db_session)

    new_external_data_connection = tenant_repo.create_external_data_connection(external_data_connection)

    yield new_external_data_connection, tenant.id

    if not request.param["cleanup_resources"]:
        return

    tenant_repo.hard_delete_external_data_connection(tenant.id, new_external_data_connection.id)


@pytest.fixture
def user_document_seed(
    user_seed: UserSeed, document_seed: DocumentSeed, get_db_session: Session
) -> Generator[UserDocumentSeed, None, None]:
    user_id, _, _, _, _ = user_seed
    document, _, _ = document_seed
    document_id = document.id

    document_feedback = UserDocument(
        user_id=user_id.value,
        document_id=document_id.value,
        evaluation=document_feedback_domain.Evaluation.GOOD,
    )

    session = get_db_session
    try:
        session.add(document_feedback)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    yield document_feedback.to_domain(), user_id, document_id

    # テスト後処理
    try:
        session.delete(document_feedback)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


@pytest.fixture(params=[{"cleanup_resources": True}])
def document_folder_seed(
    request: pytest.FixtureRequest, bots_seed: BotsSeed, get_db_session: Session
) -> Generator[DocumentFolderSeed, None, None]:
    """初期データのセットアップ"""

    # ボットの作成
    bots, _, _, _ = bots_seed
    bot_id = bots[0].id

    session = get_db_session
    root_document_folder = (
        session.execute(
            select(DocumentFolder)
            .where(
                DocumentFolder.bot_id == bot_id.value,
            )
            .join(
                DocumentFolderPath,
                DocumentFolderPath.descendant_document_folder_id == DocumentFolder.id,
            )
            .group_by(DocumentFolder.id)
            .having(func.count(DocumentFolderPath.id) == 1)
        )
        .scalars()
        .first()
    )
    if root_document_folder is None:
        raise ValueError("root_document_folder not found")

    domain_root_document_folder = root_document_folder.to_domain()

    # ドキュメントの作成
    child_document_folders_for_create = [
        # child document_folder 1
        document_folder_domain.DocumentFolderForCreate(
            name=document_folder_domain.Name(root="child_document_folder_seed_name1"),
        ),
        # child document_folder 2
        document_folder_domain.DocumentFolderForCreate(
            name=document_folder_domain.Name(root="child_document_folder_seed_name2"),
        ),
    ]

    child_child_document_folders_for_create = [
        # child_child document_folder 1
        document_folder_domain.DocumentFolderForCreate(
            name=document_folder_domain.Name(root="child_child_document_folder_seed_name1"),
        ),
    ]
    # データベースに直接挿入
    new_child_document_folders: list[DocumentFolder] = []
    new_child_child_document_folders: list[DocumentFolder] = []
    for child_document_folder in child_document_folders_for_create:
        new_child_document_folders.append(
            DocumentFolder(
                id=child_document_folder.id.root,
                bot_id=bot_id.value,
                name=child_document_folder.name.root,
            )
        )
    for child_child_document_folder in child_child_document_folders_for_create:
        new_child_child_document_folders.append(
            DocumentFolder(
                id=child_child_document_folder.id.root,
                bot_id=bot_id.value,
                name=child_child_document_folder.name.root,
            )
        )

    new_child_document_folder_paths: list[DocumentFolderPath] = [
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=child_document_folders_for_create[0].id.root,
            descendant_document_folder_id=child_document_folders_for_create[0].id.root,
            path_length=0,
        ),
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=domain_root_document_folder.id.root,
            descendant_document_folder_id=child_document_folders_for_create[0].id.root,
            path_length=1,
        ),
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=child_document_folders_for_create[1].id.root,
            descendant_document_folder_id=child_document_folders_for_create[1].id.root,
            path_length=0,
        ),
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=domain_root_document_folder.id.root,
            descendant_document_folder_id=child_document_folders_for_create[1].id.root,
            path_length=1,
        ),
    ]

    new_child_child_document_folder_paths: list[DocumentFolderPath] = [
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=child_child_document_folders_for_create[0].id.root,
            descendant_document_folder_id=child_child_document_folders_for_create[0].id.root,
            path_length=0,
        ),
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=child_document_folders_for_create[0].id.root,
            descendant_document_folder_id=child_child_document_folders_for_create[0].id.root,
            path_length=1,
        ),
        DocumentFolderPath(
            id=uuid4(),
            ancestor_document_folder_id=domain_root_document_folder.id.root,
            descendant_document_folder_id=child_child_document_folders_for_create[0].id.root,
            path_length=2,
        ),
    ]

    try:
        session.add_all(new_child_document_folders)
        session.add_all(new_child_child_document_folders)
        session.flush()
        session.add_all(new_child_document_folder_paths)
        session.add_all(new_child_child_document_folder_paths)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    child_document_folders = [document_folder.to_domain() for document_folder in new_child_document_folders]
    child_child_document_folders = [
        document_folder.to_domain() for document_folder in new_child_child_document_folders
    ]

    # 親フォルダ, [子フォルダ1, 子フォルダ2], bot_id
    yield (
        domain_root_document_folder,
        child_document_folders,
        child_child_document_folders,
        bot_id,
    )

    if not request.param["cleanup_resources"]:
        return

    # テスト後処理
    for dfp in new_child_document_folder_paths:
        document_folder_path_to_delete = (
            session.execute(select(DocumentFolderPath).where(DocumentFolderPath.id == dfp.id)).scalars().first()
        )
        if document_folder_path_to_delete:
            document_folder_path_to_delete.deleted_at = datetime.datetime.now()
    for df in new_child_document_folders:
        document_folder_to_delete = (
            session.execute(
                select(DocumentFolder).where(DocumentFolder.id == df.id, DocumentFolder.bot_id == bot_id.value)
            )
            .scalars()
            .first()
        )
        if document_folder_to_delete:
            document_folder_to_delete.deleted_at = datetime.datetime.now()
    for df in new_child_child_document_folders:
        document_folder_to_delete = (
            session.execute(
                select(DocumentFolder).where(DocumentFolder.id == df.id, DocumentFolder.bot_id == bot_id.value)
            )
            .scalars()
            .first()
        )
        if document_folder_to_delete:
            document_folder_to_delete.deleted_at = datetime.datetime.now()
    for dfcp in new_child_child_document_folder_paths:
        document_folder_path_to_delete = (
            session.execute(select(DocumentFolderPath).where(DocumentFolderPath.id == dfcp.id)).scalars().first()
        )
        if document_folder_path_to_delete:
            document_folder_path_to_delete.deleted_at = datetime.datetime.now()

    session.commit()


@pytest.fixture
def external_document_folder_seed(
    bots_seed: BotsSeed, get_db_session: Session
) -> Generator[ExternalDocumentFolderSeed, None, None]:
    """初期データのセットアップ"""
    bots, _, _, _ = bots_seed
    bot_id = bots[0].id

    document_folder_for_create = document_folder_domain.ExternalDocumentFolderForCreate(
        name=document_folder_domain.Name(root="external-document-folder"),
        external_id=external_data_connection_domain.ExternalId(root="drive_id:testtest,drive_item_id:testtest"),
        external_type=external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT,
        external_updated_at=external_data_connection_domain.ExternalUpdatedAt(root=datetime.datetime.now()),
        external_sync_metadata=external_data_connection_domain.ExternalSyncMetadata(
            root={"test": "test"},
        ),
        last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.datetime.now()),
    )

    new_document_folder = DocumentFolder(
        id=document_folder_for_create.id.root,
        bot_id=bot_id.value,
        name=document_folder_for_create.name.root,
        external_id=document_folder_for_create.external_id.root,
        external_type=document_folder_for_create.external_type.value,
        external_updated_at=document_folder_for_create.external_updated_at.root,
        external_sync_metadata=document_folder_for_create.external_sync_metadata.root,
        last_synced_at=document_folder_for_create.last_synced_at.root,
    )

    session = get_db_session
    document_folder_repo = DocumentFolderRepository(session)

    try:
        session.add(new_document_folder)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    yield new_document_folder.to_external_domain(), new_document_folder.to_domain().id, bot_id

    document_folder_repo.delete_by_bot_id(bot_id)


@pytest.fixture
def document_seed(
    document_folder_seed: DocumentFolderSeed,
    get_db_session: Session,
) -> Generator[DocumentSeed, None, None]:
    """初期データのセットアップ"""
    folder, _, _, bot_id = document_folder_seed

    # ドキュメントの作成
    document_for_create = document_domain.DocumentForCreate(
        name=document_domain.Name(value="テストドキュメント"),
        memo=document_domain.Memo(value="テストメモ"),
        file_extension=document_domain.FileExtension("pdf"),
        data=b"test_data",
        creator_id=user_domain.Id(value=1),
    )

    session = get_db_session
    document_repo = DocumentRepository(session)

    new_document = document_repo.create(bot_id, folder.id, document_for_create)

    yield new_document, document_for_create, bot_id

    document_repo.delete(new_document.id)


@pytest.fixture(params=[{"cleanup_resources": True}])
def documents_seed(
    request, document_folder_seed: DocumentFolderSeed, get_db_session: Session
) -> Generator[DocumentsSeed, None, None]:
    """初期データのセットアップ"""
    folder, _, _, bot_id = document_folder_seed

    # ドキュメントの作成
    documents_for_create = [
        document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント"),
            memo=document_domain.Memo(value="テストメモ"),
            file_extension=document_domain.FileExtension("pdf"),
            data=b"test_data",
            creator_id=user_domain.Id(value=1),
        ),
        document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント2"),
            memo=document_domain.Memo(value="テストメモ2"),
            file_extension=document_domain.FileExtension("pdf"),
            data=b"test_data2",
            creator_id=user_domain.Id(value=1),
        ),
    ]

    session = get_db_session
    document_repo = DocumentRepository(session)

    new_documents = [
        document_repo.create(bot_id, folder.id, document_for_create) for document_for_create in documents_for_create
    ]

    yield new_documents, bot_id

    if not request.param["cleanup_resources"]:
        return

    for document in new_documents:
        document_repo.delete(document.id)


@pytest.fixture
def documents_with_ancestor_folders_seed(
    document_folder_seed: DocumentFolderSeed,
    get_db_session: Session,
) -> Generator[DocumentsWithAncestorFoldersSeed, None, None]:
    """初期データのセットアップ"""
    root_folder, child_folders, child_child_folders, bot_id = document_folder_seed

    documents_for_create = [
        document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント"),
            memo=document_domain.Memo(value="テストメモ"),
            file_extension=document_domain.FileExtension("pdf"),
            data=b"test_data",
            creator_id=user_domain.Id(value=1),
        ),
        document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント2"),
            memo=document_domain.Memo(value="テストメモ2"),
            file_extension=document_domain.FileExtension("pdf"),
            data=b"test_data2",
            creator_id=user_domain.Id(value=1),
        ),
        document_domain.DocumentForCreate(
            name=document_domain.Name(value="テストドキュメント3"),
            memo=document_domain.Memo(value="テストメモ3"),
            file_extension=document_domain.FileExtension("pdf"),
            data=b"test_data3",
            creator_id=user_domain.Id(value=1),
        ),
    ]

    session = get_db_session
    document_repo = DocumentRepository(session)
    root_document = document_repo.create(bot_id, root_folder.id, documents_for_create[0])
    child_document = document_repo.create(bot_id, child_folders[0].id, documents_for_create[1])
    child_child_document = document_repo.create(bot_id, child_child_folders[0].id, documents_for_create[2])

    document_with_ancestor_folders = []
    document_with_ancestor_folders.append(
        document_domain.DocumentWithAncestorFolders(
            id=root_document.id,
            name=root_document.name,
            memo=root_document.memo,
            file_extension=root_document.file_extension,
            status=root_document.status,
            creator_id=root_document.creator_id,
            storage_usage=root_document.storage_usage,
            document_folder_id=root_document.document_folder_id,
            created_at=root_document.created_at,
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=root_folder.id,
                    name=root_folder.name,
                    created_at=root_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                ),
            ],
        )
    )
    document_with_ancestor_folders.append(
        document_domain.DocumentWithAncestorFolders(
            id=child_document.id,
            name=child_document.name,
            memo=child_document.memo,
            file_extension=child_document.file_extension,
            status=child_document.status,
            creator_id=child_document.creator_id,
            storage_usage=child_document.storage_usage,
            document_folder_id=child_document.document_folder_id,
            created_at=child_document.created_at,
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=root_folder.id,
                    name=root_folder.name,
                    created_at=root_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    id=child_folders[0].id,
                    name=child_folders[0].name,
                    created_at=child_folders[0].created_at,
                    order=document_folder_domain.Order(root=1),
                ),
            ],
        )
    )
    document_with_ancestor_folders.append(
        document_domain.DocumentWithAncestorFolders(
            id=child_child_document.id,
            name=child_child_document.name,
            memo=child_child_document.memo,
            file_extension=child_child_document.file_extension,
            status=child_child_document.status,
            creator_id=child_child_document.creator_id,
            storage_usage=child_child_document.storage_usage,
            document_folder_id=child_child_document.document_folder_id,
            created_at=child_child_document.created_at,
            ancestor_folders=[
                document_folder_domain.DocumentFolderWithOrder(
                    id=root_folder.id,
                    name=root_folder.name,
                    created_at=root_folder.created_at,
                    order=document_folder_domain.Order(root=0),
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    id=child_folders[0].id,
                    name=child_folders[0].name,
                    created_at=child_folders[0].created_at,
                    order=document_folder_domain.Order(root=1),
                ),
                document_folder_domain.DocumentFolderWithOrder(
                    id=child_child_folders[0].id,
                    name=child_child_folders[0].name,
                    created_at=child_child_folders[0].created_at,
                    order=document_folder_domain.Order(root=2),
                ),
            ],
        )
    )

    yield document_with_ancestor_folders, bot_id

    document_repo.delete(root_document.id)
    document_repo.delete(child_document.id)
    document_repo.delete(child_child_document.id)


@pytest.fixture(params=[{"cleanup_resources": True}])
def attachment_seed(
    request,
    bots_seed: BotsSeed,
    user_seed: UserSeed,
    get_db_session: Session,
) -> Generator[
    Tuple[
        attachment_domain.Attachment,
        attachment_domain.AttachmentForCreate,
        bot_domain.Id,
    ],
    None,
    None,
]:
    """初期データのセットアップ"""

    # ボットの作成
    bots, _, _, _ = bots_seed
    user_id, _, _, _, _ = user_seed
    bot_id = bots[0].id

    # アタッチメントの作成
    attachments_for_create = attachment_domain.AttachmentForCreate(
        name=attachment_domain.Name(root="テストドキュメント"),
        file_extension=attachment_domain.FileExtension("pdf"),
        id=attachment_domain.Id(root=uuid4()),
        data=b"test_data",
    )

    session = get_db_session
    attachment_repo = AttachmentRepository(session)
    new_attachment = attachment_repo.create(bot_id, user_id, attachments_for_create)

    yield new_attachment, attachments_for_create, bot_id

    if not request.param["cleanup_resources"]:
        return

    attachment_repo.delete(new_attachment.id)


@pytest.fixture
def basic_ai_seed(
    tenant_seed, general_group_seed, get_db_session: Session
) -> Generator[Tuple[list[Bot], Tenant, group_domain.Group], None, None]:
    """初期データのセットアップ"""
    new_tenant = tenant_seed

    basic_ai_for_create = bot_domain.BasicAiForCreate(
        tenant=new_tenant,
        model_family=ModelFamily.GPT_35_TURBO,
    )

    text2_image_bot_for_create = bot_domain.Text2ImageBotForCreate(
        tenant=new_tenant,
        model_family=Text2ImageModelFamily.DALL_E_3,
    )

    group, _, _ = general_group_seed

    session = get_db_session
    bot_repo = BotRepository(session)
    new_basic_ai = bot_repo.create(new_tenant.id, group.id, basic_ai_for_create)
    new_text2_image_bot = bot_repo.create(new_tenant.id, group.id, text2_image_bot_for_create)

    yield [new_basic_ai, new_text2_image_bot], new_tenant, group

    bot_repo.delete(new_basic_ai.id)
    bot_repo.delete(new_text2_image_bot.id)


@pytest.fixture(params=[{"cleanup_resources": True}])
def bots_seed(request, tenant_seed, group_seed, get_db_session: Session) -> Generator[BotsSeed, None, None]:
    """初期データのセットアップ"""
    new_tenant = tenant_seed
    new_group, _, _ = group_seed

    # ボットの作成
    bot_base_info = {
        "name": "確定申告Bot",
        "group_id": new_group.id.value,
        "description": "確定申告に関する質問に答えるBotです",
        "index_name": "sort-demo",
        "container_name": "content",
        "approach": "neollm",
        "example_question": "不動産投資に関する所得はどのように申告しますか？",
        "search_method": "bm25",
        "response_generator_model_family": ModelFamily.GPT_35_TURBO,
        "pdf_parser": "pypdf",
        "response_system_prompt": "",
        "enable_web_browsing": "false",
        "enable_follow_up_questions": "false",
        "icon_url": "https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png",
        "icon_color": "#AA68FF",
        "endpoint_id": "506b11e3-528d-4df6-91e7-8932d03e1b1f",
        "max_conversation_turns": "5",
    }

    bot_base_info_for_web_browsing = {
        "name": "テストchatgpt",
        "group_id": new_group.id.value,
        "description": "テストchatgpt",
        "index_name": "sort-demo",
        "container_name": "content",
        "approach": "chat_gpt_default",
        "example_question": "test",
        "search_method": "bm25",
        "response_generator_model_family": ModelFamily.GPT_4,
        "pdf_parser": "pypdf",
        "response_system_prompt": "",
        "enable_web_browsing": "true",
        "icon_url": "https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png",
        "icon_color": "#AA68FF",
        "endpoint_id": "506b11e3-528d-4df6-91e7-8932d03e1b1f",
        "max_conversation_turns": "5",
    }

    bot_base_info2 = dict(bot_base_info)
    bot_base_info2["name"] = "テスト2Bot"
    bot_base_info2["approach"] = "chat_gpt_default"

    bot_base_info3 = dict(bot_base_info)
    bot_base_info3["name"] = "テスト3Bot"
    bot_base_info3["response_system_prompt"] = "test"

    bot_base_info4 = dict(bot_base_info_for_web_browsing)
    bot_base_info4["name"] = "テスト4Bot"

    session = get_db_session
    bot_repo = BotRepository(session)
    document_folder_repo = DocumentFolderRepository(session)

    bot_infos = [bot_base_info, bot_base_info2, bot_base_info3, bot_base_info4]

    new_bots = []

    for bot_info in bot_infos:
        if bot_info["enable_web_browsing"] == "true":
            enable_web_browsing = True
        else:
            enable_web_browsing = False
        input = bot_domain.BotForCreate(
            name=bot_domain.Name(value=bot_info["name"]),
            description=bot_domain.Description(value=bot_info["description"]),
            index_name=IndexName(root=bot_info["index_name"]),
            container_name=ContainerName(root=bot_info["container_name"]),
            approach=bot_domain.Approach(bot_info["approach"]),
            example_questions=[bot_domain.ExampleQuestion(value=bot_info["example_question"])],
            search_method=bot_domain.SearchMethod(bot_info["search_method"]),
            response_generator_model_family=ModelFamily(bot_info["response_generator_model_family"]),
            pdf_parser=llm_domain.PdfParser(bot_info["pdf_parser"]),
            approach_variables=(
                [
                    av_domain.ApproachVariable(
                        name=av_domain.Name(value="response_system_prompt"),
                        value=av_domain.Value(value=bot_info["response_system_prompt"]),
                    )
                ]
                if bot_info["response_system_prompt"]
                else []
            ),
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=enable_web_browsing),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=bot_domain.IconUrl(root=bot_info["icon_url"]),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=(
                bot_domain.MaxConversationTurns(root=int(bot_info["max_conversation_turns"]))
                if bot_info["max_conversation_turns"]
                else None
            ),
        )
        new_bot = bot_repo.create(new_tenant.id, new_group.id, input)
        new_bots.append(new_bot)
        document_folder_repo.create_root_document_folder(
            new_bot.id,
            document_folder_domain.RootDocumentFolderForCreate(),
        )

    yield new_bots, bot_infos, new_tenant, new_group

    if not request.param["cleanup_resources"]:
        return

    for bot in new_bots:
        bot_repo.delete(bot.id)


@pytest.fixture
def api_key_seed(
    bots_seed: BotsSeed, get_db_session: Session
) -> Generator[tuple[api_key_domain.ApiKey, bot_domain.Bot], None, None]:
    bots, _, tenant, _ = bots_seed
    bot_id = bots[0].id
    api_key = api_key_domain.ApiKeyForCreate(
        bot_id=bot_id,
        name=api_key_domain.Name(root="test_api_key"),
        expires_at=api_key_domain.ExpiresAt(root=datetime.datetime(2060, 1, 1, 0, 0, 0)),
    )

    session = get_db_session
    api_key_repo = ApiKeyRepository(session)
    created = api_key_repo.create(api_key)
    yield created, bots[0]
    api_key_repo.delete_by_ids_and_tenant_id([created.id], tenant.id)


@pytest.fixture
def api_keys_seed(
    bots_seed: BotsSeed, get_db_session: Session
) -> Generator[tuple[list[api_key_domain.ApiKey], bot_domain.Id], None, None]:
    bots, _, tenant, _ = bots_seed
    bot_id = bots[0].id
    api_keys = [
        api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_api_key"),
            expires_at=api_key_domain.ExpiresAt(root=datetime.datetime(2060, 1, 1, 0, 0, 0)),
        )
        for _ in range(3)
    ]

    session = get_db_session
    api_key_repo = ApiKeyRepository(session)

    created_api_keys: list[api_key_domain.ApiKey] = []
    for api_key in api_keys:
        created_api_keys.append(api_key_repo.create(api_key))
    yield created_api_keys, bot_id

    for created_api_key in created_api_keys:
        api_key_repo.delete_by_ids_and_tenant_id([created_api_key.id], tenant.id)


@pytest.fixture(params=[{"cleanup_resources": True}])
def user_seed(
    request, tenant_seed, get_db_session: Session
) -> Generator[
    Tuple[
        user_domain.Id,
        user_domain.UserForCreate,
        tenant_domain.Id,
        user_domain.ExternalUserId,
        user_domain.Id,
    ],
    None,
    None,
]:
    """初期データのセットアップ"""

    new_tenant = tenant_seed
    tenant_id = new_tenant.id

    # ユーザーの作成
    user_info = {
        "name": "テストユーザー",
        "email": "testuserseed@example.com",
        "auth0_id": "email|testuserseed",
    }
    user_info2 = {
        "name": "テストユーザー2",
        "email": "testuserseed2@example.com",
        "auth0_id": "email|testuserseed2",
    }

    user_for_create = user_domain.UserForCreate(
        name=user_domain.Name(value=user_info["name"]),
        email=user_domain.Email(value=user_info["email"]),
        roles=[user_domain.Role("admin"), user_domain.Role("user")],
    )
    user_for_create2 = user_domain.UserForCreate(
        name=user_domain.Name(value=user_info2["name"]),
        email=user_domain.Email(value=user_info2["email"]),
        roles=[user_domain.Role("admin"), user_domain.Role("user")],
    )

    session = get_db_session
    user_repo = UserRepository(session)

    #  user_repo.create は userオブジェクトではなく user_idを返す
    new_user_id = user_repo.create(tenant_id, user_for_create, user_info["auth0_id"])
    new_user_id2 = user_repo.create(tenant_id, user_for_create2, user_info2["auth0_id"])

    yield (
        new_user_id,
        user_for_create,
        tenant_id,
        user_domain.ExternalUserId.from_string(user_info["auth0_id"]),
        new_user_id2,
    )

    if not request.param["cleanup_resources"]:
        return

    user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)
    user_repo.delete_by_id_and_tenant_id(new_user_id2, tenant_id)


@pytest.fixture
def general_group_seed(
    tenant_seed, get_db_session: Session
) -> Generator[Tuple[group_domain.Group, group_domain.Name, tenant_domain.Id], None, None]:
    """初期データのセットアップ"""

    # テナントの作成
    new_tenant = tenant_seed
    tenant_id = new_tenant.id

    # グループの作成
    group_info = {
        "name": "テストグループ",
    }

    group_name = group_domain.Name(value=group_info["name"])

    session = get_db_session
    group_repo = GroupRepository(session)

    new_group = group_repo.create_group(tenant_id, group_name, is_general=group_domain.IsGeneral(root=True))
    yield new_group, group_name, tenant_id

    group_repo.delete_group(tenant_id, new_group.id)


@pytest.fixture(params=[{"cleanup_resources": True}])
def group_seed(request, tenant_seed, get_db_session: Session) -> Generator[GroupSeed, None, None]:
    """初期データのセットアップ"""

    # テナントの作成
    new_tenant = tenant_seed
    tenant_id = new_tenant.id

    # グループの作成
    group_info = {
        "name": "テストグループ",
    }

    group_name = group_domain.Name(value=group_info["name"])

    session = get_db_session
    group_repo = GroupRepository(session)

    new_group = group_repo.create_group(tenant_id, group_name, is_general=group_domain.IsGeneral(root=False))
    yield new_group, group_name, tenant_id

    if not request.param["cleanup_resources"]:
        return

    group_repo.delete_group(tenant_id, new_group.id)


@pytest.fixture
def groups_seed(tenant_seed: tenant_domain.Tenant, get_db_session: Session) -> Generator[GroupsSeed, None, None]:
    tenant = tenant_seed
    session = get_db_session
    group_repo = GroupRepository(session)
    new_groups = []
    for i in range(3):
        new_groups.append(
            group_repo.create_group(
                tenant.id, group_domain.Name(value=f"test_group_{i}"), is_general=group_domain.IsGeneral(root=False)
            )
        )
    yield new_groups, tenant.id


@pytest.fixture(params=[{"cleanup_resources": True}])
def term_v2_seed(
    bots_seed: BotsSeed, get_db_session: Session
) -> Generator[Tuple[list[term_domain.TermV2], bot_domain.Id], None, None]:
    """初期データのセットアップ"""
    session = get_db_session

    # ボットの作成
    bots, _, _, _ = bots_seed
    bot_id = bots[0].id

    # ドキュメントの作成
    terms_for_create = [
        term_domain.TermForCreateV2(
            names=[
                term_domain.NameV2(root="test"),
                term_domain.NameV2(root="test_array"),
            ],
            description=term_domain.DescriptionV2(root="テスト用語の説明"),
        ),
        term_domain.TermForCreateV2(
            names=[term_domain.NameV2(root="test2")],
            description=term_domain.DescriptionV2(root="テスト2用語の説明"),
        ),
        term_domain.TermForCreateV2(
            names=[
                term_domain.NameV2(root="test3"),
                term_domain.NameV2(root="test3_array"),
            ],
            description=term_domain.DescriptionV2(root="テスト3用語の説明"),
        ),
    ]
    # データベースに直接挿入
    new_terms: list[TermV2] = []
    for term in terms_for_create:
        new_terms.append(
            TermV2(
                bot_id=bot_id.value,
                names=[name.root for name in term.names],
                description=term.description.root,
            )
        )
    session.add_all(new_terms)
    session.commit()
    terms = [term.to_domain() for term in new_terms]

    yield terms, bot_id

    # テスト後処理
    for tm in terms:
        term_to_delete = (
            session.execute(select(TermV2).where(TermV2.id == tm.id.root, TermV2.bot_id == bot_id.value))
            .scalars()
            .first()
        )
        if term_to_delete:
            session.delete(term_to_delete)
    session.commit()


@pytest.fixture(params=[{"cleanup_resources": True}])
def prompt_templates_seed(
    request,
    tenant_seed: tenant_domain.Tenant,
    get_db_session: Session,
) -> Generator[Tuple[tenant_domain.Id, list[prompt_template_domain.PromptTemplate]], None, None]:
    tenant = tenant_seed
    prompt_templates_for_create = [
        prompt_template_domain.PromptTemplateForCreate(
            title=prompt_template_domain.Title(value="title1"),
            description=prompt_template_domain.Description(value="description1"),
            prompt=prompt_template_domain.Prompt(value="prompt1"),
        ),
        prompt_template_domain.PromptTemplateForCreate(
            title=prompt_template_domain.Title(value="title2"),
            description=prompt_template_domain.Description(value="description2"),
            prompt=prompt_template_domain.Prompt(value="prompt2"),
        ),
    ]

    session = get_db_session
    prompt_template_repo = PromptTemplateRepository(session)
    pts = prompt_template_repo.bulk_create(
        tenant_id=tenant.id,
        prompt_templates=prompt_templates_for_create,
    )
    yield tenant.id, pts

    if not request.param["cleanup_resources"]:
        return

    prompt_template_repo.delete_by_ids_and_tenant_id(
        tenant_id=tenant.id,
        ids=[pt.id for pt in pts],
    )


def _delete_conversation_exports_for_test(
    session: Session, conversation_export_ids: list[conversation_export_domain.Id]
) -> None:
    conversation_exports = (
        session.execute(
            select(ConversationExport)
            .where(
                ConversationExport.id.in_(
                    [conversation_export_id.root for conversation_export_id in conversation_export_ids]
                )
            )
            .execution_options(include_deleted=True)
        )
        .scalars()
        .all()
    )
    for ce in conversation_exports:
        session.delete(ce)
    session.commit()


@pytest.fixture
def conversation_exports_seed(
    user_seed: UserSeed,
    bots_seed: BotsSeed,
    get_db_session: Session,
) -> Generator[list[conversation_export_domain.ConversationExport], None, None]:
    session = get_db_session
    user_id, _, _, _, _ = user_seed
    bots, _, _, _ = bots_seed
    target_bot_id = bots[0].id

    # 会話エクスポートの作成
    id1 = conversation_export_domain.Id(root=uuid4())
    id2 = conversation_export_domain.Id(root=uuid4())
    id3 = conversation_export_domain.Id(root=uuid4())
    id4 = conversation_export_domain.Id(root=uuid4())
    id5 = conversation_export_domain.Id(root=uuid4())

    new_conversation_exports = [
        ConversationExport(
            id=id1.root,
            status=conversation_export_domain.Status.ACTIVE.value,
            user_id=user_id.value,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.datetime(2024, 1, 1, 0, 0, 0)).root,
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.datetime(2024, 3, 31, 0, 0, 0)).root,
            target_bot_id=target_bot_id.value,
            target_user_id=user_id.value,
            deleted_at=None,
        ),
        ConversationExport(
            id=id2.root,
            status=conversation_export_domain.Status.ACTIVE.value,
            user_id=user_id.value,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.datetime(2024, 1, 1, 0, 0, 0)).root,
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.datetime(2024, 3, 31, 0, 0, 0)).root,
            target_bot_id=target_bot_id.value,
            target_user_id=None,
            deleted_at=None,
        ),
        ConversationExport(
            id=id3.root,
            status=conversation_export_domain.Status.ACTIVE.value,
            user_id=user_id.value,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.datetime(2024, 9, 1, 0, 0, 0)).root,
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.datetime(2024, 9, 16, 0, 0, 0)).root,
            target_bot_id=None,
            target_user_id=user_id.value,
            deleted_at=None,
        ),
        ConversationExport(
            id=id4.root,
            status=conversation_export_domain.Status.PROCESSING.value,
            user_id=user_id.value,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.datetime(2024, 9, 1, 0, 0, 0)).root,
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.datetime(2024, 9, 16, 0, 0, 0)).root,
            target_bot_id=None,
            target_user_id=None,
            deleted_at=None,
        ),
        ConversationExport(
            id=id5.root,
            status=conversation_export_domain.Status.DELETED.value,
            user_id=user_id.value,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime.datetime(2024, 9, 1, 0, 0, 0)).root,
            end_date_time=conversation_export_domain.EndDateTime(root=datetime.datetime(2024, 9, 16, 0, 0, 0)).root,
            target_bot_id=target_bot_id.value,
            target_user_id=user_id.value,
            deleted_at=datetime.datetime(2024, 9, 16, 0, 0, 0),
        ),
    ]

    try:
        session.add_all(new_conversation_exports)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    conversation_exports = [
        new_conversation_export.to_domain() for new_conversation_export in new_conversation_exports
    ]

    yield conversation_exports

    _delete_conversation_exports_for_test(
        session,
        [conversation_export.id for conversation_export in conversation_exports],
    )


def _delete_chat_completion_exports_for_test(
    session: Session,
    chat_completion_export_ids: list[chat_completion_export_domain.Id],
) -> None:
    chat_completion_export = session.execute(
        select(ChatCompletionExport).where(
            ChatCompletionExport.id.in_(
                [chat_completion_export_id.root for chat_completion_export_id in chat_completion_export_ids]
            )
        )
    ).scalar()
    if chat_completion_export:
        session.delete(chat_completion_export)
        session.commit()


@pytest.fixture
def chat_completion_exports_seed(
    user_seed: UserSeed,
    bots_seed: BotsSeed,
    api_key_seed: Tuple[api_key_domain.ApiKey, bot_domain.Id],
    get_db_session: Session,
) -> Generator[list[chat_completion_export_domain.ChatCompletionExport], None, None]:
    user_id, _, _, _, _ = user_seed
    bots, _, _, _ = bots_seed
    target_bot_id = bots[0].id
    api_key, _ = api_key_seed

    id1 = chat_completion_export_domain.Id(root=uuid4())
    id2 = chat_completion_export_domain.Id(root=uuid4())

    new_chat_completion_exports = [
        ChatCompletionExport(
            id=id1.root,
            status=chat_completion_export_domain.Status.PROCESSING.value,
            creator_id=user_id.value,
            start_date_time=chat_completion_export_domain.StartDateTime(
                root=datetime.datetime(2024, 1, 1, 0, 0, 0)
            ).root,
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.datetime(2024, 3, 31, 0, 0, 0)).root,
            target_bot_id=target_bot_id.value,
            target_api_key_id=api_key.id.root,
        ),
        ChatCompletionExport(
            id=id2.root,
            status=chat_completion_export_domain.Status.PROCESSING.value,
            creator_id=user_id.value,
            start_date_time=chat_completion_export_domain.StartDateTime(
                root=datetime.datetime(2024, 1, 1, 0, 0, 0)
            ).root,
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.datetime(2024, 3, 31, 0, 0, 0)).root,
        ),
    ]

    session = get_db_session
    try:
        session.add_all(new_chat_completion_exports)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    chat_completion_exports = [
        new_chat_completion_export.to_domain() for new_chat_completion_export in new_chat_completion_exports
    ]

    yield chat_completion_exports

    _delete_chat_completion_exports_for_test(
        session,
        [chat_completion_export.id for chat_completion_export in chat_completion_exports],
    )


def _delete_conversation_for_test(session: Session, conversation_id: ConversationId) -> None:
    conversation = session.execute(select(Conversation).where(Conversation.id == conversation_id.root)).scalar()
    if conversation:
        session.delete(conversation)
        session.commit()


@pytest.fixture
def conversations_seed(
    user_seed: UserSeed,
    bots_seed: BotsSeed,
    get_db_session: Session,
) -> Generator[Tuple[conversation_domain.Conversation, tenant_domain.Id], None, None]:
    session = get_db_session
    conversation_repo = ConversationRepository(session)

    user_id, _, _, _, _ = user_seed
    bots, _, tenant, _ = bots_seed
    bot_id = bots[0].id
    tenant_id = tenant.id
    # 会話の作成
    conversation_for_create = conversation_domain.ConversationForCreate(
        user_id=user_id,
        bot_id=bot_id,
    )
    new_conversation = conversation_repo.save_conversation(conversation_for_create)

    yield (
        new_conversation,
        tenant_id,
    )


@pytest.fixture(params=[{"cleanup_resources": True}])
def conversation_with_turns_seed(
    request,
    conversations_seed: Tuple[conversation_domain.Conversation, tenant_domain.Id],
    get_db_session: Session,
) -> Generator[ConversationWithTurnsSeed, None, None]:
    session = get_db_session
    conversation_repo = ConversationRepository(session)

    conversation, _ = conversations_seed
    conversation_id = conversation.id
    user_input = conversation_turn_domain.UserInput(root="user_input")
    bot_output = conversation_turn_domain.BotOutput(root="bot_output")
    queries = [conversation_turn_domain.Query(root="query")]
    token_set = token_domain.TokenSet(
        query_input_token=token_domain.Token(root=1),
        query_output_token=token_domain.Token(root=2),
        response_input_token=token_domain.Token(root=3),
        response_output_token=token_domain.Token(root=4),
    )
    query_generator_model = ModelName(ModelName.GPT_35_TURBO)
    response_generator_model = ModelName(ModelName.GPT_35_TURBO)
    evaluation = None
    comment = None

    conversation_turn_for_create = conversation_turn_domain.ConversationTurnForCreate(
        conversation_id=conversation_id,
        user_input=user_input,
        bot_output=bot_output,
        queries=queries,
        token_set=token_set,
        token_count=token_domain.TokenCount(root=1.0),
        query_generator_model=query_generator_model,
        response_generator_model=response_generator_model,
        evaluation=evaluation,
        comment=comment,
    )
    content = data_point.Content(root="content")
    cite_number = data_point.CiteNumber(root=1)
    page_number = data_point.PageNumber(root=1)
    chunk_name = data_point.ChunkName(root="chunk_name")
    blob_path = data_point.BlobPath(root="blob_path")
    type = data_point.Type.INTERNAL
    url = data_point.Url(root="")
    additional_info = data_point.AdditionalInfo(root={"key": "value"})
    conversation_data_point_for_create = conversation_data_point_domain.ConversationDataPointForCreate(
        turn_id=conversation_turn_for_create.id,
        content=content,
        cite_number=cite_number,
        page_number=page_number,
        chunk_name=chunk_name,
        blob_path=blob_path,
        type=type,
        url=url,
        additional_info=additional_info,
    )

    conversation_repo.save_conversation_turn(conversation_turn_for_create, [conversation_data_point_for_create])

    new_conversation = conversation_domain.Conversation(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        bot_id=conversation.bot_id,
    )
    conversation_turns = [
        conversation_turn_domain.ConversationTurn(
            id=conversation_turn_for_create.id,
            conversation_id=conversation_turn_for_create.conversation_id,
            user_input=conversation_turn_for_create.user_input,
            bot_output=conversation_turn_for_create.bot_output,
            queries=conversation_turn_for_create.queries,
            token_set=conversation_turn_for_create.token_set,
            token_count=conversation_turn_for_create.token_count,
            query_generator_model=conversation_turn_for_create.query_generator_model,
            response_generator_model=conversation_turn_for_create.response_generator_model,
            evaluation=conversation_turn_for_create.evaluation,
            # datetime型の値を入れる
            created_at=conversation_turn_domain.CreatedAt(root=datetime.datetime.strptime("20240101", "%Y%m%d")),
            data_points=[
                conversation_data_point_domain.ConversationDataPoint(
                    id=conversation_data_point_for_create.id,
                    turn_id=conversation_data_point_for_create.turn_id,
                    document_id=None,
                    content=conversation_data_point_for_create.content,
                    cite_number=conversation_data_point_for_create.cite_number,
                    page_number=conversation_data_point_for_create.page_number,
                    chunk_name=conversation_data_point_for_create.chunk_name,
                    blob_path=conversation_data_point_for_create.blob_path,
                    type=conversation_data_point_for_create.type,
                    url=conversation_data_point_for_create.url,
                    additional_info=conversation_data_point_for_create.additional_info,
                )
            ],
        )
    ]
    yield new_conversation, conversation_turns

    if not request.param["cleanup_resources"]:
        return

    _delete_conversation_for_test(session, new_conversation.id)


@pytest.fixture
def conversation_with_turns_attachment_seed(
    conversations_seed: Tuple[conversation_domain.Conversation, tenant_domain.Id],
    attachment_seed: Tuple[
        attachment_domain.Attachment,
        attachment_domain.AttachmentForCreate,
        bot_domain.Id,
    ],
    get_db_session: Session,
) -> Generator[conversation_domain.ConversationWithAttachments, None, None]:
    session = get_db_session
    conversation_repo = ConversationRepository(session)
    attachment_repo = AttachmentRepository(session)

    conversation, _ = conversations_seed
    attachment, _, _ = attachment_seed
    conversation_id = conversation.id
    user_input = conversation_turn_domain.UserInput(root="user_input")
    bot_output = conversation_turn_domain.BotOutput(root="bot_output")
    queries = [conversation_turn_domain.Query(root="query")]
    token_set = token_domain.TokenSet(
        query_input_token=token_domain.Token(root=1),
        query_output_token=token_domain.Token(root=2),
        response_input_token=token_domain.Token(root=3),
        response_output_token=token_domain.Token(root=4),
    )
    query_generator_model = ModelName(ModelName.GPT_35_TURBO)
    response_generator_model = ModelName(ModelName.GPT_35_TURBO)
    evaluation = None
    comment = None
    document_folder = None

    conversation_turn_for_create = conversation_turn_domain.ConversationTurnForCreate(
        conversation_id=conversation_id,
        user_input=user_input,
        bot_output=bot_output,
        queries=queries,
        token_set=token_set,
        token_count=token_domain.TokenCount(root=1.0),
        query_generator_model=query_generator_model,
        response_generator_model=response_generator_model,
        evaluation=evaluation,
        comment=comment,
        document_folder=document_folder,
    )
    content = data_point.Content(root="content")
    cite_number = data_point.CiteNumber(root=1)
    page_number = data_point.PageNumber(root=1)
    chunk_name = data_point.ChunkName(root="chunk_name")
    blob_path = data_point.BlobPath(root="blob_path")
    type = data_point.Type.INTERNAL
    url = data_point.Url(root="")
    additional_info = data_point.AdditionalInfo(root={"key": "value"})
    conversation_data_point_for_create = conversation_data_point_domain.ConversationDataPointForCreate(
        turn_id=conversation_turn_for_create.id,
        content=content,
        cite_number=cite_number,
        page_number=page_number,
        chunk_name=chunk_name,
        blob_path=blob_path,
        type=type,
        url=url,
        additional_info=additional_info,
    )

    conversation_repo.save_conversation_turn(conversation_turn_for_create, [conversation_data_point_for_create])
    # attachmentのconversation_turn_idを更新
    attachment_repo.update_conversation_turn_ids([attachment.id], conversation_turn_for_create.id)

    new_conversation = conversation_domain.ConversationWithAttachments(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        bot_id=conversation.bot_id,
        conversation_turns=[
            conversation_turn_domain.ConversationTurnWithAttachments(
                id=conversation_turn_for_create.id,
                conversation_id=conversation_turn_for_create.conversation_id,
                user_input=conversation_turn_for_create.user_input,
                bot_output=conversation_turn_for_create.bot_output,
                queries=conversation_turn_for_create.queries,
                token_set=conversation_turn_for_create.token_set,
                token_count=conversation_turn_for_create.token_count,
                query_generator_model=conversation_turn_for_create.query_generator_model,
                response_generator_model=conversation_turn_for_create.response_generator_model,
                evaluation=conversation_turn_for_create.evaluation,
                comment=conversation_turn_for_create.comment,
                # datetime型の値を入れる
                created_at=conversation_turn_domain.CreatedAt(root=datetime.datetime.strptime("20240101", "%Y%m%d")),
                data_points=[
                    conversation_data_point_domain.ConversationDataPoint(
                        id=conversation_data_point_for_create.id,
                        turn_id=conversation_data_point_for_create.turn_id,
                        document_id=None,
                        content=conversation_data_point_for_create.content,
                        cite_number=conversation_data_point_for_create.cite_number,
                        page_number=conversation_data_point_for_create.page_number,
                        chunk_name=conversation_data_point_for_create.chunk_name,
                        blob_path=conversation_data_point_for_create.blob_path,
                        type=conversation_data_point_for_create.type,
                        url=conversation_data_point_for_create.url,
                        additional_info=conversation_data_point_for_create.additional_info,
                    )
                ],
                attachments=[attachment],
                document_folder=conversation_turn_for_create.document_folder,
            )
        ],
    )
    yield new_conversation
    _delete_conversation_for_test(session, new_conversation.id)


@pytest.fixture
def pdf_parser_page_metering_seed(
    tenant_seed: Tenant, bots_seed: BotsSeed, get_db_session: Session, workflow_seed: WorkflowSeed
) -> Generator[PdfParserPageMeteringSeed, None, None]:
    """初期データのセットアップ"""
    session = get_db_session
    metering_repo = MeteringRepository(session)

    tenant = tenant_seed
    bots, _, _, _ = bots_seed
    workflow, _ = workflow_seed
    bot = bots[0]

    tenant_id = tenant.id
    bot_id = bot.id

    bot_meterings = [
        PdfParserMeterForCreate(
            tenant_id=tenant_id,
            bot_id=bot_id,
            type=PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
            quantity=Quantity(root=5),
        ),
        PdfParserMeterForCreate(
            tenant_id=tenant_id,
            bot_id=bot_id,
            type=PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
            quantity=Quantity(root=10),
        ),
    ]

    workflow_meterings = [
        PdfParserMeterForCreate(
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            type=PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
            quantity=Quantity(root=10),
        ),
        PdfParserMeterForCreate(
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            type=PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
            quantity=Quantity(root=20),
        ),
    ]

    for bot_metering in bot_meterings:
        metering_repo.create_pdf_parser_count(bot_metering)
    for workflow_metering in workflow_meterings:
        metering_repo.create_pdf_parser_count(workflow_metering)

    created_at = datetime.datetime.now()

    saved_bot_meterings = [
        Meter(
            tenant_id=tenant_id,
            bot_id=bot_id,
            type=PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
            quantity=Quantity(root=5),
        ),
        Meter(
            tenant_id=tenant_id,
            bot_id=bot_id,
            type=PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
            quantity=Quantity(root=10),
        ),
    ]

    saved_workflow_meterings = [
        Meter(
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            type=PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
            quantity=Quantity(root=10),
        ),
        Meter(
            tenant_id=tenant_id,
            workflow_id=workflow.id,
            type=PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT,
            quantity=Quantity(root=20),
        ),
    ]

    yield saved_bot_meterings, saved_workflow_meterings, created_at, bot

    # テスト後処理: 最新の2件を削除
    latest_two_metering = session.query(Metering).order_by(desc(Metering.created_at)).limit(4).all()

    for metering_to_delete in latest_two_metering:
        session.delete(metering_to_delete)
    session.commit()


@pytest.fixture(params=[{"cleanup_resources": True}])
def bot_prompt_template_seed(
    request,
    bots_seed: BotsSeed,
    get_db_session: Session,
) -> Generator[Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]], None, None]:
    session = get_db_session
    bot_repo = BotRepository(session)

    bots, _, _, _ = bots_seed
    bot_id = bots[0].id

    bot_prompt_templates_for_create = [
        bot_prompt_template_domain.PromptTemplateForCreate(
            title=bot_prompt_template_domain.Title(root="title1"),
            description=bot_prompt_template_domain.Description(root="description1"),
            prompt=bot_prompt_template_domain.Prompt(root="bot_prompt1"),
        ),
        bot_prompt_template_domain.PromptTemplateForCreate(
            title=bot_prompt_template_domain.Title(root="title2"),
            description=bot_prompt_template_domain.Description(root="description2"),
            prompt=bot_prompt_template_domain.Prompt(root="bot_prompt2"),
        ),
    ]
    pts = [bot_repo.create_prompt_template(bot_id, pt) for pt in bot_prompt_templates_for_create]
    yield bot_id, pts

    if not request.param["cleanup_resources"]:
        return

    bot_repo.delete_prompt_templates(bot_id=bot_id, bot_prompt_template_ids=[pt.id for pt in pts])


@pytest.fixture(params=[{"cleanup_resources": True}])
def question_answer_seed(
    request,
    bots_seed: BotsSeed,
    get_db_session: Session,
) -> Generator[Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]], None, None]:
    session = get_db_session
    question_answer_repo = QuestionAnswerRepository(session)

    bots, _, _, _ = bots_seed
    bot_id = bots[0].id
    question_answers_for_create = [
        question_answer_domain.QuestionAnswerForCreate(
            question=question_answer_domain.Question(root="question1"),
            answer=question_answer_domain.Answer(root="answer1"),
            status=question_answer_domain.Status(question_answer_domain.Status.INDEXED),
        ),
        question_answer_domain.QuestionAnswerForCreate(
            question=question_answer_domain.Question(root="question2"),
            answer=question_answer_domain.Answer(root="answer2"),
            status=question_answer_domain.Status(question_answer_domain.Status.INDEXED),
        ),
    ]
    qas = [question_answer_repo.create(bot_id, qa) for qa in question_answers_for_create]

    yield bot_id, qas

    if not request.param["cleanup_resources"]:
        return

    # テスト後処理
    for qa in qas:
        question_answer = (
            session.execute(
                select(QuestionAnswer).where(
                    QuestionAnswer.id == qa.id.root,
                    QuestionAnswer.bot_id == bot_id.value,
                )
            )
            .scalars()
            .first()
        )
        session.delete(question_answer)
    session.commit()


@pytest.fixture
def notifications_seed(
    get_db_session: Session,
) -> Generator[list[notification_domain.Notification], None, None]:
    session = get_db_session
    notification_repo = NotificationRepository(session)

    now = datetime.datetime.now()
    today = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    notifications_for_create = [
        notification_domain.NotificationForCreate(
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=today),
            end_date=notification_domain.EndDate(root=datetime.datetime.now() + datetime.timedelta(days=2)),
        ),
        notification_domain.NotificationForCreate(
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.ADMIN),
            start_date=notification_domain.StartDate(root=today),
            end_date=notification_domain.EndDate(root=datetime.datetime.now() + datetime.timedelta(days=2)),
        ),
    ]

    for notification_for_create in notifications_for_create:
        notification_repo.create(notification_for_create)
    created_notifications = (
        session.execute(
            select(Notification).where(
                Notification.id.in_([notification.id.root for notification in notifications_for_create])
            )
        )
        .scalars()
        .all()
    )

    notifications = [created_notification.to_domain() for created_notification in created_notifications]
    yield notifications

    # テスト後処理
    for notification in notifications:
        nf_to_delete = (
            session.execute(select(Notification).where(Notification.id == notification.id.root)).scalars().first()
        )
        session.delete(nf_to_delete)
    session.commit()


@pytest.fixture
def bot_templates_seed(
    get_db_session: Session,
) -> Generator[list[bot_template_domain.BotTemplate], None, None]:
    session = get_db_session
    bot_template_repo = BotTemplateRepository(session)

    bot_templates_for_create = [
        bot_template_domain.BotTemplateForCreate(
            name=bot_template_domain.Name(root="test-name"),
            description=bot_template_domain.Description(root="test-description"),
            approach=bot_template_domain.Approach(bot_template_domain.Approach.NEOLLM),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=llm_domain.PdfParser(llm_domain.PdfParser.PYPDF),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=True),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=bot_template_domain.DocumentLimit(root=5),
            is_public=bot_template_domain.IsPublic(root=True),
            icon_color=bot_template_domain.IconColor(root="#000000"),
        ),
        bot_template_domain.BotTemplateForCreate(
            name=bot_template_domain.Name(root="test-name"),
            description=bot_template_domain.Description(root="test-description"),
            approach=bot_template_domain.Approach(bot_template_domain.Approach.NEOLLM),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=llm_domain.PdfParser(llm_domain.PdfParser.PYPDF),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=False),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=bot_template_domain.DocumentLimit(root=5),
            is_public=bot_template_domain.IsPublic(root=False),
            icon_color=bot_template_domain.IconColor(root="#000000"),
        ),
    ]
    created_bot_templates = [
        bot_template_repo.create(bot_template_for_create) for bot_template_for_create in bot_templates_for_create
    ]
    yield created_bot_templates

    # テスト後処理
    for bot_template in created_bot_templates:
        bot_template_to_delete = (
            session.execute(select(BotTemplate).where(BotTemplate.id == bot_template.id.root)).scalars().first()
        )
        if bot_template_to_delete is not None:
            bot_template_to_delete.deleted_at = datetime.datetime.now()
    session.commit()


@pytest.fixture
def common_prompt_templates_seed(
    bot_templates_seed: list[bot_template_domain.BotTemplate],
    get_db_session: Session,
) -> Generator[Tuple[bot_template_domain.Id, list[cpt_domain.CommonPromptTemplate]], None, None]:
    session = get_db_session
    common_prompt_template_repo = CommonPromptTemplateRepository(session)

    bot_templates = bot_templates_seed
    bot_template_id = bot_templates[0].id
    common_prompt_templates_for_create = [
        cpt_domain.CommonPromptTemplateForCreate(
            title=cpt_domain.Title(root="title1"),
            prompt=cpt_domain.Prompt(root="common_prompt1"),
        ),
        cpt_domain.CommonPromptTemplateForCreate(
            title=cpt_domain.Title(root="title2"),
            prompt=cpt_domain.Prompt(root="common_prompt2"),
        ),
    ]
    cpts = [common_prompt_template_repo.create(bot_templates[0].id, cpt) for cpt in common_prompt_templates_for_create]
    yield bot_template_id, cpts

    # テスト後処理
    for cpt in cpts:
        cpt_to_delete = (
            session.execute(select(CommonPromptTemplate).where(CommonPromptTemplate.id == cpt.id.root))
            .scalars()
            .first()
        )
        session.delete(cpt_to_delete)
    session.commit()


@pytest.fixture
def common_document_template_seed(
    bot_templates_seed: list[bot_template_domain.BotTemplate],
    get_db_session: Session,
) -> Generator[Tuple[list[cdt_domain.CommonDocumentTemplate], bot_template_domain.Id], None, None]:
    session = get_db_session
    common_document_template_repo = CommonDocumentTemplateRepository(session)

    bot_templates = bot_templates_seed
    bot_template_id = bot_templates[0].id
    common_document_templates_for_create = [
        cdt_domain.CommonDocumentTemplateForCreate(
            memo=cdt_domain.Memo(root="test"),
            basename=cdt_domain.Basename(root="test"),
            file_extension=cdt_domain.FileExtension("pdf"),
            data=b"test_data",
        ),
        cdt_domain.CommonDocumentTemplateForCreate(
            memo=cdt_domain.Memo(root="test"),
            basename=cdt_domain.Basename(root="test"),
            file_extension=cdt_domain.FileExtension("xlsx"),
            data=b"test_data",
        ),
    ]
    created_common_document_templates = [
        common_document_template_repo.create(
            bot_template_id=bot_template_id,
            common_document_template=common_document_template_for_create,
        )
        for common_document_template_for_create in common_document_templates_for_create
    ]

    yield created_common_document_templates, bot_template_id

    # テスト後処理
    for common_document_template in created_common_document_templates:
        common_document_template_to_delete = (
            session.execute(
                select(CommonDocumentTemplate).where(CommonDocumentTemplate.id == common_document_template.id.root)
            )
            .scalars()
            .first()
        )
        session.delete(common_document_template_to_delete)
    session.commit()


@pytest.fixture(params=[{"cleanup_resources": True}])
def chat_completions_seed(
    request,
    api_keys_seed: tuple[list[api_key_domain.ApiKey], bot_domain.Id],
    get_db_session: Session,
) -> Generator[ChatCompletionsSeed, None, None]:
    session = get_db_session

    api_keys, bot_id = api_keys_seed

    chat_completions_list = [
        [
            chat_completion_domain.ChatCompletion(
                messages=chat_completion_domain.Messages(
                    root=[
                        chat_completion_domain.Message(
                            role=chat_completion_domain.Role(chat_completion_domain.Role.USER),
                            content=chat_completion_domain.Content(root=f"{api_key.id.root}test"),
                        ),
                        chat_completion_domain.Message(
                            role=chat_completion_domain.Role(chat_completion_domain.Role.ASSISTANT),
                            content=chat_completion_domain.Content(root=f"{api_key.id.root}test"),
                        ),
                    ]
                ),
                answer=chat_completion_domain.Content(root=f"{api_key.id.root}test"),
                token_count=token_domain.TokenCount(root=100),
                data_points=[
                    chat_completion_domain.ChatCompletionDataPoint(
                        content=data_point.Content(root=f"{api_key.id.root}test"),
                        page_number=data_point.PageNumber(root=1),
                        chunk_name=data_point.ChunkName(root=f"{api_key.id.root}test"),
                        blob_path=data_point.BlobPath(root=f"{api_key.id.root}test"),
                        type=data_point.Type(data_point.Type.INTERNAL),
                        url=data_point.Url(root=f"{api_key.id.root}test"),
                        question_answer_id=None,
                        additional_info=None,
                        cite_number=data_point.CiteNumber(root=1),
                    )
                ],
            ),
        ]
        for api_key in api_keys
    ]

    chat_completion_with_api_key_tuple: list[tuple[api_key_domain.ApiKey, chat_completion_domain.ChatCompletion]] = []

    for i, chat_completions in enumerate(chat_completions_list):
        for chat_completion in chat_completions:
            chat_completion_to_create = ChatCompletion.from_domain(
                api_key_id=api_keys[i].id,
                chat_completion=chat_completion,
            )
            for chat_completion_data_point in chat_completion.data_points:
                chat_completion_data_point_to_create = ChatCompletionDataPoint.from_domain(
                    chat_completion_id=chat_completion.id,
                    chat_completion_data_point=chat_completion_data_point,
                )
                session.add(chat_completion_data_point_to_create)
            session.add(chat_completion_to_create)
            chat_completion_with_api_key_tuple.append((api_keys[i], chat_completion))
    session.commit()

    yield bot_id, chat_completion_with_api_key_tuple

    if not request.param["cleanup_resources"]:
        return

    # テスト後処理
    for chat_completions in chat_completions_list:
        for chat_completion in chat_completions:
            for chat_completion_data_point in chat_completion.data_points:
                chat_completion_data_point_to_delete = (
                    session.execute(
                        select(ChatCompletionDataPoint).where(
                            ChatCompletionDataPoint.id == chat_completion_data_point.id.root
                        )
                    )
                    .scalars()
                    .first()
                )
                session.delete(chat_completion_data_point_to_delete)
            chat_completion_to_delete = (
                session.execute(select(ChatCompletion).where(ChatCompletion.id == chat_completion.id.root))
                .scalars()
                .first()
            )
            session.delete(chat_completion_to_delete)
    session.commit()


@pytest.fixture
def liked_bot_seed(
    user_seed: UserSeed,
    bots_seed: BotsSeed,
    get_db_session: Session,
) -> Generator[Tuple[user_domain.Id, list[bot_domain.Id], Tenant], None, None]:
    session = get_db_session

    user_id, _, _, _, _ = user_seed
    bots, _, tenant, _ = bots_seed

    new_liked_bots: list[UserLikedBot] = [
        UserLikedBot(
            id=uuid4(),
            user_id=user_id.value,
            bot_id=bots[0].id.value,
        ),
        UserLikedBot(
            id=uuid4(),
            user_id=user_id.value,
            bot_id=bots[1].id.value,
        ),
    ]

    try:
        session.add_all(new_liked_bots)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    liked_bot_ids = [bot_domain.Id(value=liked_bot.bot_id) for liked_bot in new_liked_bots]

    yield user_id, liked_bot_ids, tenant

    # テスト後処理
    for fbi in liked_bot_ids:
        liked_bot_to_delete = (
            session.execute(
                select(UserLikedBot).where(
                    UserLikedBot.bot_id == fbi.value,
                    UserLikedBot.user_id == user_id.value,
                )
            )
            .scalars()
            .first()
        )
        session.delete(liked_bot_to_delete)
    session.commit()


@pytest.fixture
def workflow_seed(bots_seed: BotsSeed, get_db_session: Session) -> Generator[WorkflowSeed, None, None]:
    session = get_db_session
    workflow_repo = WorkflowRepository(session)
    bots, _, tenant, group = bots_seed
    bot_id = bots[0].id
    workflow_for_create = workflow_domain.WorkflowForCreate(
        name=workflow_domain.Name(root="test_create_workflow_name"),
        description=workflow_domain.Description(root="test_create_workflow_description"),
        type=workflow_domain.WorkflowType(root=workflow_domain.WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS),
        configs=workflow_domain.WorkflowConfigList(
            items=[
                workflow_domain.WorkflowConfig(key="bot_id", value=bot_id.value),
                workflow_domain.WorkflowConfig(key="labor_rate_table_file_name", value="lrt.xlsx"),
                workflow_domain.WorkflowConfig(key="disposal_asset_statement_file_name", value="dasf.xlsx"),
            ]
        ),
    )
    workflow_repo.create(group_id=group.id, wfc=workflow_for_create)

    created_workflow = session.execute(select(Workflow).where(Workflow.id == workflow_for_create.id.root)).scalar_one()
    yield created_workflow.to_domain(), tenant
    # # テスト後処理
    # session.delete(created_workflow)
    # session.commit()


@pytest.fixture
def workflow_list_seed(bots_seed: BotsSeed, get_db_session: Session) -> Generator[WorkflowListSeed, None, None]:
    session = get_db_session
    workflow_repo = WorkflowRepository(session)

    bots, _, tenant, group = bots_seed
    bot_ids = [bot.id for bot in bots]
    workflow_for_create_list = [
        workflow_domain.WorkflowForCreate(
            name=workflow_domain.Name(root="test_create_workflow_name"),
            description=workflow_domain.Description(root="test_create_workflow_description"),
            type=workflow_domain.WorkflowType(
                root=workflow_domain.WorkflowTypeEnum.GENERATE_CONSTRUCTION_SPECIFICATIONS
            ),
            configs=workflow_domain.WorkflowConfigList(
                items=[
                    workflow_domain.WorkflowConfig(key="bot_id", value=bot_id.value),
                ]
            ),
        )
        for bot_id in bot_ids
    ]
    for workflow_for_create in workflow_for_create_list:
        workflow_repo.create(group_id=group.id, wfc=workflow_for_create)
    created_workflows = session.execute(select(Workflow).where(Workflow.group_id == group.id.value)).scalars().all()

    yield [workflow.to_domain() for workflow in created_workflows], group, tenant


@pytest.fixture
def workflow_thread_seed(
    workflow_seed: WorkflowSeed, get_db_session: Session
) -> Generator[WorkflowThreadSeed, None, None]:
    session = get_db_session
    workflow_thread_repo = WorkflowThreadRepository(session)
    workflow, tenant = workflow_seed
    user_id = user_domain.Id(value=1)
    wf_thread_for_create = wf_thread_domain.WorkflowThreadForCreate(
        title=wf_thread_domain.Title(root="test_create_workflow_thread_title"),
    )
    created_workflow_thread = workflow_thread_repo.create(
        workflow_id=workflow.id, user_id=user_id, wf_thread_for_create=wf_thread_for_create
    )
    yield tenant.id, workflow.id, created_workflow_thread

    # # テスト後処理
    # workflow_thread_to_delete = (
    #     session.execute(select(WorkflowThread).where(WorkflowThread.id == created_workflow_thread.id.root))
    #     .scalars()
    #     .first()
    # )
    # session.delete(workflow_thread_to_delete)
    # session.commit()


@pytest.fixture
def workflow_thread_flow_seed(
    request: pytest.FixtureRequest, workflow_thread_seed: WorkflowThreadSeed, get_db_session: Session
) -> Generator[WorkflowThreadFlowSeed, None, None]:
    session = get_db_session
    workflow_thread_flow_repo = WorkflowThreadRepository(session)
    tenant_id, workflow_id, workflow_thread = workflow_thread_seed
    wf_thread_flow_for_create = wf_thread_flow_domain.WorkflowThreadFlowForCreate()
    created_workflow_thread_flow = workflow_thread_flow_repo.create_flow(
        wf_thread_id=workflow_thread.id, wf_thread_flow_for_create=wf_thread_flow_for_create
    )

    print("created_workflow_thread_flow", created_workflow_thread_flow)

    yield tenant_id, workflow_id, workflow_thread.id, created_workflow_thread_flow

    # # テスト後処理
    # workflow_thread_flow_to_delete = (
    #     session.execute(
    #         select(WorkflowThreadFlow).where(WorkflowThreadFlow.id == created_workflow_thread_flow.id.root)
    #     )
    #     .scalars()
    #     .first()
    # )
    # session.delete(workflow_thread_flow_to_delete)
    # session.commit()


@pytest.fixture
def workflow_thread_flow_step_seed(
    workflow_thread_flow_seed: WorkflowThreadFlowSeed, get_db_session: Session
) -> Generator[WorkflowThreadFlowStepSeed, None, None]:
    session = get_db_session
    workflow_thread_flow_repo = WorkflowThreadRepository(session)
    tenant_id, workflow_id, workflow_thread_id, workflow_thread_flow = workflow_thread_flow_seed
    wf_thread_flow_step_for_create = wf_thread_flow_step_domain.WorkflowThreadFlowStepForCreate(
        step=wf_thread_flow_step_domain.Step(root=1),
        input=wf_thread_flow_step_domain.Input(
            items=[wf_thread_flow_step_domain.InputItem(key="test_key", value="test_value")]
        ),
        output=wf_thread_flow_step_domain.Output(
            items=[wf_thread_flow_step_domain.OutputItem(key="test_key", value="test_value")]
        ),
        is_active=wf_thread_flow_step_domain.IsActive(root=True),
        status=wf_thread_flow_step_domain.Status.PROCESSING,
        token_count=token_domain.TokenCount(root=100),
    )

    created_workflow_thread_flow_step = workflow_thread_flow_repo.create_flow_step(
        wf_thread_flow_id=workflow_thread_flow.id, wf_thread_flow_step_for_create=wf_thread_flow_step_for_create
    )
    yield tenant_id, workflow_id, workflow_thread_id, workflow_thread_flow.id, created_workflow_thread_flow_step

    # # テスト後処理
    # workflow_thread_flow_step_to_delete = (
    #     session.execute(
    #         select(WorkflowThreadFlowStep).where(
    #             WorkflowThreadFlowStep.id == created_workflow_thread_flow_step.id.root
    #         )
    #     )
    #     .scalars()
    #     .first()
    # )
    # session.delete(workflow_thread_flow_step_to_delete)
    # session.commit()
