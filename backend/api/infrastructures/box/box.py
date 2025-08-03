from box_sdk_gen import (
    BoxAPIError,
    BoxCCGAuth,
    BoxClient,
    CCGConfig,
    FileFull as BaseFileFull,
    FolderMini,
    Items,
)
from pydantic_core import Url

from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.document_folder import (
    document_folder as document_folder_domain,
    external_data_connection as external_document_folder_domain,
)
from api.domain.models.tenant import external_data_connection as external_data_connection_domain
from api.domain.services.box.box import IBoxService
from api.libs.exceptions import BadRequest, NotFound
from api.libs.logging import get_logger

from .models.file_full import FileFull
from .models.folder_full import FolderFull


class BoxService(IBoxService):
    def __init__(self):
        self.logger = get_logger()

    # https://ja.developer.box.com/guides/api-calls/permissions-and-errors/common-errors/
    def _handle_box_api_error(self, e: BoxAPIError):
        if e.response_info.status_code == 400:
            raise BadRequest("Box認証情報が無効です。")
        if e.response_info.status_code == 404:
            raise NotFound("指定したアイテムが見つかりません。")
        raise e

    def _get_client(self, credentials: external_data_connection_domain.BoxDecryptedCredentials) -> BoxClient:
        ccg_config = CCGConfig(
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            enterprise_id=credentials.enterprise_id,
        )
        ccg_auth = BoxCCGAuth(ccg_config)
        return BoxClient(ccg_auth)

    def is_authorized_client(self, credentials: external_data_connection_domain.BoxDecryptedCredentials) -> bool:
        try:
            client = self._get_client(credentials)
            client.auth.retrieve_token()
            return True
        except Exception as e:
            self.logger.error("Boxの認証に失敗しました", exc_info=e)
            return False

    def get_external_document_folder_to_sync(
        self, credentials: external_data_connection_domain.BoxDecryptedCredentials, shared_url: str
    ) -> document_folder_domain.ExternalDocumentFolderToSync:
        client = self._get_client(credentials)

        try:
            folder_full = client.shared_links_folders.find_folder_for_shared_link(f"shared_link={shared_url}")
        except BoxAPIError as e:
            self._handle_box_api_error(e)

        return FolderFull(folder_full).to_domain_to_sync()

    def get_document_folder_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_document_folder_domain.ExternalDocumentFolder:
        client = self._get_client(credentials)

        try:
            folder_full = client.folders.get_folder_by_id(external_id.id)
        except BoxAPIError as e:
            self._handle_box_api_error(e)

        return FolderFull(folder_full).to_document_folder_domain()

    def get_document_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_document_domain.ExternalDocument:
        client = self._get_client(credentials)

        try:
            file_full = client.files.get_file_by_id(external_id.id)
        except BoxAPIError as e:
            self._handle_box_api_error(e)

        return FileFull(file_full).to_external_document()

    def get_descendant_documents_by_id(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> list[external_document_domain.ExternalDocument]:
        client = self._get_client(credentials)

        external_folder_ids = [external_id.id]
        descendant_documents: list[external_document_domain.ExternalDocument] = []

        def _get_folder_items(self, client: BoxClient, folder_id: str, limit, marker: str | None) -> Items:
            return client.folders.get_folder_items(
                folder_id=folder_id,
                limit=limit,
                usemarker=True,
                marker=marker,
                # 指定しないと"modified_at"などが取得できない
                fields=["id", "name", "type", "modified_at", "path_collection"],
            )

        def _append_items(items: Items):
            if items.entries is None:
                raise BadRequest("Boxのフォルダ内のアイテムが取得できませんでした。")

            for item in items.entries:
                if isinstance(item, FolderMini):
                    external_folder_ids.append(item.id)
                elif isinstance(item, BaseFileFull):
                    try:
                        descendant_documents.append(FileFull(item).to_external_document())
                    except BadRequest:
                        # 無効な拡張子の場合を無視して続行
                        continue

        MAX_ITEM_COLLECTION_LIMIT = 1000
        while external_folder_ids:
            external_folder_id = external_folder_ids.pop()

            try:
                items = _get_folder_items(
                    self, client=client, folder_id=external_folder_id, limit=MAX_ITEM_COLLECTION_LIMIT, marker=None
                )
            except BoxAPIError as e:
                self._handle_box_api_error(e)
            _append_items(items)

            next_marker = items.next_marker
            while next_marker:
                try:
                    items = _get_folder_items(
                        self,
                        client=client,
                        folder_id=external_folder_id,
                        limit=MAX_ITEM_COLLECTION_LIMIT,
                        marker=next_marker,
                    )
                except BoxAPIError as e:
                    self._handle_box_api_error(e)
                _append_items(items)

                next_marker = items.next_marker

        return descendant_documents

    def download_document(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> bytes:
        client = self._get_client(credentials)

        try:
            byte_stream = client.downloads.download_file(external_id.id)
            if byte_stream is None:
                raise NotFound("指定したアイテムが見つかりません。")
            with byte_stream:
                data = byte_stream.read()
        except BoxAPIError as e:
            self._handle_box_api_error(e)

        return data

    def get_external_document_folder_url(
        self,
        credentials: external_data_connection_domain.BoxDecryptedCredentials,
        external_id: external_data_connection_domain.BoxExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        client = self._get_client(credentials)

        try:
            folder_full = client.shared_links_folders.get_shared_link_for_folder(external_id.id, "shared_link")
        except BoxAPIError as e:
            self._handle_box_api_error(e)

        if folder_full.shared_link is None:
            raise NotFound("共有リンクが見つかりません。")

        return external_data_connection_domain.ExternalUrl(root=Url(folder_full.shared_link.url))
