from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.box.box import IBoxService
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.libs.exceptions import BadRequest, Conflict, NotFound


class CreateDocumentFolderInput(BaseModel):
    document_folder_for_create: document_folder_domain.DocumentFolderForCreate
    parent_document_folder_id: document_folder_domain.Id | None


class StartExternalDataConnectionInput(BaseModel):
    parent_document_folder_id: document_folder_domain.Id | None
    external_id: external_data_connection_domain.ExternalId
    external_type: external_data_connection_domain.ExternalDataConnectionType
    sync_schedule: external_data_connection_domain.SyncSchedule | None


class IDocumentFolderUseCase(ABC):
    @abstractmethod
    def get_document_folders_by_parent_document_folder_id(
        self, bot_id: bot_domain.Id, parent_document_folder_id: document_folder_domain.Id | None
    ) -> list[document_folder_domain.DocumentFolderWithDocumentProcessingStats]:
        pass

    @abstractmethod
    def create_document_folder(
        self, bot_id: bot_domain.Id, document_folder: CreateDocumentFolderInput
    ) -> document_folder_domain.DocumentFolder:
        pass

    @abstractmethod
    def get_root_document_folder_by_bot_id(self, bot_id: bot_domain.Id) -> document_folder_domain.DocumentFolder:
        pass

    @abstractmethod
    def get_with_ancestors_by_id_and_bot_id(
        self, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> document_folder_domain.DocumentFolderWithAncestors:
        pass

    @abstractmethod
    def update_document_folder(
        self,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_folder_for_update: document_folder_domain.DocumentFolderForUpdate,
    ) -> document_folder_domain.DocumentFolder:
        pass

    @abstractmethod
    def update_document_folder_v2(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_folder_for_update: document_folder_domain.DocumentFolderForUpdate,
    ) -> document_folder_domain.DocumentFolder:
        pass

    @abstractmethod
    def delete_document_folder(self, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id) -> None:
        pass

    @abstractmethod
    def delete_document_folder_v2(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> None:
        pass

    @abstractmethod
    def move_document_folder(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        new_parent_document_folder_id: document_folder_domain.Id,
    ) -> None:
        pass

    @abstractmethod
    def get_external_root_document_folder_to_sync(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id | None,
        external_data_connection_type: external_data_connection_domain.ExternalDataConnectionType,
        external_data_shared_url: str,
    ) -> document_folder_domain.ExternalDocumentFolderToSync:
        pass

    @abstractmethod
    def start_external_data_connection(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        input: StartExternalDataConnectionInput,
    ) -> None:
        pass

    @abstractmethod
    def resync_external_document_folder(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        external_document_folder_id: document_folder_domain.Id,
    ) -> None:
        pass

    @abstractmethod
    def get_external_document_folder_url(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        external_data_connection_type: external_data_connection_domain.ExternalDataConnectionType,
    ) -> external_data_connection_domain.ExternalUrl:
        pass


class DocumentFolderUseCase(IDocumentFolderUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
        box_service: IBoxService,
    ):
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.document_repo = document_repo
        self.document_folder_repo = document_folder_repo
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service
        self.box_service = box_service

    def get_document_folders_by_parent_document_folder_id(
        self, bot_id: bot_domain.Id, parent_document_folder_id: document_folder_domain.Id | None
    ) -> list[document_folder_domain.DocumentFolderWithDocumentProcessingStats]:
        if parent_document_folder_id is None:
            parent_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        else:
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(parent_document_folder_id, bot_id)
        document_folders = self.document_folder_repo.find_by_parent_document_folder_id(
            bot_id, parent_document_folder.id
        )

        document_folders_with_document_processing_stats: list[
            document_folder_domain.DocumentFolderWithDocumentProcessingStats
        ] = []
        for document_folder in document_folders:
            document_folder_with_document_status_count = (
                document_folder_domain.DocumentFolderWithDocumentProcessingStats(**document_folder.model_dump())
            )

            if document_folder.external_id is None:
                document_folders_with_document_processing_stats.append(document_folder_with_document_status_count)
                continue

            # 外部連携フォルダの場合は、子ドキュメントのステータスを数えて返す
            documents = self.document_repo.find_by_parent_document_folder_id(bot_id, document_folder.id)
            document_folder_with_document_status_count.document_processing_stats = (
                document_folder_domain.DocumentProcessingStats.from_statuses(
                    [document.status for document in documents]
                )
            )
            document_folders_with_document_processing_stats.append(document_folder_with_document_status_count)

        return document_folders_with_document_processing_stats

    def create_document_folder(
        self, bot_id: bot_domain.Id, document_folder: CreateDocumentFolderInput
    ) -> document_folder_domain.DocumentFolder:
        if document_folder.parent_document_folder_id is None:
            parent_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        else:
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(
                document_folder.parent_document_folder_id, bot_id
            )

        # validate name
        try:
            existing_document_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
                parent_document_folder.id,
                document_folder.document_folder_for_create.name,
            )
            if len(existing_document_folders) > 0:
                raise BadRequest("フォルダの名前が重複しています")
        except NotFound:
            pass

        return self.document_folder_repo.create(
            bot_id, parent_document_folder.id, document_folder.document_folder_for_create
        )

    def get_root_document_folder_by_bot_id(self, bot_id: bot_domain.Id) -> document_folder_domain.DocumentFolder:
        return self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)

    def get_with_ancestors_by_id_and_bot_id(
        self, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> document_folder_domain.DocumentFolderWithAncestors:
        document_folders = self.document_folder_repo.find_with_ancestors_by_id_and_bot_id(document_folder_id, bot_id)

        return document_folders

    def update_document_folder(
        self,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_folder_for_update: document_folder_domain.DocumentFolderForUpdate,
    ) -> document_folder_domain.DocumentFolder:
        # document_folder_id のフォルダの存在を確認
        folder = self.document_folder_repo.find_with_ancestors_by_id_and_bot_id(document_folder_id, bot_id)
        try:
            parent_folder = folder.get_parent_folder()
        except NotFound:
            raise BadRequest("ルートフォルダは更新できません")
        # folder name が重複していないか確認
        existing_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
            parent_folder.id, document_folder_for_update.name
        )
        existing_folders_without_target = [
            existing_folder for existing_folder in existing_folders if existing_folder.id != document_folder_id
        ]
        if len(existing_folders_without_target) > 0:
            raise Conflict("フォルダの名前が重複しています")

        folder.update(document_folder_for_update)

        return self.document_folder_repo.update(bot_id, folder)

    def update_document_folder_v2(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_folder_for_update: document_folder_domain.DocumentFolderForUpdate,
    ) -> document_folder_domain.DocumentFolder:
        # document_folder_id のフォルダの存在を確認
        folder = self.document_folder_repo.find_with_ancestors_by_id_and_bot_id(document_folder_id, bot_id)
        try:
            parent_folder = folder.get_parent_folder()
        except NotFound:
            raise BadRequest("ルートフォルダは更新できません")

        # folder name が重複していないか確認
        existing_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
            parent_folder.id, document_folder_for_update.name
        )
        existing_folders_without_target = [
            existing_folder for existing_folder in existing_folders if existing_folder.id != document_folder_id
        ]
        if len(existing_folders_without_target) > 0:
            raise Conflict("フォルダの名前が重複しています")

        # 更新
        folder.update(document_folder_for_update)
        updated_folder = self.document_folder_repo.update(bot_id, folder)

        documents_to_update = self.document_repo.find_all_descendants_documents_by_ancestor_folder_id(
            bot_id, updated_folder.id
        )

        if any(document.status == document_domain.Status.PENDING for document in documents_to_update):
            raise BadRequest("処理中のドキュメントが含まれています")

        # ドキュメントのステータスを pending に更新
        for document in documents_to_update:
            document.update_status_to_pending()
        self.document_repo.bulk_update(documents_to_update)
        # queueにメッセージを送信
        self.queue_storage_service.send_message_to_sync_document_path_queue(
            tenant_id=tenant.id,
            bot_id=bot_id,
            document_folder_id=updated_folder.id,
            document_ids=[document.id for document in documents_to_update],
        )
        return updated_folder

    def delete_document_folder(self, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id) -> None:
        # validate
        # 子フォルダが存在する場合は削除できない
        descendant_folders = self.document_folder_repo.find_descendants_by_id(bot_id, document_folder_id)
        if len(descendant_folders) > 0:
            raise BadRequest("フォルダに子フォルダが存在するため削除できません")

        # 　ドキュメントが存在する場合は削除できない
        child_documents = self.document_repo.find_by_parent_document_folder_id(bot_id, document_folder_id)
        if len(child_documents) > 0:
            raise BadRequest("フォルダにドキュメントが存在するため削除できません")

        # ルートフォルダの場合は削除できない
        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        if document_folder_id == root_document_folder.id:
            raise BadRequest("ルートフォルダは削除できません")

        self.document_folder_repo.delete_by_ids(bot_id, [document_folder_id])

    def delete_document_folder_v2(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> None:
        # validate
        # bot_idとdocument_folder_idの関係を確認
        self.document_folder_repo.find_by_id_and_bot_id(document_folder_id, bot_id)
        # ルートフォルダの場合は削除できない
        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        if document_folder_id == root_document_folder.id:
            raise BadRequest("ルートフォルダは削除できません")

        descendant_folders = self.document_folder_repo.find_descendants_by_id(bot_id, document_folder_id)
        document_folder_ids_to_delete = [folder.id for folder in descendant_folders] + [document_folder_id]

        self.document_repo.delete_by_folder_ids(bot_id, document_folder_ids_to_delete)

        self.document_folder_repo.delete_by_ids(bot_id, document_folder_ids_to_delete)

        self.queue_storage_service.send_message_to_delete_document_folders_queue(
            tenant_id, bot_id, document_folder_ids_to_delete
        )

    def move_document_folder(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        new_parent_document_folder_id: document_folder_domain.Id,
    ) -> None:
        # bot_idにフォルダが存在するか確認
        document_folder = self.document_folder_repo.find_by_id_and_bot_id(document_folder_id, bot_id)
        self.document_folder_repo.find_by_id_and_bot_id(new_parent_document_folder_id, bot_id)

        # ルートフォルダは移動できない
        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        if document_folder_id == root_document_folder.id:
            raise BadRequest("ルートフォルダは移動できません")

        # 移動先が自分自身の場合は移動できない
        if document_folder_id == new_parent_document_folder_id:
            raise BadRequest("選択されたフォルダに移動することはできません")

        # 移動先が自分の子孫フォルダの場合は移動できない
        descendant_folders = self.document_folder_repo.find_descendants_by_id(bot_id, document_folder_id)
        if new_parent_document_folder_id in [folder.id for folder in descendant_folders]:
            raise BadRequest("選択されたフォルダに移動することはできません")

        # 移動先に同一の名前のフォルダが存在する場合は移動できない
        if document_folder.name is not None:
            existing_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
                new_parent_document_folder_id, document_folder.name
            )
            if len(existing_folders) > 0:
                raise Conflict("移動先に同一の名前のフォルダが存在します")

        # 処理中のドキュメントが含まれる場合はフォルダ移動できない
        documents_to_update = self.document_repo.find_all_descendants_documents_by_ancestor_folder_id(
            bot_id, document_folder_id
        )
        if any(document.status == document_domain.Status.PENDING for document in documents_to_update):
            raise BadRequest("処理中のドキュメントが含まれています")

        # フォルダを移動
        self.document_folder_repo.move_document_folder(bot_id, document_folder_id, new_parent_document_folder_id)

        # AI Search のデータを更新
        # ドキュメントのステータスを pending に更新
        for document in documents_to_update:
            document.update_status_to_pending()
        self.document_repo.bulk_update(documents_to_update)
        # queueにメッセージを送信
        self.queue_storage_service.send_message_to_sync_document_path_queue(
            tenant_id=tenant.id,
            bot_id=bot_id,
            document_folder_id=new_parent_document_folder_id,
            document_ids=[document.id for document in documents_to_update],
        )

    def get_external_root_document_folder_to_sync(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id | None,
        external_data_connection_type: external_data_connection_domain.ExternalDataConnectionType,
        external_data_shared_url: str,
    ) -> document_folder_domain.ExternalDocumentFolderToSync:
        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, external_data_connection_type
        )
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        )

        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                sharepoint_credentials = decrypted_credentials.to_sharepoint_credentials()
                external_root_document_folder_to_sync = asyncio.run(
                    self.msgraph_service.get_external_document_folder_to_sync(
                        sharepoint_credentials, external_data_shared_url
                    )
                )
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                box_credentials = decrypted_credentials.to_box_credentials()
                external_root_document_folder_to_sync = self.box_service.get_external_document_folder_to_sync(
                    box_credentials, external_data_shared_url
                )
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        if parent_document_folder_id is None:
            parent_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        else:
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(parent_document_folder_id, bot_id)

        existing_document_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
            parent_document_folder.id,
            external_root_document_folder_to_sync.name,
        )
        if len(existing_document_folders) > 0:
            external_root_document_folder_to_sync.update_is_valid(False)

        return external_root_document_folder_to_sync

    def start_external_data_connection(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        input: StartExternalDataConnectionInput,
    ) -> None:
        # tenantとbotの関係を確認
        self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, input.external_type
        )
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        )
        match input.external_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                sharepoint_credentials = decrypted_credentials.to_sharepoint_credentials()
                external_root_document_folder = asyncio.run(
                    self.msgraph_service.get_document_folder_by_id(
                        sharepoint_credentials,
                        external_data_connection_domain.SharepointExternalId.from_external_id(input.external_id),
                    )
                )
                external_sync_metadata = asyncio.run(
                    self.msgraph_service.get_document_folder_delta_token_by_id(
                        sharepoint_credentials,
                        external_data_connection_domain.SharepointExternalId.from_external_id(input.external_id),
                    )
                )
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                box_credentials = decrypted_credentials.to_box_credentials()
                external_root_document_folder = self.box_service.get_document_folder_by_id(
                    box_credentials,
                    external_data_connection_domain.BoxExternalId.from_external_id(input.external_id),
                )
                external_sync_metadata = external_data_connection_domain.ExternalSyncMetadata(root={})
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        external_document_folder_for_create = document_folder_domain.ExternalDocumentFolderForCreate(
            name=external_root_document_folder.name,
            external_id=input.external_id,
            external_type=input.external_type,
            external_updated_at=external_root_document_folder.external_updated_at,
            sync_schedule=input.sync_schedule,
            external_sync_metadata=external_sync_metadata,
            last_synced_at=external_data_connection_domain.LastSyncedAt(root=datetime.now(timezone.utc)),
        )

        if input.parent_document_folder_id is None:
            parent_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        else:
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(
                input.parent_document_folder_id, bot_id
            )

        # validate document folder name
        existing_document_folders = self.document_folder_repo.find_by_parent_document_folder_id_and_name(
            parent_document_folder.id,
            external_document_folder_for_create.name,
        )

        if len(existing_document_folders) > 0:
            raise BadRequest("フォルダの名前が重複しています")

        document_folder = self.document_folder_repo.create_external_document_folder(
            bot_id,
            parent_document_folder.id,
            external_document_folder_for_create,
        )

        self.queue_storage_service.send_message_to_start_external_data_connection_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_id=document_folder.id,
        )

    def resync_external_document_folder(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        external_document_folder_id: document_folder_domain.Id,
    ) -> None:
        # tenantとbotの関係を確認
        self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        external_document_folder = self.document_folder_repo.find_external_document_folder_by_id_and_bot_id(
            external_document_folder_id, bot_id
        )
        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, external_document_folder.external_type
        )

        documents_in_folder = self.document_repo.find_by_parent_document_folder_id(bot_id, external_document_folder_id)
        if any(document.status == document_domain.Status.PENDING for document in documents_in_folder):
            raise BadRequest("処理中のドキュメントが含まれています。")

        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        )
        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                credentials = decrypted_credentials.to_sharepoint_credentials()
                is_authorized = asyncio.run(self.msgraph_service.is_authorized_client(credentials))
                if not is_authorized:
                    raise BadRequest("連携情報が無効です。外部データ連携情報を再設定してください。")
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        # TODO: queueにメッセージを送信
        # self.queue_storage_service.send_message_to_resync_external_document_folder_queue(
        #     tenant_id=tenant_id,
        #     bot_id=bot_id,
        #     document_folder_id=external_document_folder_id,
        # )

    def get_external_document_folder_url(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        external_data_connection_type: external_data_connection_domain.ExternalDataConnectionType,
    ) -> external_data_connection_domain.ExternalUrl:
        external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
            tenant_id, external_data_connection_type
        )
        external_document_folder = self.document_folder_repo.find_external_document_folder_by_id_and_bot_id(
            document_folder_id, bot_id
        )
        decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
            external_data_connection.encrypted_credentials,
            external_data_connection.external_data_connection_type,
        )

        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                sharepoint_credentials = decrypted_credentials.to_sharepoint_credentials()
                sharepoint_external_id = external_data_connection_domain.SharepointExternalId.from_external_id(
                    external_document_folder.external_id
                )
                url = asyncio.run(
                    self.msgraph_service.get_external_document_folder_url(
                        sharepoint_credentials, sharepoint_external_id
                    )
                )
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                box_credentials = decrypted_credentials.to_box_credentials()
                box_external_id = external_data_connection_domain.BoxExternalId.from_external_id(
                    external_document_folder.external_id
                )
                url = self.box_service.get_external_document_folder_url(box_credentials, box_external_id)
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        return url
