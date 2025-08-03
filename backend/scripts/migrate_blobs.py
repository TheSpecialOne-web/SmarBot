from contextlib import suppress
from enum import Enum

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from pydantic import BaseModel

load_dotenv()

dsn = "postgresql://postgres:postgres@db/neosmartchat?client_encoding=utf8"
conn = psycopg2.connect(dsn)


class Tenant(BaseModel):
    id: int
    name: str
    container_name: str


def get_tenants():
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, name, container_name
        FROM tenants
        WHERE deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    return [Tenant(**row) for row in rows]


class Approach(str, Enum):
    NEOLLM = "neollm"
    CHAT_GPT_DEFAULT = "chat_gpt_default"
    CUSTOM_GPT = "custom_gpt"
    TEXT_2_IMAGE = "text_2_image"
    URSA = "ursa"


class Bot(BaseModel):
    id: int
    name: str
    approach: Approach
    icon_url: str | None


def get_bots_by_tenant_id(tenant_id: int) -> list[Bot]:
    approaches = [Approach.NEOLLM, Approach.CUSTOM_GPT, Approach.URSA]

    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, name, approach, icon_url
        FROM bots
        WHERE tenant_id = %s AND approach IN %s
        AND deleted_at IS NULL
    """,
        (tenant_id, tuple(approaches)),
    )
    rows = cur.fetchall()
    cur.close()
    return [Bot(**row) for row in rows]


def update_bot_icon_url(bot_id: int, icon_url: str):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bots
        SET icon_url = %s
        WHERE id = %s
    """,
        (icon_url, bot_id),
    )
    conn.commit()
    cur.close()


class DocumentFolder(BaseModel):
    id: str
    name: str | None


def get_document_folders_by_bot_id(bot_id: int) -> list[DocumentFolder]:
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, name
        FROM document_folders
        WHERE bot_id = %s
        AND deleted_at IS NULL
    """,
        (bot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    return [DocumentFolder(**row) for row in rows]


class Document(BaseModel):
    id: int
    basename: str
    file_extension: str


def get_documents_by_folder_id(folder_id: str) -> list[Document]:
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, basename, file_extension
        FROM documents
        WHERE document_folder_id = %s
        AND deleted_at IS NULL
    """,
        (folder_id,),
    )
    rows = cur.fetchall()
    cur.close()
    return [Document(**row) for row in rows]


class BotTemplate(BaseModel):
    id: str
    name: str
    icon_url: str | None


def get_bot_templates():
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, name, icon_url
        FROM bot_templates
        WHERE deleted_at IS NULL
    """
    )
    rows = cur.fetchall()
    cur.close()
    return [BotTemplate(**row) for row in rows]


def update_bot_template_icon_url(bot_template_id: str, icon_url: str):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE bot_templates
        SET icon_url = %s
        WHERE id = %s
    """,
        (icon_url, bot_template_id),
    )
    conn.commit()
    cur.close()


class BotTemplateDocument(BaseModel):
    id: str
    basename: str
    file_extension: str


def get_bot_template_documents_by_bot_template_id(bot_template_id: str) -> list[BotTemplateDocument]:
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT id, basename, file_extension
        FROM common_document_templates
        WHERE bot_template_id = %s
        AND deleted_at IS NULL
    """,
        (bot_template_id,),
    )
    rows = cur.fetchall()
    cur.close()
    return [BotTemplateDocument(**row) for row in rows]


azure_credential = DefaultAzureCredential()

AZURE_BLOB_STORAGE_ACCOUNT = "sty6b7j6po6acuw"
blob_service_client_dev = BlobServiceClient(
    account_url=f"https://{AZURE_BLOB_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=azure_credential,
)

AZURITE_BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=http;AccountName=stbloblocal;AccountKey=c3RibG9ibG9jYWw=;BlobEndpoint=http://azurite:10000/stbloblocal;"
blob_service_client_local: BlobServiceClient = BlobServiceClient.from_connection_string(AZURITE_BLOB_CONNECTION_STRING)


COMMON_CONTAINER_NAME = "common-container"
AZURE_PUBLIC_STORAGE_ACCOUNT = "neoscdevpublicstorage"
common_blob_container_client_dev = BlobServiceClient(
    account_url=f"https://{AZURE_PUBLIC_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=azure_credential,
).get_container_client(COMMON_CONTAINER_NAME)

AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=http;AccountName=stpubliclocal;AccountKey=c3RwdWJsaWNsb2NhbGtleQ==;BlobEndpoint=http://azurite:10000/stpubliclocal;"
common_blob_service_client_local: BlobServiceClient = BlobServiceClient.from_connection_string(
    AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING
)
common_blob_container_client_local = common_blob_service_client_local.get_container_client(COMMON_CONTAINER_NAME)


def create_containers():
    tenants = get_tenants()
    for tenant in tenants:
        print(f"create container for tenant: {tenant.name} container: {tenant.container_name}")
        with suppress(ResourceExistsError):
            blob_service_client_local.create_container(tenant.container_name)


def migrate_document_blobs():
    tenants = get_tenants()
    for tenant in tenants:
        bots = get_bots_by_tenant_id(tenant.id)
        for bot in bots:
            document_folders = get_document_folders_by_bot_id(bot.id)
            for folder in document_folders:
                documents = get_documents_by_folder_id(folder.id)
                for document in documents:
                    blob_path = (
                        f"{bot.id}/{folder.id}/{document.basename}.{document.file_extension}"
                        if folder.name
                        else f"{bot.id}/{document.basename}.{document.file_extension}"
                    )
                    print(f"migrating blob... container: {tenant.container_name}, blob: {blob_path}")
                    try:
                        blob_client_dev = blob_service_client_dev.get_blob_client(
                            container=tenant.container_name,
                            blob=blob_path,
                        )
                        blob_client_local = blob_service_client_local.get_blob_client(
                            container=tenant.container_name,
                            blob=blob_path,
                        )

                        blob = blob_client_dev.download_blob()
                        blob_client_local.upload_blob(
                            blob.readall(),
                            overwrite=True,
                            content_settings=blob_client_dev.get_blob_properties().content_settings,
                        )
                    except ResourceNotFoundError:
                        print(f"blob not found... container: {tenant.container_name}, blob: {blob_path}")
                    except Exception as e:
                        print(f"failed to migrate blob... container: {tenant.container_name}, blob: {blob_path}")
                        print(e)

                    if document.file_extension in ["docx", "xlsx", "pptx"]:
                        pdf_blob_path = (
                            f"{bot.id}/{folder.id}/{document.basename}.pdf"
                            if folder.name
                            else f"{bot.id}/{document.basename}.pdf"
                        )
                        print(f"migrating blob... container: {tenant.container_name}, blob: {pdf_blob_path}")
                        try:
                            blob_client_dev = blob_service_client_dev.get_blob_client(
                                container=tenant.container_name,
                                blob=pdf_blob_path,
                            )
                            blob_client_local = blob_service_client_local.get_blob_client(
                                container=tenant.container_name,
                                blob=pdf_blob_path,
                            )

                            blob = blob_client_dev.download_blob()
                            blob_client_local.upload_blob(
                                blob.readall(),
                                overwrite=True,
                                content_settings=blob_client_dev.get_blob_properties().content_settings,
                            )
                        except ResourceNotFoundError:
                            print(f"pdf blob not found... container: {tenant.container_name}, blob: {pdf_blob_path}")
                        except Exception as e:
                            print(
                                f"failed to migrate pdf blob... container: {tenant.container_name}, blob: {pdf_blob_path}"
                            )
                            print(e)


def migrate_icon_blobs():
    tenants = get_tenants()
    for tenant in tenants:
        bots = get_bots_by_tenant_id(tenant.id)
        for bot in bots:
            if not bot.icon_url:
                continue
            if not bot.icon_url.startswith("https://neoscdevpublicstorage.blob.core.windows.net"):
                print(f"skipping... blob: {bot.icon_url}")
                continue
            print(f"migrating icon blob... blob: {bot.icon_url}")
            blob_client_dev = BlobClient.from_blob_url(blob_url=bot.icon_url, credential=azure_credential)

            container_name = bot.icon_url.split("/")[3]
            blob_name = "/".join(bot.icon_url.split("/")[4:])
            blob_client_local = BlobClient.from_connection_string(
                conn_str=AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING,
                container_name=container_name,
                blob_name=blob_name,
            )
            blob = blob_client_dev.download_blob()
            blob_client_local.upload_blob(
                blob.readall(),
                overwrite=True,
                content_settings=blob_client_dev.get_blob_properties().content_settings,
            )
            icon_url = str(blob_client_local.url)
            if icon_url.startswith("http://azurite"):
                icon_url = icon_url.replace("http://azurite", "http://localhost")

            update_bot_icon_url(bot.id, icon_url)


def migrate_bot_template_blobs():
    bot_templates = get_bot_templates()
    for bot_template in bot_templates:
        bot_template_documents = get_bot_template_documents_by_bot_template_id(bot_template.id)
        for document in bot_template_documents:
            blob_path = f"bot-templates/{bot_template.id}/documents/{document.basename}.{document.file_extension}"
            print(f"migrating blob... container: common-container, blob: {blob_path}")
            blob_client_dev = common_blob_container_client_dev.get_blob_client(blob_path)
            blob_client_local = common_blob_container_client_local.get_blob_client(blob_path)

            blob = blob_client_dev.download_blob()
            blob_client_local.upload_blob(
                blob.readall(),
                overwrite=True,
                content_settings=blob_client_dev.get_blob_properties().content_settings,
            )

        if not bot_template.icon_url:
            continue
        if not bot_template.icon_url.startswith("https://neoscdevpublicstorage.blob.core.windows.net"):
            print(f"skipping... blob: {bot_template.icon_url}")
            continue
        print(f"migrating icon blob... blob: {bot_template.icon_url}")
        blob_client_dev = BlobClient.from_blob_url(blob_url=bot_template.icon_url, credential=azure_credential)

        container_name = bot_template.icon_url.split("/")[3]
        blob_name = "/".join(bot_template.icon_url.split("/")[4:])
        blob_client_local = BlobClient.from_connection_string(
            conn_str=AZURITE_PUBLIC_STORAGE_BLOB_CONNECTION_STRING,
            container_name=container_name,
            blob_name=blob_name,
        )
        blob = blob_client_dev.download_blob()
        blob_client_local.upload_blob(
            blob.readall(),
            overwrite=True,
            content_settings=blob_client_dev.get_blob_properties().content_settings,
        )
        icon_url = str(blob_client_local.url)
        if icon_url.startswith("http://azurite"):
            icon_url = icon_url.replace("http://azurite", "http://localhost")

        update_bot_template_icon_url(bot_template.id, icon_url)


def main():
    create_containers()
    migrate_document_blobs()
    migrate_icon_blobs()
    migrate_bot_template_blobs()


if __name__ == "__main__":
    main()
