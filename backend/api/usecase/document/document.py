from abc import ABC, abstractmethod
import asyncio
from typing import Literal, Optional, TypedDict

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.document.memo import Memo
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.msgraph.msgraph import IMsgraphService
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.exceptions import BadRequest, NotFound
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger

from .types import DocumentWithCreator, GetDocumentsOutput


class DocumentUploadError(TypedDict):
    type: Literal[
        "document_exists",
        "get_document_error",
        "create_document_error",
        "upload_document_error",
    ]
    message: str
    document_id: Optional[document_domain.Id]


class CreateDocumentsInput(BaseModel):
    documents_for_create: list[document_domain.DocumentForCreate]
    parent_document_folder_id: document_folder_domain.Id | None = None


class GetDocumentDetailOutput(DocumentWithCreator):
    document_folder_name: document_folder_domain.Name | None
    document_folder_created_at: document_folder_domain.CreatedAt
    document_folder_ancestor_folders: list[document_folder_domain.DocumentFolderWithOrder]
    signed_url_original: document_domain.SignedUrl
    signed_url_pdf: Optional[document_domain.SignedUrl]
    external_url: external_data_connection_domain.ExternalUrl | None = None


class CreateOrUpdateDocumentFeedbackInput(BaseModel):
    bot_id: bot_domain.Id
    document_id: document_domain.Id
    user_id: user_domain.Id
    evaluation: document_feedback_domain.Evaluation | None


class IDocumentUseCase(ABC):
    @abstractmethod
    def create_documents(self, tenant: tenant_domain.Tenant, bot_id: bot_domain.Id, input: CreateDocumentsInput):
        pass

    @abstractmethod
    def get_documents(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id | None,
    ) -> GetDocumentsOutput:
        pass

    @abstractmethod
    def get_all_documents(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> GetDocumentsOutput:
        pass

    @abstractmethod
    def get_document_detail(
        self, tenant: tenant_domain.Tenant, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> GetDocumentDetailOutput:
        pass

    @abstractmethod
    def delete_document(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> None:
        pass

    @abstractmethod
    def update_document(
        self,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document: document_domain.DocumentForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def update_document_v2(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document: document_domain.DocumentForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def add_chunks(
        self, bot_id: bot_domain.Id, document_id: document_domain.Id, chunks: document_domain.ChunksForCreate
    ) -> None:
        pass

    @abstractmethod
    def delete_documents(self, bot_id: bot_domain.Id, document_ids: list[document_domain.Id]) -> None:
        pass

    @abstractmethod
    def create_or_update_document_feedback(self, input: CreateOrUpdateDocumentFeedbackInput) -> None:
        pass

    @abstractmethod
    def move_document(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        new_document_folder_id: document_folder_domain.Id,
    ) -> None:
        pass


class DocumentUseCase(IDocumentUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        user_repo: user_domain.IUserRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        cognitive_search_service: ICognitiveSearchService,
        blob_storage_service: IBlobStorageService,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo
        self.bot_repo = bot_repo
        self.document_repo = document_repo
        self.document_folder_repo = document_folder_repo
        self.cognitive_search_service = cognitive_search_service
        self.blob_storage_service = blob_storage_service
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service

    def _get_creator_name(
        self, user_map: dict[int, user_domain.User], creator_id: Optional[user_domain.Id]
    ) -> Optional[user_domain.Name]:
        if creator_id is None:
            return None
        creator = user_map.get(creator_id.value)
        if creator is None:
            return None
        return creator.name

    def _create_blob_sas_url(
        self,
        blob_container_renewal_flag: bool,
        container_name: storage_domain.ContainerName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.DisplayableBlobName,
    ):
        if document_folder_context.is_external:
            return self.blob_storage_service.create_external_blob_sas_url(
                container_name=container_name,
                bot_id=bot_id,
                document_id=document_id,
                document_folder_context=document_folder_context,
                blob_name=blob_name,
            )
        if blob_container_renewal_flag:
            return self.blob_storage_service.create_blob_sas_url_v2(
                container_name=container_name,
                bot_id=bot_id,
                document_folder_context=document_folder_context,
                blob_name=blob_name,
            )
        return self.blob_storage_service.create_blob_sas_url(
            container_name=container_name, document_folder_context=document_folder_context, blob_name=blob_name
        )

    def create_documents(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        input: CreateDocumentsInput,
    ):
        FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag(FLAG_KEY, tenant.id, tenant.name, default=True)

        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ファイルのアップロードがサポートされていません")
        if bot.container_name is None:
            raise Exception("container_name is not set")

        if flag:
            container_name = tenant.container_name
        else:
            container_name = bot.container_name

        uploaded_documents: list[document_domain.Document] = []
        document_upload_error: Optional[DocumentUploadError] = None

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)

        if input.parent_document_folder_id is None:
            parent_document_folder_id = root_document_folder.id
        else:
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(
                input.parent_document_folder_id, bot_id
            )
            parent_document_folder_id = parent_document_folder.id

        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=parent_document_folder_id, is_root=parent_document_folder_id == root_document_folder.id
        )

        for document_for_create in input.documents_for_create:
            try:
                # フォルダ内の既存のドキュメントと重複していないか確認
                try:
                    existing_document = self.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name(
                        bot_id, parent_document_folder_id, document_for_create.name
                    )
                except NotFound:
                    existing_document = None
                if existing_document is not None:
                    document_upload_error = {
                        "type": "document_exists",
                        "message": f"{document_for_create.name.value} は既に存在しています。",
                        "document_id": None,
                    }
                    break
            except Exception as e:
                document_upload_error = {
                    "type": "get_document_error",
                    "message": f"Failed to get document {document_for_create.name.value}: {e!s}",
                    "document_id": None,
                }
                break

            try:
                # ドキュメントをDBに保存
                saved_document = self.document_repo.create(
                    bot_id=bot_id,
                    parent_document_folder_id=parent_document_folder_id,
                    document=document_for_create,
                )
            except Exception as e:
                document_upload_error = {
                    "type": "create_document_error",
                    "message": f"Failed to create document {document_for_create.name.value}: {e!s}",
                    "document_id": None,
                }
                break

            try:
                # ドキュメントをBlobストレージにアップロード
                if flag:
                    self.blob_storage_service.upload_blob_v2(
                        container_name=container_name,
                        bot_id=bot_id,
                        document_folder_context=document_folder_context,
                        document_for_create=document_for_create,
                    )
                else:
                    self.blob_storage_service.upload_blob(
                        container_name=container_name,
                        document_folder_context=document_folder_context,
                        document_for_create=document_for_create,
                    )

            except Exception as e:
                document_upload_error = {
                    "type": "upload_document_error",
                    "message": f"Failed to upload document {document_for_create.name.value}: {e!s}",
                    "document_id": saved_document.id,
                }
                break

            uploaded_documents.append(saved_document)

        if document_upload_error is not None:
            # 何らかのエラーが発生した場合は、アップロードされたドキュメントを削除
            for document in uploaded_documents:
                self.document_repo.delete(document.id)
                if flag:
                    self.blob_storage_service.delete_document_blob_v2(
                        container_name=container_name,
                        bot_id=bot_id,
                        document_folder_context=document_folder_context,
                        blob_name=document.blob_name_v2,
                    )
                    if document.file_extension != document_domain.FileExtension.PDF:
                        try:
                            self.blob_storage_service.delete_document_blob_v2(
                                container_name=container_name,
                                bot_id=bot_id,
                                document_folder_context=document_folder_context,
                                blob_name=document.pdf_blob_name_v2,
                            )
                        except NotFound:
                            self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

                else:
                    self.blob_storage_service.delete_document_blob(
                        container_name=container_name,
                        document_folder_context=document_folder_context,
                        blob_name=document.blob_name,
                    )
                    if document.file_extension != document_domain.FileExtension.PDF:
                        try:
                            self.blob_storage_service.delete_document_blob(
                                container_name=container_name,
                                document_folder_context=document_folder_context,
                                blob_name=document.pdf_blob_name,
                            )
                        except NotFound:
                            self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

            # ドキュメントが既に存在する場合は、BadRequestを返す
            if document_upload_error["type"] == "document_exists":
                raise BadRequest(document_upload_error["message"])
            if (
                document_upload_error["type"] == "upload_document_error"
                and document_upload_error["document_id"] is not None
            ):
                self.document_repo.delete(document_upload_error["document_id"])
            raise Exception(document_upload_error["message"])

        # すべてのファイルがアップロードされた後にキューにメッセージを送信
        document_ids_to_process: list[document_domain.Id] = []
        document_ids_to_convert: list[document_domain.Id] = []
        for document in uploaded_documents:
            if document.file_extension.is_indexing_supported():
                document_ids_to_process.append(document.id)
            if document.file_extension.is_convertible_to_pdf():
                document_ids_to_convert.append(document.id)
        if len(document_ids_to_process) > 0:
            self.queue_storage_service.send_messages_to_documents_process_queue(
                tenant.id, bot_id, document_ids_to_process
            )
        if len(document_ids_to_convert) > 0:
            self.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue(
                tenant.id, bot_id, document_ids_to_convert
            )

    def get_documents(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id | None,
    ) -> GetDocumentsOutput:
        users = self.user_repo.find_by_tenant_id(tenant_id)
        user_map = {user.id.value: user for user in users}

        bot = self.bot_repo.find_by_id(bot_id)
        if bot is None:
            raise NotFound(f"アシスタントが見つかりませんでした。 bot_id: {bot_id}")
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            return GetDocumentsOutput(documents=[])

        if parent_document_folder_id is not None:
            # 親フォルダのbot_idが一致するかチェック
            parent_document_folder = self.document_folder_repo.find_by_id_and_bot_id(parent_document_folder_id, bot_id)
        else:
            # 親フォルダが指定されていない場合は、ルートフォルダを取得
            parent_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)

        documents = self.document_repo.find_by_bot_id_and_parent_document_folder_id(
            bot_id,
            parent_document_folder.id,
        )

        documents_with_creator: list[DocumentWithCreator] = []
        for document in documents:
            creator_name = self._get_creator_name(user_map, document.creator_id)
            documents_with_creator.append(
                DocumentWithCreator(
                    id=document.id,
                    name=document.name,
                    memo=document.memo,
                    file_extension=document.file_extension,
                    status=document.status,
                    storage_usage=document.storage_usage,
                    created_at=document.created_at,
                    creator_id=document.creator_id,
                    creator_name=creator_name,
                    document_folder_id=document.document_folder_id,
                )
            )

        return GetDocumentsOutput(documents=documents_with_creator)

    def get_all_documents(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> GetDocumentsOutput:
        users = self.user_repo.find_by_tenant_id(tenant_id)
        user_map = {user.id.value: user for user in users}

        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            return GetDocumentsOutput(documents=[])

        documents = self.document_repo.find_by_bot_id(bot_id)

        documents_with_creator: list[DocumentWithCreator] = []
        for document in documents:
            creator_name = self._get_creator_name(user_map, document.creator_id)
            documents_with_creator.append(
                DocumentWithCreator(
                    id=document.id,
                    name=document.name,
                    memo=document.memo,
                    file_extension=document.file_extension,
                    status=document.status,
                    storage_usage=document.storage_usage,
                    created_at=document.created_at,
                    creator_id=document.creator_id,
                    creator_name=creator_name,
                    document_folder_id=document.document_folder_id,
                )
            )

        return GetDocumentsOutput(documents=documents_with_creator)

    def get_document_detail(
        self, tenant: tenant_domain.Tenant, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> GetDocumentDetailOutput:
        FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag(FLAG_KEY, tenant.id, tenant.name, default=True)

        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ドキュメントのダウンロードがサポートされていません。")
        container_name = tenant.container_name if flag else bot.container_name
        if container_name is None:
            raise Exception("container_name is not set")

        document = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)

        # creator_name の取得
        if document.creator_id is None:
            creator_name = None
        else:
            creator = self.user_repo.find_by_id_and_tenant_id(document.creator_id, tenant.id, include_deleted=True)
            creator_name = creator.name

        # signed_urlの取得
        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=document.document_folder_id,
            is_root=document.document_folder_id == root_document_folder.id,
            is_external=document.external_id is not None,
        )

        if document_folder_context.is_root:
            document_folder = document_folder_domain.DocumentFolderWithAncestors(
                id=root_document_folder.id,
                name=root_document_folder.name,
                created_at=root_document_folder.created_at,
                ancestor_folders=[],
            )
        else:
            document_folder = self.document_folder_repo.find_with_ancestors_by_id_and_bot_id(
                id=document.document_folder_id, bot_id=bot_id
            )

        displayable_blob_name = document.name.to_displayable_blob_name(document.file_extension)
        signed_url_original = self._create_blob_sas_url(
            flag, container_name, bot_id, document.id, document_folder_context, displayable_blob_name
        )

        external_url = None
        if document.external_id is not None and document_folder.external_type is not None:
            external_data_connection = self.tenant_repo.get_external_data_connection_by_tenant_id_and_type(
                tenant.id, document_folder.external_type
            )
            decrypted_credentials = external_data_connection_domain.DecryptedCredentials.from_encrypted_credentials(
                external_data_connection.encrypted_credentials, external_data_connection.external_data_connection_type
            )
            match document_folder.external_type:
                case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                    external_id = external_data_connection_domain.SharepointExternalId.from_external_id(
                        document.external_id
                    )
                    external_url = asyncio.run(
                        self.msgraph_service.get_external_document_url(
                            decrypted_credentials.to_sharepoint_credentials(), external_id
                        )
                    )
                case _:
                    raise BadRequest("未対応の外部データ連携です。")

        if not document.file_extension.is_convertible_to_pdf():
            return GetDocumentDetailOutput(
                id=document.id,
                name=document.name,
                memo=document.memo,
                file_extension=document.file_extension,
                status=document.status,
                storage_usage=document.storage_usage,
                created_at=document.created_at,
                creator_id=document.creator_id,
                creator_name=creator_name,
                signed_url_original=signed_url_original,
                signed_url_pdf=None,
                external_url=external_url,
                document_folder_id=document.document_folder_id,
                document_folder_name=document_folder.name,
                document_folder_created_at=document_folder.created_at,
                document_folder_ancestor_folders=document_folder.without_root_folder().ancestor_folders,
            )

        displayable_pdf_blob_name = document.name.to_displayable_blob_name(document_domain.FileExtension.PDF)

        signed_url_pdf = None
        try:
            signed_url_pdf = self._create_blob_sas_url(
                flag, container_name, bot_id, document.id, document_folder_context, displayable_pdf_blob_name
            )
        except NotFound:
            self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

        return GetDocumentDetailOutput(
            id=document.id,
            name=document.name,
            memo=document.memo,
            file_extension=document.file_extension,
            status=document.status,
            storage_usage=document.storage_usage,
            created_at=document.created_at,
            creator_id=document.creator_id,
            creator_name=creator_name,
            signed_url_original=signed_url_original,
            signed_url_pdf=signed_url_pdf,
            external_url=external_url,
            document_folder_id=document.document_folder_id,
            document_folder_name=document_folder.name,
            document_folder_created_at=document_folder.created_at,
            document_folder_ancestor_folders=document_folder.without_root_folder().ancestor_folders,
        )

    def delete_document(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
    ) -> None:
        FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag(FLAG_KEY, tenant.id, tenant.name, default=True)

        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ドキュメントの削除がサポートされていません。")

        document = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)
        if document.status == document_domain.Status.PENDING:
            raise BadRequest("処理中のドキュメントは削除できません。")
        if document.status == document_domain.Status.DELETING:
            raise BadRequest("削除中のドキュメントは削除できません。")

        search_service_endpoint = (
            tenant.search_service_endpoint
            if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
            else bot.search_service_endpoint
        )
        if search_service_endpoint is None:
            raise Exception("search_service_endpoint is not set")

        index_name = (
            tenant.index_name
            if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
            else bot.index_name
        )
        if index_name is None:
            raise Exception("index_name is not set")

        container_name = tenant.container_name if flag else bot.container_name
        if container_name is None:
            raise Exception("container_name is not set")

        self.cognitive_search_service.delete_documents_from_index_by_document_id(
            endpoint=search_service_endpoint,
            index_name=index_name,
            document_id=document_id,
        )

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=document.document_folder_id, is_root=document.document_folder_id == root_document_folder.id
        )

        if flag:
            self.blob_storage_service.delete_document_blob_v2(
                container_name=container_name,
                bot_id=bot_id,
                document_folder_context=document_folder_context,
                blob_name=document.blob_name_v2,
            )
            if document.file_extension.is_convertible_to_pdf():
                try:
                    self.blob_storage_service.delete_document_blob_v2(
                        container_name=container_name,
                        bot_id=bot_id,
                        document_folder_context=document_folder_context,
                        blob_name=document.pdf_blob_name_v2,
                    )
                except NotFound:
                    self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

        else:
            self.blob_storage_service.delete_document_blob(
                container_name=container_name,
                document_folder_context=document_folder_context,
                blob_name=document.blob_name,
            )
            if document.file_extension.is_convertible_to_pdf():
                try:
                    self.blob_storage_service.delete_document_blob(
                        container_name=container_name,
                        document_folder_context=document_folder_context,
                        blob_name=document.pdf_blob_name,
                    )
                except NotFound:
                    self.logger.warning("拡張子が.pdfのファイルが見つかりませんでした。")

        # DBのドキュメントの削除
        self.document_repo.delete(document_id)

    def update_document(
        self, bot_id: bot_domain.Id, document_id: document_domain.Id, document: document_domain.DocumentForUpdate
    ) -> None:
        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ドキュメントの編集がサポートされていません。")

        current = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)

        current.update(document)

        self.document_repo.update(current)

    def update_document_v2(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document: document_domain.DocumentForUpdate,
    ) -> None:
        current = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)

        if current.status == document_domain.Status.PENDING:
            raise BadRequest("処理中のドキュメントは編集できません。")

        # validate name
        old_name = current.name
        new_name = document.basename if document.basename is not None else old_name
        is_basename_updated = old_name.value != new_name.value
        if is_basename_updated:
            try:
                self.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name(
                    bot_id=bot_id, parent_document_folder_id=current.document_folder_id, name=new_name
                )
                raise BadRequest("ファイル名が重複しています。")
            except NotFound:
                current.update_status_to_pending()

        # ursaの場合はファイル名とメモが連動している必要があるためメモをアップデート
        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach == bot_domain.Approach.URSA and current.memo:
            delimiter = "\\" if "\\" in current.memo.value else "/"
            current_memo_list = current.memo.value.split(delimiter)
            new_memo_list = current_memo_list[:-1]
            new_memo_list.append(current_memo_list[-1].replace(old_name.value, new_name.value))
            new_memo = delimiter.join(new_memo_list)
            document.update_memo(Memo(value=new_memo))

        current.update(document)

        self.document_repo.update(current)

        if not is_basename_updated:
            return

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        document_folder_context = document_folder_domain.DocumentFolderContext(
            id=current.document_folder_id,
            is_root=current.document_folder_id == root_document_folder.id,
        )
        self.blob_storage_service.update_document_blob_name(
            container_name=tenant.container_name,
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            old_blob_name=old_name.to_displayable_blob_name(current.file_extension),
            new_blob_name=new_name.to_displayable_blob_name(current.file_extension),
        )

        # AI Search のフィールドを変更するために、Jobで処理を続ける
        self.queue_storage_service.send_message_to_sync_document_name_queue(tenant.id, bot_id, document_id)

    def add_chunks(
        self, bot_id: bot_domain.Id, document_id: document_domain.Id, chunks: document_domain.ChunksForCreate
    ) -> None:
        bot = self.bot_repo.find_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ドキュメントの編集がサポートされていません。")
        if bot.index_name is None:
            raise Exception("index_name is not set")

        document = self.document_repo.find_by_id_and_bot_id(id=document_id, bot_id=bot_id)

        if document.status == document_domain.Status.COMPLETED:
            raise BadRequest("このドキュメントはすでに反映済みになっています。")

        if bot.search_service_endpoint is None:
            raise BadRequest("エンドポイントが設定されていません。")
        self.cognitive_search_service.add_chunks_to_index(
            endpoint=bot.search_service_endpoint,
            index_name=bot.index_name,
            chunks=chunks,
        )

        document.update_status_to_completed()

        self.document_repo.update(document)

    def delete_documents(self, bot_id: bot_domain.Id, document_ids: list[document_domain.Id]) -> None:
        bot = self.bot_repo.find_with_tenant_by_id(bot_id)
        if bot.approach.value == bot_domain.Approach.CHAT_GPT_DEFAULT.value:
            raise BadRequest("ドキュメントの削除がサポートされていません。")

        # ドキュメントの存在確認
        documents = self.document_repo.find_by_ids_and_bot_id(bot_id, document_ids)

        if any(document.status == document_domain.Status.PENDING for document in documents):
            raise BadRequest("処理中のドキュメントは削除できません。")
        if any(document.status == document_domain.Status.DELETING for document in documents):
            raise BadRequest("削除中のドキュメントは削除できません。")

        if len(documents) == 0:
            raise NotFound("ドキュメントが見つかりません。")

        # DBのドキュメントのステータスを削除中に更新
        for document in documents:
            document.update_status_to_deleting()
            self.document_repo.update(document)

        # ここで queue にメッセージを送信する（各データの削除はfunction内で実行）
        self.queue_storage_service.send_message_to_delete_multiple_documents_queue(
            bot.tenant.id, bot_id, [document.id for document in documents]
        )

    def create_or_update_document_feedback(self, input: CreateOrUpdateDocumentFeedbackInput) -> None:
        # Make sure the document belongs to the bot
        self.document_repo.find_by_id_and_bot_id(input.document_id, input.bot_id)

        new_document_feedback = document_feedback_domain.DocumentFeedback(
            user_id=input.user_id,
            document_id=input.document_id,
            evaluation=input.evaluation,
        )

        try:
            existing_document_feedback = self.document_repo.find_feedback_by_id_and_user_id(
                input.document_id, input.user_id
            )
        except NotFound:
            existing_document_feedback = None

        if existing_document_feedback is None:
            self.document_repo.create_feedback(new_document_feedback)
        else:
            self.document_repo.update_feedback(new_document_feedback)

    def move_document(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        new_document_folder_id: document_folder_domain.Id,
    ) -> None:
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant.id)

        document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)
        if document.status != document_domain.Status.COMPLETED:
            raise BadRequest("反映済みのドキュメントのみ移動できます。")

        old_document_folder = self.document_folder_repo.find_by_id_and_bot_id(document.document_folder_id, bot_id)
        new_document_folder = self.document_folder_repo.find_by_id_and_bot_id(new_document_folder_id, bot_id)
        if old_document_folder.id == new_document_folder.id:
            raise BadRequest("移動先が同じフォルダです。")

        # 移動先に同じ名前のファイルがあるか確認
        try:
            self.document_repo.find_by_bot_id_and_parent_document_folder_id_and_name(
                bot_id, new_document_folder.id, document.name
            )
            raise BadRequest("移動先に同じ名前のファイルがあります。")
        except NotFound:
            pass

        root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)

        # blobのドキュメントのパスを変更する
        self.blob_storage_service.update_document_folder_path(
            container_name=tenant.container_name,
            bot_id=bot.id,
            old_document_folder_context=document_folder_domain.DocumentFolderContext(
                id=old_document_folder.id, is_root=old_document_folder.id == root_document_folder.id
            ),
            new_document_folder_context=document_folder_domain.DocumentFolderContext(
                id=new_document_folder.id, is_root=new_document_folder.id == root_document_folder.id
            ),
            blob_name=document.name.to_displayable_blob_name(document.file_extension),
        )

        # 属するdocument_folderを更新
        document.update_document_folder_id(new_document_folder.id)
        document.update_status_to_pending()
        self.document_repo.update(document)
        # queueにメッセージを送る
        self.queue_storage_service.send_message_to_sync_document_location_queue(tenant.id, bot_id, document_id)
