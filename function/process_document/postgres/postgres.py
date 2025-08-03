from enum import Enum
from typing import Literal, TypedDict
from uuid import UUID

from psycopg2.extras import DictCursor
from pydantic import BaseModel
from sqlalchemy import select

from libs.connection import get_connection
from libs.session import Session

from .models.document_folder import DocumentFolder as DocumentFolderModel
from .models.document_folder_path import DocumentFolderPath as DocumentFolderPathModel


class Bot(TypedDict):
    id: int
    name: str
    index_name: str
    container_name: str
    search_method: str
    pdf_parser: Literal["pypdf", "document_intelligence", "ai_vision", "llm_document_reader"]
    enable_web_browsing: bool
    approach_variables: dict[str, str]
    data_source_id: str
    enable_follow_up_questions: bool


def get_bot(tenant_id: int, bot_id: int) -> Bot:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT b.*, av.name AS var_name, av.value AS var_value
                FROM bots b
                LEFT JOIN approach_variables av ON b.id = av.bot_id
                WHERE b.tenant_id = %s and b.id = %s
            """,
                (tenant_id, bot_id),
            )

            rows = cur.fetchall()
            if len(rows) == 0:
                raise Exception(f"bot not found. bot_id: {bot_id}")

            bot: Bot = {
                "id": rows[0]["id"],
                "name": rows[0]["name"],
                "index_name": rows[0]["index_name"],
                "container_name": rows[0]["container_name"],
                "search_method": rows[0]["search_method"],
                "pdf_parser": rows[0]["pdf_parser"],
                "enable_web_browsing": rows[0]["enable_web_browsing"],
                "approach_variables": {},
                "data_source_id": rows[0]["data_source_id"],
                "enable_follow_up_questions": rows[0]["enable_follow_up_questions"],
            }

            for row in rows:
                if row["var_name"] is not None:
                    bot["approach_variables"][row["var_name"]] = row["var_value"]

            return bot


class DocumentFolder(TypedDict):
    id: UUID
    name: str | None
    external_id: str | None


class DocumentFolderWithOrder(DocumentFolder):
    order: int


class DocumentFolderWithAncestors(DocumentFolder):
    ancestor_folders: list[DocumentFolderWithOrder]


def get_document_folder(id: UUID) -> DocumentFolder:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM document_folders WHERE id = %s", (str(id),))
            document_folder = cur.fetchone()
            if document_folder is None:
                raise Exception(f"document folder not found. document_folder_id: {id}")
            return {
                "id": UUID(document_folder["id"]),
                "name": document_folder["name"] or None,
                "external_id": document_folder["external_id"] or None,
            }


def get_root_document_folder_by_bot_id(bot_id: int) -> DocumentFolder:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT df.id, df.bot_id, df.name, df.created_at, df.updated_at, df.deleted_at, df.external_id
                FROM document_folders df JOIN document_folder_paths dfp ON dfp.descendant_document_folder_id = df.id
                WHERE df.bot_id = %s GROUP BY df.id
                HAVING count(dfp.id) = 1
            """,
                (bot_id,),
            )
            document_folder = cur.fetchone()
            if document_folder is None:
                raise Exception(f"root document folder not found. bot_id: {bot_id}")
            return {
                "id": UUID(document_folder["id"]),
                "name": document_folder["name"] or None,
                "external_id": document_folder["external_id"] or None,
            }


def find_with_ancestors_by_id_and_bot_id(id: UUID, bot_id: int) -> DocumentFolderWithAncestors:
    with Session() as session:
        # サブクエリ: 対象フォルダとその祖先のIDと階層順序を取得
        ancestor_subquery = (
            select(DocumentFolderPathModel)
            .where(DocumentFolderPathModel.descendant_document_folder_id == id)
            .subquery()
        )

        # メインクエリ
        stmt = (
            select(DocumentFolderModel)
            .join(ancestor_subquery, DocumentFolderModel.id == ancestor_subquery.c.ancestor_document_folder_id)
            .where(DocumentFolderModel.bot_id == bot_id)
            .order_by(ancestor_subquery.c.path_length.desc())
        )

        result = session.execute(stmt).scalars().all()

        if len(result) == 0:
            raise Exception("指定されたフォルダは存在しません")

        ancestors = [
            DocumentFolderWithOrder(
                id=df.id,
                name=df.name,
                external_id=df.external_id,
                order=index,
            )
            for index, df in enumerate(result[:-1])
        ]
        target = DocumentFolder(
            id=result[-1].id,
            name=result[-1].name,
            external_id=result[-1].external_id,
        )

        return DocumentFolderWithAncestors(
            id=target["id"],
            name=target["name"],
            external_id=target["external_id"],
            ancestor_folders=ancestors,
        )


class Status(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETING = "deleting"


class Document(TypedDict):
    id: int
    bot_id: int
    basename: str
    file_extension: str
    status: Status
    memo: str
    document_folder_id: UUID | None
    external_id: str | None


def get_document(bot_id: int, document_id: int) -> Document:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT d.* FROM documents d
                JOIN document_folders df ON d.document_folder_id = df.id
                WHERE df.bot_id = %s and d.id = %s
            """,
                (bot_id, document_id),
            )
            document = cur.fetchone()
            if document is None:
                raise Exception(f"document not found. document_id: {document_id}")
            return {
                "id": document["id"],
                "bot_id": document["bot_id"],
                "basename": document["basename"],
                "file_extension": document["file_extension"],
                "status": Status(document["status"]),
                "memo": document["memo"] or "",
                "document_folder_id": UUID(document["document_folder_id"]),
                "external_id": document["external_id"] or None,
            }


def update_document_status_to_completed(document_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("UPDATE documents SET status = 'completed' WHERE id = %s", (document_id,))


def update_document_status_to_failed(document_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("UPDATE documents SET status = 'failed' WHERE id = %s", (document_id,))


class Tenant(TypedDict):
    id: int
    name: str
    search_service_endpoint: str
    index_name: str
    container_name: str


def get_tenant(tenant_id: int) -> Tenant:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM tenants WHERE id = %s", (tenant_id,))
            tenant = cur.fetchone()
            if tenant is None:
                raise Exception(f"tenant not found. tenant_id: {tenant_id}")
            return {
                "id": tenant["id"],
                "name": tenant["name"],
                "search_service_endpoint": tenant["search_service_endpoint"],
                "index_name": tenant["index_name"],
                "container_name": tenant["container_name"],
            }


class Metering(BaseModel):
    tenant_id: int
    type: str
    quantity: int
    bot_id: int


def create_metering(metering: Metering) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO metering (tenant_id, bot_id, type, quantity) VALUES (%s, %s, %s, %s)",
                (metering.tenant_id, metering.bot_id, metering.type, metering.quantity),
            )
