import base64
import json
import os
import re
from typing import TypeVar

from azure.identity import ClientSecretCredential
from msgraph.generated.drives.item.items.item.delta.delta_get_response import DeltaGetResponse
from msgraph.generated.drives.item.items.item.delta_with_token.delta_with_token_get_response import (
    DeltaWithTokenGetResponse,
)
from msgraph.graph_service_client import GraphServiceClient
from pydantic_core import Url
import requests

from api.domain.models import tenant as tenant_domain
from api.domain.models.document import external_data_connection as external_document_domain
from api.domain.models.document_folder import (
    ExternalDocumentFolderToSync,
    external_data_connection as external_document_folder_domain,
)
from api.domain.models.tenant import (
    external_data_connection as external_data_connection_domain,
    tenant_alert as tenant_alert_domain,
)
from api.domain.models.user.email import Email
from api.domain.models.user.name import Name
from api.domain.services.msgraph.msgraph import IMsgraphService
from api.infrastructures.msgraph.client import get_access_token
from api.libs.exceptions import BadRequest, NotFound
from api.libs.logging import get_logger

from .models.drive_item import DriveItem

EMAIL_SENDER_OBJECT_ID = os.environ.get("EMAIL_SENDER_OBJECT_ID")
EMAIL_SENDER_ADDRESS = os.environ.get("EMAIL_SENDER_ADDRESS")
AZURE_PUBLIC_STORAGE_ACCOUNT = os.environ.get("AZURE_PUBLIC_STORAGE_ACCOUNT")
APP_URL = os.environ.get("APP_URL")
LOGO_URL = f"https://{AZURE_PUBLIC_STORAGE_ACCOUNT}.blob.core.windows.net/common-container/neoAIChatLogo.png"

HTTP_POST_URL = f"https://graph.microsoft.com/v1.0/users/{EMAIL_SENDER_OBJECT_ID}/sendMail"
CHUNK_SIZE = 500

T = TypeVar("T")


def split_list_into_sublists(original_list: list[T], size: int = CHUNK_SIZE) -> list[list[T]]:
    return [original_list[i : i + size] for i in range(0, len(original_list), size)]


class MsgraphService(IMsgraphService):
    def __init__(self):
        self.logger = get_logger()

    def _get_client(
        self, credentials: external_data_connection_domain.SharepointDecryptedCredentials
    ) -> GraphServiceClient:
        msgraph_credentials = ClientSecretCredential(
            tenant_id=credentials.tenant_id, client_id=credentials.client_id, client_secret=credentials.client_secret
        )
        scopes = ["https://graph.microsoft.com/.default"]
        return GraphServiceClient(credentials=msgraph_credentials, scopes=scopes)

    def _encode_url(self, url: str):
        return "u!" + base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")

    def _extract_token_from_delta_link(self, delta_link: str) -> str | None:
        # delta(token='TOKEN')
        match = re.search(r"delta\(token='([^']+)'\)", delta_link)
        if match:
            return match.group(1)

        # delta?token=TOKEN, delta()?token=TOKEN
        match = re.search(r"delta(?:\(\))?\?token=([^&]+)", delta_link)
        if match:
            return match.group(1)

        return None

    def _extract_documents_from_delta_response(
        self,
        delta_response: DeltaGetResponse | DeltaWithTokenGetResponse,
    ) -> list[external_document_domain.ExternalDocument]:
        if delta_response.value is None:
            raise NotFound("指定したアイテムが見つかりません。")

        documents = []
        for drive_item in delta_response.value:
            if drive_item.folder is not None:
                continue
            try:
                document = DriveItem(drive_item).to_document_domain()
            except BadRequest:
                continue

            documents.append(document)

        return documents

    async def _get_drive_item_url(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
        is_folder: bool,
    ) -> str:
        client = self._get_client(credentials)

        drive_item = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .get()
        )
        if drive_item is None:
            raise NotFound("指定したアイテムが見つかりません。")
        if is_folder and drive_item.folder is None:
            raise BadRequest("指定したアイテムはフォルダではありません。")
        if not is_folder and drive_item.folder is not None:
            raise BadRequest("指定したアイテムはフォルダです。")
        if drive_item.web_url is None:
            raise BadRequest("指定したアイテムのURLが取得できません。")
        return drive_item.web_url

    def send_alert_email_to_tenant_users(
        self,
        tenant_name: tenant_domain.Name,
        recipients: list[Email],
        bcc_recipients: list[Email],
        alerts: list[tenant_alert_domain.Alert],
    ) -> None:
        alert_components = ""
        for alert in alerts:
            usage_rate = alert.usage.root / alert.limit.root * 100
            if alert.type == tenant_alert_domain.AlertType.STORAGE:
                alert_components += f"<h3>・ストレージ使用量:{usage_rate:.2f}%</h3>"
            elif alert.type == tenant_alert_domain.AlertType.TOKEN:
                alert_components += f"<h3>・消費トークン数:{usage_rate:.2f}%</h3>"
            # TODO: delete ocr type
            elif alert.type == tenant_alert_domain.AlertType.OCR:
                alert_components += f"<h3>・高精度表読み取り+OCR処理数:{usage_rate:.2f}%</h3>"

        is_over_limit = any(alert.usage.root > alert.limit.root for alert in alerts)
        description = (
            f"{tenant_name.value}の以下の使用上限が超過しました。"
            if is_over_limit
            else f"{tenant_name.value}の以下の使用上限が間近です。"
        )

        token = get_access_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        html = """
                    <html>
                    <head>
                    <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }}
                    h1 {{
                        color: #333333;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }}
                    p {{
                        color: #555555;
                        font-size: 16px;
                        line-height: 1.5;
                        margin-bottom: 20px;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #007bff;
                        color: #ffffff;
                        text-decoration: none;
                        border-radius: 5px;
                        font-size: 16px;
                    }}
                    .button:hover {{
                        background-color: #0056b3;
                    }}
                    .logo {{
                        display: block;
                        margin: 0 auto 20px;
                        max-width: 200px;
                    }}
                    </style>
                    </head>
                    <body>
                    <div class="container">
                        <img src={logo_url} alt="neoAIChat Logo" class="logo">
                        <p>{description}</p>
                        {alert_components}
                        <p><a href="{app_url}" class="button">ログイン画面へ</a></p>
                        <p>使用上限を超過しても利用が直ちに停止されることはございません。</p>
                        <p>超過分については、翌月初頭にご請求書を送付させていただきます。</p>
                        <p>詳細は、営業担当者へお問い合わせください。</p>
                        <p>neoAI Chatカスタマーサポートチーム</p>
                    </div>
                    </body>
                    </html>
                    """

        # send email to tenant admins
        chunked_recipient_emails_list = split_list_into_sublists(recipients)
        for chunked_recipient_emails in chunked_recipient_emails_list:
            data = {
                "message": {
                    "subject": "【neoAI Chat】組織の使用容量についてのお知らせ",
                    "body": {
                        "contentType": "HTML",
                        "content": html.format(
                            app_url=APP_URL,
                            logo_url=LOGO_URL,
                            description=description,
                            alert_components=alert_components,
                        ),
                    },
                    "from": {"emailAddress": {"address": EMAIL_SENDER_ADDRESS}},
                    "toRecipients": [{"emailAddress": {"address": email.value}} for email in chunked_recipient_emails],
                },
                "saveToSentItems": "true",
            }

            res = requests.post(HTTP_POST_URL, json.dumps(data), headers=headers, proxies=None)
            if res.status_code != 202:
                raise Exception(f"Failed to send email: {res.text}")

        # send email to neoai
        chunked_bcc_recipient_emails_list = split_list_into_sublists(bcc_recipients)
        for chunked_bcc_recipient_emails in chunked_bcc_recipient_emails_list:
            data = {
                "message": {
                    "subject": "【neoAI Chat】組織の使用容量についてのお知らせ",
                    "body": {
                        "contentType": "HTML",
                        "content": html.format(
                            app_url=APP_URL,
                            logo_url=LOGO_URL,
                            description=description,
                            alert_components=alert_components,
                        ),
                    },
                    "from": {"emailAddress": {"address": EMAIL_SENDER_ADDRESS}},
                    "bccRecipients": [
                        {"emailAddress": {"address": email.value}} for email in chunked_bcc_recipient_emails
                    ],
                },
                "saveToSentItems": "true",
            }

            res = requests.post(HTTP_POST_URL, json.dumps(data), headers=headers, proxies=None)
            if res.status_code != 202:
                raise Exception(f"Failed to send email: {res.text}")

    def send_create_user_email(self, name: Name, email: Email) -> None:
        try:
            token = get_access_token()
        except Exception as e:
            self.logger.error("Failed to get access token", exc_info=e)
            return
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        html = """
                <html>
                <head>
                <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }}
                h1 {{
                    color: #333333;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #555555;
                    font-size: 16px;
                    line-height: 1.5;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 16px;
                }}
                .button:hover {{
                    background-color: #0056b3;
                }}
                .logo {{
                    display: block;
                    margin: 0 auto 20px;
                    max-width: 200px;
                }}
                </style>
                </head>
                <body>
                <div class="container">
                    <img src={logo_url} alt="neoAIChat Logo" class="logo">
                    <h1>neoAI Chatへようこそ、{name}さん！</h1>
                    <p>neoAI Chatに、組織管理者によってあなたのアカウントが追加されました。</br>ログインするには、以下のリンクをクリックしてください。</p>
                    <p><a href="{app_url}" class="button">ログイン画面へ</a></p>
                    <p>neoAI Chatカスタマーサポートチーム</p>
                </div>
                </body>
                </html>
                """
        data = {
            "message": {
                "subject": "【neoAI Chat】アカウントの準備ができました。",
                "body": {
                    "contentType": "HTML",
                    "content": html.format(
                        name=name.value,
                        app_url=APP_URL,
                        logo_url=LOGO_URL,
                    ),
                },
                "from": {"emailAddress": {"address": EMAIL_SENDER_ADDRESS}},
                "toRecipients": [{"emailAddress": {"address": email.value}}],
            },
            "saveToSentItems": "true",
        }

        res = requests.post(HTTP_POST_URL, json.dumps(data), headers=headers, proxies=None)
        if res.status_code != 202:
            self.logger.error(f"Failed to send email: {res.text}")

    async def is_authorized_client(
        self, credentials: external_data_connection_domain.SharepointDecryptedCredentials
    ) -> bool:
        client = self._get_client(credentials)

        try:
            await client.drives.get()
            return True
        except Exception as e:
            self.logger.error("Failed to get user", exc_info=e)
            return False

    async def get_external_document_folder_to_sync(
        self, credentials: external_data_connection_domain.SharepointDecryptedCredentials, shared_url: str
    ) -> ExternalDocumentFolderToSync:
        client = self._get_client(credentials)
        encoded_url = self._encode_url(shared_url)

        drive_item = await client.shares.by_shared_drive_item_id(encoded_url).drive_item.get()
        if drive_item is None:
            raise NotFound("指定したアイテムが見つかりません。")
        if drive_item.folder is None:
            raise BadRequest("指定したアイテムはフォルダではありません。")
        return DriveItem(drive_item).to_domain_to_sync()

    async def get_descendant_documents_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> list[external_document_domain.ExternalDocument]:
        client = self._get_client(credentials)
        delta_get_response = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .delta.get()
        )
        if delta_get_response is None:
            raise NotFound("指定したアイテムが見つかりません。")

        descendant_documents = self._extract_documents_from_delta_response(delta_get_response)

        next_link = delta_get_response.odata_next_link
        if next_link is None:
            return descendant_documents

        while next_link:
            token = self._extract_token_from_delta_link(next_link)
            if token is None:
                raise BadRequest("トークンが見つかりません。")
            delta_with_token_get_response = (
                await client.drives.by_drive_id(external_id.drive_id)
                .items.by_drive_item_id(external_id.drive_item_id)
                .delta_with_token(token)
                .get()
            )
            if delta_with_token_get_response is None:
                raise NotFound("指定したアイテムが見つかりません。")

            descendant_documents_to_extend = self._extract_documents_from_delta_response(delta_with_token_get_response)
            descendant_documents.extend(descendant_documents_to_extend)

            next_link = delta_with_token_get_response.odata_next_link

        return descendant_documents

    async def get_document_folder_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_document_folder_domain.ExternalDocumentFolder:
        client = self._get_client(credentials)
        drive_item = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .get()
        )
        if drive_item is None:
            raise NotFound("指定したアイテムが見つかりません。")
        return DriveItem(drive_item).to_document_folder_domain()

    # Ref: https://learn.microsoft.com/ja-jp/graph/api/listitem-delta?view=graph-rest-1.0&tabs=python#query-parameters
    async def get_document_folder_delta_token_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalSyncMetadata:
        client = self._get_client(credentials)

        delta_response = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .delta_with_token("latest")
            .get()
        )
        if delta_response is None or delta_response.odata_delta_link is None:
            raise NotFound("指定したアイテムが見つかりません。")

        delta_token = self._extract_token_from_delta_link(delta_response.odata_delta_link)
        if delta_token is None:
            raise BadRequest("トークンが見つかりません。")

        return external_data_connection_domain.ExternalSyncMetadata(root={"delta_token": delta_token})

    async def get_document_by_id(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_document_domain.ExternalDocument:
        client = self._get_client(credentials)
        drive_item = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .get()
        )
        if drive_item is None:
            raise NotFound("指定したアイテムが見つかりません。")
        return DriveItem(drive_item).to_document_domain()

    async def download_document(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> bytes:
        client = self._get_client(credentials)
        data = (
            await client.drives.by_drive_id(external_id.drive_id)
            .items.by_drive_item_id(external_id.drive_item_id)
            .content.get()
        )
        if data is None:
            raise NotFound("指定したアイテムが見つかりません。")
        return data

    async def get_external_document_folder_url(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        url = await self._get_drive_item_url(credentials, external_id, is_folder=True)
        return external_data_connection_domain.ExternalUrl(root=Url(url))

    async def get_external_document_url(
        self,
        credentials: external_data_connection_domain.SharepointDecryptedCredentials,
        external_id: external_data_connection_domain.SharepointExternalId,
    ) -> external_data_connection_domain.ExternalUrl:
        url = await self._get_drive_item_url(credentials, external_id, is_folder=False)
        return external_data_connection_domain.ExternalUrl(root=Url(url))
