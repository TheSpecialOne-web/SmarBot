from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
import subprocess
from typing import Union
import urllib.parse
from uuid import uuid4

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobClient,
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    UserDelegationKey,
    generate_blob_sas,
)
from pydantic import BaseModel, ConfigDict
from tenacity import retry, stop_after_attempt, wait_exponential

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    bot_template as bot_template_domain,
    common_document_template as cdt_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    user as user_domain,
)
from api.domain.models.bot_template import Id as BotTemplateId
from api.domain.models.chat_completion_export import (
    BlobPath as ChatCompletionExportBlobPath,
    SignedUrl as ChatCompletionExportSignedUrl,
)
from api.domain.models.conversation_export import (
    BlobPath as ConversationExportBlobPath,
    SignedUrl as ConversationExportSignedUrl,
)
from api.domain.models.storage import ContainerName
from api.domain.models.tenant import Alias, LogoUrl
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.app_env import app_env
from api.libs.exceptions import Conflict, NotFound

# Azureの設定
AZURE_BLOB_STORAGE_ACCOUNT = os.environ.get("AZURE_BLOB_STORAGE_ACCOUNT") or ""
AZURE_BLOB_STORAGE_ACCOUNT_KEY = os.environ.get("AZURE_BLOB_STORAGE_ACCOUNT_KEY")
AZURE_FRONT_DOOR_BLOB_STORAGE_ENDPOINT = os.environ.get("AZURE_FRONT_DOOR_BLOB_STORAGE_ENDPOINT")

AZURE_PUBLIC_STORAGE_ACCOUNT = os.environ.get("AZURE_PUBLIC_STORAGE_ACCOUNT") or ""
AZURE_COMMON_CONTAINER_NAME = "common-container"
AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT = os.environ.get("AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT")

AZURE_BATCH_STORAGE_ACCOUNT = os.environ.get("AZURE_BATCH_STORAGE_ACCOUNT") or ""
FUNCTION_STORAGE_CONTAINER = os.environ.get("AZURE_BLOB_STORAGE_USERS_IMPORT_CONTAINER") or "users-import-container"

# Azuriteの設定
AZURITE_BLOB_CONNECTION_STRING = (
    os.environ.get("AZURITE_BLOB_CONNECTION_STRING")  # CI上では環境変数をセットする
    or "DefaultEndpointsProtocol=http;AccountName=stbloblocal;AccountKey=c3RibG9ibG9jYWw=;BlobEndpoint=http://azurite:10000/stbloblocal;"
)
AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING = (
    os.environ.get("AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING")  # CI上では環境変数をセットする
    or "DefaultEndpointsProtocol=http;AccountName=stpubliclocal;AccountKey=c3RwdWJsaWNsb2NhbGtleQ==;BlobEndpoint=http://azurite:10000/stpubliclocal;"
)
AZURITE_BATCH_STORAGE_BLOB_CONNECTION_STRING = (
    os.environ.get("AZURITE_BATCH_STORAGE_BLOB_CONNECTION_STRING")  # CI上では環境変数をセットする
    or "DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;BlobEndpoint=http://azurite:10000/stbatchlocal;"
)


class GenerateBlobSasParams(BaseModel):
    # pydanticでサポートされていない型を使うための設定
    model_config = ConfigDict(arbitrary_types_allowed=True)

    account_name: str
    container_name: str
    blob_name: str
    permission: BlobSasPermissions
    expiry: datetime
    content_type: str | None = None
    content_disposition: str | None = None
    account_key: str | None = None
    user_delegation_key: UserDelegationKey | None = None

    def set_account_key(self, account_key: str):
        self.account_key = account_key

    def set_user_delegation_key(self, user_delegation_key: UserDelegationKey):
        self.user_delegation_key = user_delegation_key


class BlobStorageService(IBlobStorageService):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.credential = azure_credential
        self.blob_service_client = (
            BlobServiceClient(
                account_url=f"https://{AZURE_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
                credential=azure_credential,
            )
            if not app_env.is_localhost()
            else BlobServiceClient.from_connection_string(AZURITE_BLOB_CONNECTION_STRING)
        )

        common_blob_service_client = (
            BlobServiceClient(
                account_url=f"https://{AZURE_PUBLIC_STORAGE_ACCOUNT}.blob.core.windows.net",
                credential=azure_credential,
            )
            if not app_env.is_localhost()
            else BlobServiceClient.from_connection_string(AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING)
        )
        self.common_blob_container_client = common_blob_service_client.get_container_client(
            AZURE_COMMON_CONTAINER_NAME
        )

        self.batch_blob_service_client = (
            BlobServiceClient(
                account_url=f"https://{AZURE_BATCH_STORAGE_ACCOUNT}.blob.core.windows.net",
                credential=azure_credential,
            )
            if not app_env.is_localhost()
            else BlobServiceClient.from_connection_string(AZURITE_BATCH_STORAGE_BLOB_CONNECTION_STRING)
        )

    def _get_blob_client_by_url(self, url: str):
        if not app_env.is_localhost():
            return BlobClient.from_blob_url(
                blob_url=url,
                credential=self.credential,
            )
        return BlobClient.from_connection_string(
            conn_str=AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING,
            container_name=url.split("/")[4],
            blob_name="/".join(url.split("/")[5:]),
        )

    def upload_blob(
        self,
        container_name: ContainerName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        document_for_create: document_domain.DocumentForCreate,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        blob_name = document_for_create.blob_name
        blob_path = self._create_blob_path(
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )
        with BytesIO(document_for_create.data) as bytes_stream:
            blob_container.upload_blob(
                blob_path,
                bytes_stream,
                overwrite=True,
            )

    def upload_blob_v2(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        document_for_create: document_domain.DocumentForCreate,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            blob_name=document_for_create.blob_name_v2,
            document_folder_context=document_folder_context,
        )
        with BytesIO(document_for_create.data) as bytes_stream:
            blob_container.upload_blob(
                blob_path,
                bytes_stream,
                overwrite=True,
            )

    def upload_external_blob(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_id: document_domain.Id,
        blob_name: document_domain.BlobName,
        data: bytes,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        blob_path = self._create_external_blob_path(
            bot_id=bot_id,
            document_folder_id=document_folder_id,
            document_id=document_id,
            blob_name=blob_name,
        )
        with BytesIO(data) as bytes_stream:
            blob_container.upload_blob(
                blob_path,
                bytes_stream,
                overwrite=True,
            )

    def upload_attachment(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
        attachment_for_create: attachment_domain.AttachmentForCreate,
    ):
        """
        与えられたアタッチメントをBlobストレージにアップロードします。

        :param container_name: アップロードするファイルのコンテナ名
        :type container_name: storage.ContainerName
        :param blob_name: アップロードするファイルの名前
        :type blob_name: document.BlobName
        :param data: アップロードするファイルのデータ
        :type data: bytes
        """
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        prefix = f"attachments/{bot_id.value}/"
        blob_name = prefix + attachment_for_create.blob_name.root
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        with BytesIO(attachment_for_create.data) as bytes_stream:
            blob_container.upload_blob(blob_name, bytes_stream, overwrite=True)

    def _generate_blob_sas_url(
        self,
        container_name: ContainerName,
        blob_path: str,
        content_type: str | None = None,
        content_disposition: str | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        sas_expiry = now + timedelta(hours=1)

        params = GenerateBlobSasParams(
            account_name=AZURE_BLOB_STORAGE_ACCOUNT,
            container_name=container_name.root,
            blob_name=blob_path,
            permission=BlobSasPermissions(read=True),
            expiry=sas_expiry,
            content_type=content_type,
            content_disposition=content_disposition,
        )

        if app_env.is_localhost():
            params.set_account_key(AZURE_BLOB_STORAGE_ACCOUNT_KEY or "")
        else:
            params.set_user_delegation_key(self.blob_service_client.get_user_delegation_key(now, sas_expiry))

        try:
            sas_blob = generate_blob_sas(**params.model_dump())
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")
        url = f"{AZURE_FRONT_DOOR_BLOB_STORAGE_ENDPOINT}/{container_name.root}/{urllib.parse.quote(blob_path)}?{sas_blob}"
        return url

    def create_blob_sas_url(
        self,
        container_name: ContainerName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        name: Union[
            document_domain.BlobName,
            document_domain.DisplayableBlobName,
        ],
    ) -> document_domain.SignedUrl:
        """
        与えられたファイルのSAS URLを作成します。

        :param container_name: ダウンロードするファイルのコンテナ名
        :type container_name: storage.ContainerName
        :param name: ダウンロードするファイルの名前
        :type name: document.BlobName or document.DisplayableBlobName
        :return: SAS URL
        :rtype: document.SignedUrl
        """

        blob_name = ""
        if isinstance(name, document_domain.BlobName):
            blob_name = name.value
        if isinstance(name, document_domain.DisplayableBlobName):
            blob_name = name.to_blob_name().value
        blob_path = self._create_blob_path(
            document_folder_context=document_folder_context,
            blob_name=document_domain.BlobName(value=blob_name),
        )
        content_type = name.file_extension().to_content_type()
        content_disposition = name.to_content_disposition()

        # ファイルがblob_containerに存在するかを確認
        if not self.blob_service_client.get_blob_client(container=container_name.root, blob=blob_path).exists():
            raise NotFound("ファイルが見つかりませんでした。")

        url = self._generate_blob_sas_url(container_name, blob_path, content_type, content_disposition)
        return document_domain.SignedUrl(value=url)

    def delete_blob_export(
        self,
        container_name: ContainerName,
        blob_path: Union[ConversationExportBlobPath, ChatCompletionExportBlobPath],
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        try:
            blob_container.delete_blob(blob_path.root)
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    def create_blob_chat_completion_sas_url(
        self,
        container_name: ContainerName,
        blob_path: ChatCompletionExportBlobPath,
    ) -> ChatCompletionExportSignedUrl:
        url = self._generate_blob_sas_url(container_name, blob_path.root, "application/csv")
        return ChatCompletionExportSignedUrl(root=url)

    def create_blob_conversation_sas_url(
        self,
        container_name: ContainerName,
        blob_path: ConversationExportBlobPath,
    ) -> ConversationExportSignedUrl:
        url = self._generate_blob_sas_url(container_name, blob_path.root, "application/csv")
        return ConversationExportSignedUrl(root=url)

    def create_blob_sas_url_v2(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.DisplayableBlobName,
    ) -> document_domain.SignedUrl:
        """
        与えられたファイルのSAS URLを作成します。

        :param container_name: ダウンロードするファイルのコンテナ名
        :type container_name: storage.ContainerName
        :param name: ダウンロードするファイルの名前
        :type name: document.DisplayableBlobName
        :return: SAS URL
        :rtype: document.SignedUrl
        """
        blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=blob_name.to_blob_name_v2(),
        )
        content_type = blob_name.file_extension().to_content_type()
        content_disposition = blob_name.to_content_disposition()

        # ファイルがblob_containerに存在するかを確認
        if not self.blob_service_client.get_blob_client(container=container_name.root, blob=blob_path).exists():
            raise NotFound("ファイルが見つかりませんでした。")

        url = self._generate_blob_sas_url(container_name, blob_path, content_type, content_disposition)
        return document_domain.SignedUrl(value=url)

    def create_attachment_blob_sas_url(
        self, container_name: ContainerName, bot_id: bot_domain.Id, blob_name: attachment_domain.BlobName
    ) -> attachment_domain.SignedUrl:
        container_client = self.blob_service_client.get_container_client(container_name.root)
        prefix = f"attachments/{bot_id.value}/"
        content_type = blob_name.file_extension().to_content_type()
        content_disposition = blob_name.to_content_disposition()

        # ファイルがblob_containerに存在するかを確認
        if not container_client.get_blob_client(prefix + blob_name.root).exists():
            raise NotFound("ファイルが見つかりませんでした。")

        url = self._generate_blob_sas_url(container_name, prefix + blob_name.root, content_type, content_disposition)
        return attachment_domain.SignedUrl(root=url)

    def create_external_blob_sas_url(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_id: document_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.DisplayableBlobName,
    ) -> document_domain.SignedUrl:
        blob_path = self._create_external_blob_path(
            bot_id=bot_id,
            document_folder_id=document_folder_context.id,
            document_id=document_id,
            blob_name=blob_name,
        )
        content_type = blob_name.file_extension().to_content_type()
        content_disposition = blob_name.to_content_disposition()

        if not self.blob_service_client.get_blob_client(container=container_name.root, blob=blob_path).exists():
            raise NotFound("ファイルが見つかりませんでした。")

        url = self._generate_blob_sas_url(container_name, blob_path, content_type, content_disposition)
        return document_domain.SignedUrl(value=url)

    def update_document_blob_name(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        old_blob_name: document_domain.BlobName,
        new_blob_name: document_domain.BlobName,
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        old_blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=old_blob_name,
        )
        old_blob = blob_container.get_blob_client(old_blob_path)
        if not old_blob.exists():
            raise NotFound("ファイルが見つかりませんでした。")

        new_blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=new_blob_name,
        )
        new_blob = blob_container.get_blob_client(new_blob_path)
        if new_blob.exists():
            raise Conflict("ファイルが既に存在します。")

        # blobファイルの移動
        new_blob.start_copy_from_url(old_blob.url)

        # 古いblobファイルの削除
        old_blob.delete_blob()

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_document_blob(
        self,
        container_name: ContainerName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        # blobファイルの削除
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        try:
            blob_path = self._create_blob_path(
                document_folder_context=document_folder_context,
                blob_name=blob_name,
            )
            blob_container.delete_blob(blob_path)
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_document_blob_v2(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )
        try:
            blob_container.delete_blob(blob_path)
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def delete_document_blobs_by_document_folder_id(
        self, container_name: ContainerName, bot_id: bot_domain.Id, document_folder_id: document_folder_domain.Id
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        try:
            prefix = f"{bot_id}/{document_folder_id}/"

            blobs_to_delete = blob_container.list_blobs(name_starts_with=prefix)

            # 一致したBlobを削除
            for blob in blobs_to_delete:
                blob_container.delete_blob(blob)

        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    def delete_attachment_blob(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        blob_name: attachment_domain.BlobName,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        prefix = f"attachments/{bot_id.value}/"
        blob_name_to_delete = prefix + blob_name.root
        try:
            blob_container.delete_blob(blob_name_to_delete)
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    def create_blob_container(self, container_name: ContainerName):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if blob_container.exists():
            raise Conflict(f"コンテナ {container_name.root} が既に存在します。")
        blob_container.create_container()

    def get_attachment_blob_content(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        blob_name: attachment_domain.BlobName,
    ) -> attachment_domain.BlobContent:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        prefix = f"attachments/{bot_id.value}/"

        try:
            with BytesIO() as bytes_stream:
                blob_container.get_blob_client(prefix + blob_name.root).download_blob().readinto(bytes_stream)
                bytes_stream.seek(0)
                return attachment_domain.BlobContent(root=bytes_stream.getvalue())
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    def upload_users_import_csv(self, file: bytes, filename: str):
        blob_container = self.batch_blob_service_client.get_container_client(FUNCTION_STORAGE_CONTAINER)
        if not blob_container.exists():
            blob_container.create_container()
        with BytesIO(file) as bytes_stream:
            blob_container.upload_blob(filename, bytes_stream, overwrite=True)

    def delete_blob_container(self, container_name: ContainerName) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        blob_container.delete_container()

    def upload_image_to_common_container(self, file_name: str, file_content: bytes) -> LogoUrl:
        blob_container = self.common_blob_container_client
        if not blob_container.exists():
            raise Exception("blob container not found.")
        with BytesIO(file_content) as bytes_stream:
            uploaded_blob = blob_container.upload_blob(file_name, bytes_stream, overwrite=False)
            return LogoUrl(root=str(uploaded_blob.url))

    def delete_blobs_by_bot_id(self, container_name: ContainerName, bot_id: bot_domain.Id):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        prefix = str(bot_id.value) + "/"
        blobs = blob_container.list_blobs(name_starts_with=prefix)

        for blob in blobs:
            blob_container.delete_blob(blob)

    def _create_url_from_blob_client(self, blob_client: BlobClient) -> str:
        url = str(blob_client.url)
        if url.startswith("http://azurite"):
            url = url.replace("http://azurite", "http://localhost")
        return url

    def upload_bot_icon(self, file_path: str, file_content: bytes) -> bot_domain.IconUrl:
        blob_container = self.common_blob_container_client
        if not blob_container.exists():
            raise Exception("blob container not found.")
        with BytesIO(file_content) as bytes_stream:
            uploaded_blob = blob_container.upload_blob(file_path, bytes_stream, overwrite=False)
            return bot_domain.IconUrl(root=self._create_url_from_blob_client(uploaded_blob))

    def delete_bot_icon(self, alias: Alias, icon_url: bot_domain.IconUrl) -> None:
        blob_client = self._get_blob_client_by_url(icon_url.root)

        # 変なURLじゃないかチェックする
        if blob_client.account_name != AZURE_PUBLIC_STORAGE_ACCOUNT:
            raise NotFound("ファイルが見つかりませんでした。")
        if blob_client.container_name != AZURE_COMMON_CONTAINER_NAME:
            raise NotFound("ファイルが見つかりませんでした。")
        if blob_client.blob_name.split("/")[0] != alias.root:
            raise NotFound("ファイルが見つかりませんでした。")

        if not blob_client.exists():
            raise NotFound("ファイルが見つかりませんでした。")
        blob_client.delete_blob()

    def _get_file_extension_from_bot_template_icon_url(self, icon_url: bot_template_domain.IconUrl) -> str:
        return os.path.splitext(icon_url.root)[1][1:]

    def copy_icon_from_template(
        self, alias: Alias, template_icon_url: bot_template_domain.IconUrl
    ) -> bot_domain.IconUrl:
        # 共通のblobコンテナを取得
        common_blob_container = self.common_blob_container_client
        if not common_blob_container.exists():
            raise NotFound("共通のblobコンテナが見つかりません")

        # コピー元のblobを取得
        source_blob = self._get_blob_client_by_url(template_icon_url.root)
        if not source_blob.exists():
            raise NotFound("共通コンテナ内にソースblobが見つかりません")

        # コピー先のblobパスを構築
        destination_blob_path = (
            f"{alias.root}/{uuid4()}.{self._get_file_extension_from_bot_template_icon_url(template_icon_url)}"
        )
        destination_blob = common_blob_container.get_blob_client(destination_blob_path)

        # コピー元からコピー先へblobをコピー
        destination_blob.start_copy_from_url(source_blob.url)

        # コピーが完了したblobのURLを取得
        return bot_domain.IconUrl(root=self._create_url_from_blob_client(destination_blob))

    def upload_bot_template_icon(self, file_path: str, file_content: bytes) -> bot_template_domain.IconUrl:
        blob_container = self.common_blob_container_client
        if not blob_container.exists():
            raise Exception("blob container not found.")
        with BytesIO(file_content) as bytes_stream:
            uploaded_blob = blob_container.upload_blob(file_path, bytes_stream, overwrite=False)
            return bot_template_domain.IconUrl(root=self._create_url_from_blob_client(uploaded_blob))

    def delete_bot_template_icon(self, bot_template_id: BotTemplateId, icon_url: bot_template_domain.IconUrl) -> None:
        blob_client = self._get_blob_client_by_url(icon_url.root)

        # 変なURLじゃないかチェックする
        if blob_client.account_name != AZURE_PUBLIC_STORAGE_ACCOUNT:
            raise NotFound("ファイルが見つかりませんでした。")
        if blob_client.container_name != AZURE_COMMON_CONTAINER_NAME:
            raise NotFound("ファイルが見つかりませんでした。")
        if blob_client.blob_name.split("/")[1] != str(bot_template_id.root):
            raise NotFound("ファイルが見つかりませんでした。")

        if not blob_client.exists():
            raise NotFound("ファイルが見つかりませんでした。")
        blob_client.delete_blob()

    def _get_bot_templates_blob_name(self, bot_template_id: BotTemplateId, blob_name: cdt_domain.BlobName) -> str:
        return f"bot-templates/{bot_template_id.root}/documents/{blob_name.root}"

    def upload_common_document_template_to_common_container(
        self,
        bot_template_id: BotTemplateId,
        common_document_template: cdt_domain.CommonDocumentTemplateForCreate,
    ) -> None:
        blob_container = self.common_blob_container_client
        if not blob_container.exists():
            raise NotFound("blob container not found")

        upload_blob_name = self._get_bot_templates_blob_name(bot_template_id, common_document_template.blob_name)
        content_type = common_document_template.file_extension.to_content_type()
        content_settings = ContentSettings(
            content_type=content_type,
        )

        with BytesIO(common_document_template.data) as bytes_stream:
            blob_container.upload_blob(
                upload_blob_name,
                bytes_stream,
                content_settings=content_settings,
                overwrite=False,
            )

    def delete_common_document_template_from_common_container(
        self,
        bot_template_id: BotTemplateId,
        blob_name: cdt_domain.BlobName,
    ) -> None:
        blob_container = self.common_blob_container_client
        if not blob_container.exists():
            raise NotFound("blob container not found")
        blob_name_to_delete = self._get_bot_templates_blob_name(bot_template_id, blob_name)
        blob_container.delete_blob(blob_name_to_delete)

    def copy_blob_from_common_container_to_bot_container(
        self,
        bot_id: bot_domain.Id,
        bot_template_id: BotTemplateId,
        blob_name: cdt_domain.BlobName,
        container_name: ContainerName,
    ) -> None:
        # 共通のblobコンテナを取得
        common_blob_container = self.common_blob_container_client
        if not common_blob_container.exists():
            raise Exception("common blob container not found")

        # コピー元のblobを取得
        source_blob_path = self._get_bot_templates_blob_name(bot_template_id, blob_name)
        source_blob = common_blob_container.get_blob_client(source_blob_path)
        if not source_blob.exists():
            raise NotFound("共通コンテナ内にソースblobが見つかりません")

        # ボットのblobコンテナを取得
        bot_blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not bot_blob_container.exists():
            raise Exception("bot blob container not found")

        # コピー先のblobパスを構築
        destination_blob_path = f"{bot_id.value}/{blob_name.root}"
        destination_blob = bot_blob_container.get_blob_client(destination_blob_path)

        # コピー元からコピー先へblobをコピー
        destination_blob.start_copy_from_url(source_blob.url)

    def create_common_document_template_url(
        self, bot_template_id: BotTemplateId, blob_name: cdt_domain.BlobName
    ) -> cdt_domain.Url:
        return cdt_domain.Url(
            root=f"{AZURE_FRONT_DOOR_PUBLIC_STORAGE_ENDPOINT}/{AZURE_COMMON_CONTAINER_NAME}/{self._get_bot_templates_blob_name(bot_template_id, blob_name)}"
        )

    def get_csv_from_blob_storage(
        self,
        container_name: ContainerName,
        blob_name: document_domain.BlobName,
    ) -> bytes:
        blob_container = self.batch_blob_service_client.get_container_client(container_name.root)

        try:
            with BytesIO() as bytes_stream:
                blob_container.get_blob_client(blob_name.value).download_blob().readinto(bytes_stream)
                bytes_stream.seek(0)
                return bytes_stream.getvalue()
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりませんでした。")

    def upload_conversation_export_csv(
        self,
        container_name: ContainerName,
        blob_path: ConversationExportBlobPath,
        csv: bytes,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        with BytesIO(csv) as bytes_stream:
            blob_container.upload_blob(blob_path.root, bytes_stream, overwrite=True)

    def upload_chat_completion_export_csv(
        self,
        container_name: ContainerName,
        blob_path: ChatCompletionExportBlobPath,
        csv: bytes,
    ):
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        with BytesIO(csv) as bytes_stream:
            blob_container.upload_blob(blob_path.root, bytes_stream, overwrite=True)

    def upload_guideline(
        self,
        container_name: ContainerName,
        blob_path: str,
        file_content: bytes,
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        with BytesIO(file_content) as bytes_stream:
            blob_container.upload_blob(blob_path, bytes_stream, overwrite=False)

    def delete_guideline(
        self,
        container_name: ContainerName,
        blob_path: str,
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        try:
            blob_container.delete_blob(blob_path)
        except ResourceNotFoundError:
            raise NotFound("ファイルが見つかりません")

    def create_guideline_sas_url(
        self,
        container_name: ContainerName,
        blob_path: str,
    ) -> str:
        return self._generate_blob_sas_url(
            container_name=container_name, blob_path=blob_path, content_type="application/pdf"
        )

    def _create_blob_path(
        self,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ) -> str:
        blob_path = (
            f"{document_folder_context.id.root}/{blob_name.value}"
            if not document_folder_context.is_root
            else blob_name.value
        )
        return self._sanitize_blob_path(blob_path)

    def _create_blob_path_v2(
        self,
        bot_id: bot_domain.Id,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ) -> str:
        blob_path = (
            f"{bot_id.value}/{document_folder_context.id.root}/{blob_name.value}"
            if not document_folder_context.is_root
            else f"{bot_id.value}/{blob_name.value}"
        )
        return self._sanitize_blob_path(blob_path)

    def _create_external_blob_path(
        self,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_id: document_domain.Id,
        blob_name: document_domain.BlobName,
    ) -> str:
        blob_path = f"{bot_id.value}/{document_folder_id.root}/{document_id.value}/{blob_name.value}"
        return self._sanitize_blob_path(blob_path)

    def _get_blob_content(
        self,
        blob_client: BlobClient,
    ) -> bytes:
        with BytesIO() as bytes_stream:
            blob_client.download_blob().readinto(bytes_stream)
            bytes_stream.seek(0)
            return bytes_stream.read()

    def get_document_blob(
        self,
        container_name: ContainerName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ) -> bytes:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        # Determine the blob path
        blob_path = self._create_blob_path(
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )

        # Get the blob client and download the blob into a bytes stream
        blob_client = blob_container.get_blob_client(blob_path)
        return self._get_blob_content(blob_client)

    def get_document_blob_v2(
        self,
        container_name: ContainerName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
        bot_id: bot_domain.Id,
    ) -> bytes:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")

        blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )

        # Get the blob client and download the blob into a bytes stream
        blob_client = blob_container.get_blob_client(blob_path)
        return self._get_blob_content(blob_client)

    def get_external_document_blob(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_id: document_domain.Id,
        blob_name: document_domain.BlobName,
    ) -> bytes:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        blob_path = self._create_external_blob_path(
            bot_id=bot_id,
            document_folder_id=document_folder_id,
            document_id=document_id,
            blob_name=blob_name,
        )

        blob_client = blob_container.get_blob_client(blob_path)
        return self._get_blob_content(blob_client)

    def convert_and_upload_pdf_file(
        self,
        container_name: ContainerName,
        blob_name: document_domain.BlobName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        file_data: bytes,
    ) -> None:
        blob_path = self._create_blob_path(
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )

        blob_path_pdf = self._convert_to_blob_path_pdf(blob_path)

        self._convert_and_upload_pdf(
            container_name=container_name, blob_path=blob_path, blob_path_pdf=blob_path_pdf, file_data=file_data
        )

    def convert_and_upload_pdf_file_v2(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        blob_name: document_domain.BlobName,
        document_folder_context: document_folder_domain.DocumentFolderContext,
        file_data: bytes,
    ) -> None:
        blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=document_folder_context,
            blob_name=blob_name,
        )

        blob_path_pdf = self._convert_to_blob_path_pdf(blob_path)

        self._convert_and_upload_pdf(
            container_name=container_name, blob_path=blob_path, blob_path_pdf=blob_path_pdf, file_data=file_data
        )

    def convert_and_upload_external_pdf_file(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        document_folder_id: document_folder_domain.Id,
        document_id: document_domain.Id,
        blob_name: document_domain.BlobName,
        file_data: bytes,
    ) -> None:
        blob_path = self._create_external_blob_path(
            bot_id=bot_id,
            document_folder_id=document_folder_id,
            document_id=document_id,
            blob_name=blob_name,
        )

        blob_path_pdf = self._convert_to_blob_path_pdf(blob_path)

        self._convert_and_upload_pdf(
            container_name=container_name, blob_path=blob_path, blob_path_pdf=blob_path_pdf, file_data=file_data
        )

    def _convert_and_upload_pdf(
        self,
        container_name: ContainerName,
        blob_path: str,
        blob_path_pdf: str,
        file_data: bytes,
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name}")

        dirname = "/tmp/libreoffice"
        basename = str(uuid4())
        extension = os.path.splitext(blob_path)[1]
        input_file_path = f"{dirname}/{basename}{extension}"
        output_file_path = f"{dirname}/{basename}.pdf"

        os.makedirs(dirname, exist_ok=True)

        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)
            try:
                process = subprocess.Popen(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        input_file_path,
                        "--outdir",
                        dirname,
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.communicate()

                if process.returncode != 0:
                    stderr = process.stderr.read().decode("utf-8") if process.stderr else ""
                    raise Exception(f"LibreOffice conversion failed: {stderr}")

                with open(output_file_path, "rb") as output_file:
                    pdf_data = output_file.read()

                pdf_data_io = BytesIO(pdf_data)

                with pdf_data_io as bytes_stream:
                    blob_container.upload_blob(
                        blob_path_pdf,
                        bytes_stream,
                        overwrite=True,
                    )
            finally:
                os.remove(input_file_path)
                os.remove(output_file_path)
                os.rmdir(dirname)

    def _sanitize_blob_path(self, path: str) -> str:
        return path.replace("\\", "%5C")

    def _convert_to_blob_path_pdf(self, blob_path: str) -> str:
        root_path = os.path.splitext(self._sanitize_blob_path(blob_path))
        return f"{root_path[0]}.pdf"

    def update_document_folder_path(
        self,
        container_name: ContainerName,
        bot_id: bot_domain.Id,
        old_document_folder_context: document_folder_domain.DocumentFolderContext,
        new_document_folder_context: document_folder_domain.DocumentFolderContext,
        blob_name: document_domain.BlobName,
    ) -> None:
        blob_container = self.blob_service_client.get_container_client(container_name.root)
        if not blob_container.exists():
            raise Exception(f"blob container not found. container_name: {container_name.root}")
        old_blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=old_document_folder_context,
            blob_name=blob_name,
        )
        old_blob = blob_container.get_blob_client(old_blob_path)
        new_blob_path = self._create_blob_path_v2(
            bot_id=bot_id,
            document_folder_context=new_document_folder_context,
            blob_name=blob_name,
        )
        new_blob = blob_container.get_blob_client(new_blob_path)

        if not old_blob.exists():
            raise NotFound("ファイルが見つかりませんでした。")

        if new_blob.exists():
            raise Conflict("ファイルが既に存在します。")

        # blobファイルの移動
        new_blob.start_copy_from_url(old_blob.url)

        # 古いblobファイルの削除
        old_blob.delete_blob()
