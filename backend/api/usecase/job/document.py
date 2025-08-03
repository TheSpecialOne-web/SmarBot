from abc import ABC, abstractmethod
import asyncio

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.models.bot.repository import IBotRepository
from api.domain.models.data_point.blob_path import BlobPath
from api.domain.models.document.memo import Memo
from api.domain.models.document.repository import IDocumentRepository
from api.domain.models.document_folder.repository import IDocumentFolderRepository
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.models.tenant.repository import ITenantRepository
from api.domain.services.cognitive_search.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.box.box import IBoxService
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.libs.exceptions import BadRequest, NotFound
from api.libs.logging import logging

logger = logging.getLogger(__name__)


class IDocumentUseCase(ABC):
    @abstractmethod
    def sync_document_path(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        documnt_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        pass

    @abstractmethod
    def sync_document_location(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> None:
        pass


class DocumentUseCase(IDocumentUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: ITenantRepository,
        bot_repo: IBotRepository,
        document_repo: IDocumentRepository,
        document_folder_repo: IDocumentFolderRepository,
        cognitive_search_service: ICognitiveSearchService,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
        box_service: IBoxService,
    ):
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.document_repo = document_repo
        self.document_folder_repo = document_folder_repo
        self.cognitive_search_service = cognitive_search_service
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service
        self.box_service = box_service

    def _create_blob_path(
        self,
        bot_id: bot_domain.Id,
        document: document_domain.Document,
        root_folder: document_folder_domain.DocumentFolder,
    ) -> BlobPath:
        is_root_folder = document.document_folder_id == root_folder.id
        return BlobPath(
            root=(
                f"{bot_id.value}/{document.name.value}.{document.file_extension.value}"
                if is_root_folder
                else f"{bot_id.value}/{document.document_folder_id.root}/{document.name.value}.{document.file_extension.value}"
            )
        )

    Credentials = (
        external_data_connection_domain.SharepointDecryptedCredentials
        | external_data_connection_domain.BoxDecryptedCredentials
        | external_data_connection_domain.GoogleDriveDecryptedCredentials
    )

    def _get_credentials(
        self,
        tenant_id: tenant_domain.Id,
        external_type: external_data_connection_domain.ExternalDataConnectionType,
    ) -> Credentials:
        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, external_type
        )
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
        )
        match external_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                return decrypted_credentials.to_sharepoint_credentials()
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                return decrypted_credentials.to_box_credentials()
            case _:
                raise BadRequest("未対応の外部データ連携です。")

    def _get_full_path(
        self,
        document: document_domain.DocumentWithAncestorFolders,
        external_type: external_data_connection_domain.ExternalDataConnectionType | None,
        credentials: external_data_connection_domain.DecryptedCredentials | None,
    ) -> str:
        full_path = document.get_full_path()
        if document.external_id is not None and credentials is not None:
            if external_type == external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                external_document = asyncio.run(
                    self.msgraph_service.get_document_by_id(
                        credentials=credentials.to_sharepoint_credentials(),
                        external_id=external_data_connection_domain.SharepointExternalId.from_external_id(
                            document.external_id
                        ),
                    )
                )
            elif external_type == external_data_connection_domain.ExternalDataConnectionType.BOX:
                external_document = self.box_service.get_document_by_id(
                    credentials=credentials.to_box_credentials(),
                    external_id=external_data_connection_domain.BoxExternalId.from_external_id(document.external_id),
                )
            else:
                raise BadRequest("未対応の外部データ連携です。")
            full_path = f"{full_path},{external_document.external_full_path.root}"
        return full_path

    def sync_document_path(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_ids: list[document_domain.Id],
    ):
        MAX_PROCESS_CHUNK_COUNT = 10000
        MAX_PROCESS_DOCUMENT_COUNT = 100

        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        document_folder = self.document_folder_repo.find_by_id_and_bot_id(document_folder_id, bot_id)
        is_ursa = bot.approach == bot_domain.Approach.URSA

        search_service_endpoint = bot.search_service_endpoint if is_ursa else tenant.search_service_endpoint
        index_name = bot.index_name if is_ursa else tenant.index_name
        if search_service_endpoint is None or index_name is None:
            raise Exception("検索サービスのエンドポイントまたはインデックス名が設定されていません")

        # MAX_PROCESS_CHUNK_COUNTを超えないようにドキュメントを設定する。
        document_ids_to_process: list[document_domain.Id] = []
        total_document_chunk_count = 0

        for document_id in document_ids[:MAX_PROCESS_DOCUMENT_COUNT]:
            if is_ursa:
                document_chunk_count = self.cognitive_search_service.get_ursa_document_chunk_count_by_document_id(
                    endpoint=search_service_endpoint,
                    index_name=index_name,
                    bot_id=bot_id,
                    document_id=document_id,
                )
            else:
                document_chunk_count = self.cognitive_search_service.get_document_chunk_count_by_document_id(
                    endpoint=search_service_endpoint,
                    index_name=index_name,
                    bot_id=bot_id,
                    document_id=document_id,
                )
            # 上限を超える場合は処理を中断
            if total_document_chunk_count + document_chunk_count > MAX_PROCESS_CHUNK_COUNT:
                break
            total_document_chunk_count += document_chunk_count
            document_ids_to_process.append(document_id)

        # 更新対象ドキュメントとその祖先フォルダを取得
        documents_to_process = self.document_repo.find_documents_with_ancestor_folders_by_ids(
            bot_id=bot_id, ids=document_ids_to_process
        )

        credentials = None
        if document_folder.external_type is not None:
            external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
                tenant_id, document_folder.external_type
            )
            credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
                external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
            )

        # AI Searchの処理
        def _update_index_documents():
            index_documents = self.cognitive_search_service.find_index_documents_by_document_ids(
                endpoint=search_service_endpoint,
                index_name=index_name,
                document_ids=[document.id for document in documents_to_process],
                document_chunk_count=total_document_chunk_count,
            )
            for index_document in index_documents:
                target = next(
                    (document for document in documents_to_process if document.id.value == index_document.document_id),
                    None,
                )
                if target is None:
                    raise NotFound("ドキュメントが見つかりません")
                full_path = self._get_full_path(target, document_folder.external_type, credentials)
                index_document.update_full_path_in_content(full_path)
            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint,
                index_name=index_name,
                documents=index_documents,
            )

        def _update_ursa_index_documents():
            index_documents = self.cognitive_search_service.find_ursa_index_documents_by_document_ids(
                endpoint=search_service_endpoint,
                index_name=index_name,
                document_ids=[document.id for document in documents_to_process],
                document_chunk_count=total_document_chunk_count,
            )
            for index_document in index_documents:
                target = next(
                    (document for document in documents_to_process if document.id.value == index_document.document_id),
                    None,
                )
                if target is None:
                    raise NotFound("ドキュメントが見つかりません")
                full_path = self._get_full_path(target, document_folder.external_type, credentials)
                index_document.update_param_from_full_path(full_path)
            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint,
                index_name=index_name,
                documents=index_documents,
            )

        if is_ursa:
            _update_ursa_index_documents()
        else:
            _update_index_documents()

        # ステータスを更新する
        updated_documents = self.document_repo.find_by_ids_and_bot_id(
            bot_id=bot_id, document_ids=[document.id for document in documents_to_process]
        )
        for document in updated_documents:
            document.update_status_to_completed()
        self.document_repo.bulk_update(updated_documents)

        remaining_document_ids = [
            document_id for document_id in document_ids if document_id not in document_ids_to_process
        ]
        if len(remaining_document_ids) > 0:
            self.queue_storage_service.send_message_to_sync_document_path_queue(
                tenant_id=tenant_id,
                bot_id=bot_id,
                document_folder_id=document_folder_id,
                document_ids=remaining_document_ids,
            )
            return
        logger.info("すべてのドキュメントを処理しました。")

    def sync_document_location(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        document = self.document_repo.find_by_id_and_bot_id(document_id, bot.id)

        is_ursa = bot.approach == bot_domain.Approach.URSA

        search_service_endpoint = bot.search_service_endpoint if is_ursa else tenant.search_service_endpoint
        index_name = bot.index_name if is_ursa else tenant.index_name
        if search_service_endpoint is None or index_name is None:
            raise Exception("検索サービスのエンドポイントまたはインデックス名が設定されていません")

        # blobのドキュメントのパスを変更する
        root_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        new_blob_path = self._create_blob_path(bot_id=bot_id, document=document, root_folder=root_folder)
        if is_ursa:
            document_chunk_count = self.cognitive_search_service.get_ursa_document_chunk_count_by_document_id(
                endpoint=search_service_endpoint,
                index_name=index_name,
                bot_id=bot_id,
                document_id=document_id,
            )
        else:
            document_chunk_count = self.cognitive_search_service.get_document_chunk_count_by_document_id(
                endpoint=search_service_endpoint,
                index_name=index_name,
                bot_id=bot_id,
                document_id=document_id,
            )

        document_with_ancestor_folders = self.document_repo.find_with_ancestor_folders_by_id(
            bot_id=bot_id, id=document_id
        )

        # AI Searchの処理
        def _process_index_documents():
            index_documents = self.cognitive_search_service.find_index_documents_by_document_ids(
                endpoint=search_service_endpoint,
                index_name=index_name,
                document_ids=[document_id],
                document_chunk_count=document_chunk_count,
            )
            for d in index_documents:
                d.update_blob_path(new_blob_path.root)
                d.update_full_path_in_content(document_with_ancestor_folders.get_full_path())
                d.update_document_folder_id(str(document.document_folder_id.root))
                d.update_updated_at()
            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint,
                index_name=index_name,
                documents=index_documents,
            )

        def _process_ursa_index_documents():
            ursa_index_documents = self.cognitive_search_service.find_ursa_index_documents_by_document_ids(
                endpoint=search_service_endpoint,
                index_name=index_name,
                document_ids=[document_id],
                document_chunk_count=document_chunk_count,
            )
            document_full_path = document_with_ancestor_folders.get_full_path()
            memo = Memo(
                value="Z:\\"
                + document_full_path.replace("/", "\\")
                + "."
                + document_with_ancestor_folders.file_extension.value
            )
            document.update_memo(memo)
            for ud in ursa_index_documents:
                ud.update_full_path(memo.value)
                ud.update_document_folder_id(str(document.document_folder_id.root))
                ud.update_updated_at()
            self.cognitive_search_service.create_or_update_document_chunks(
                endpoint=search_service_endpoint,
                index_name=index_name,
                documents=ursa_index_documents,
            )

        if is_ursa:
            _process_ursa_index_documents()
        else:
            _process_index_documents()

        document.update_status_to_completed()
        self.document_repo.update(document)
        logger.info(f"ドキュメントのパスを更新しました。document_id: {document_id}")
