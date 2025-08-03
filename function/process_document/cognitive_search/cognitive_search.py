from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID, uuid4

from libs.logging import get_logger

from ..libs.chunk import Chunk
from ..libs.document import extract_number
from .client import get_search_client

logger = get_logger(__name__)


class IndexDocument(TypedDict):
    id: str
    bot_id: int
    data_source_id: str
    document_id: int
    document_folder_id: str | None
    content: str
    blob_path: str
    file_name: str
    file_extension: str
    page_number: int
    created_at: str
    updated_at: str
    question: str | None
    is_vectorized: bool
    external_id: str | None
    parent_external_id: str | None


def convert_chunks_to_index_documents(
    chunks: list[Chunk],
    bot_id: int,
    data_source_id: str,
    document_id: int,
    document_folder_id: UUID | None,
    basename: str,
    document_path: str,
    blob_path: str,
    file_extension: str,
    external_id: str | None,
    parent_external_id: str | None,
) -> list[IndexDocument]:
    """
    チャンクのリストをインデックスドキュメントのリストに変換します。

    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param bot_id: ボットID
    :type bot_id: int
    :param data_source_id: データソースID
    :type data_source_id: str
    :param document_id: ドキュメントID
    :type document_id: int
    :param basename: 元のファイル名（拡張子無し）
    :type basename: str
    :param document_path: 元のファイルまでのパス
    :type document_path: str
    :param blob_path: ファイルのパス
    :type blob_path: str
    :param search_method: 検索方法
    :type search_method: str
    :param file_extension: ファイルの拡張子
    :type file_extension: str
    :return: ドキュメントのリスト
    :rtype: list
    """
    # 更問生成を行うかどうか
    documents: list[IndexDocument] = []
    for chunk in chunks:
        page_number = extract_number(chunk["page_number"])
        iso_now = datetime.now(timezone.utc).isoformat()
        # basename が「neoSmartChatについて」の場合
        #   id                 00000000-0000-0000-0000-000000000000
        #   bot_id             1
        #   data_source_id     00000000-0000-0000-0000-000000000000
        #   document_id        1
        #   content            [フォルダ1/フォルダ2/neoSmartChatについて]:ドキュメントの内容
        #   blob_path          bmVvU21hcnRDaGF044Gr44Gk44GE44.pdf
        #   file_name          neoSmartChatについて
        #   file_extension     pdf
        #   page_number        1
        #   createddate        2021-08-31T08:00:00+00:00
        #   updateddate        2021-08-31T08:00:00+00:00
        #   question           neoSmartChatの価格を教えてください
        #   is_vectorized      False
        #   external_id        3d2d32d24994d4
        #   parent_external_id 7f34g7934g877f
        document: IndexDocument = {
            "id": str(uuid4()),
            "bot_id": bot_id,
            "data_source_id": data_source_id,
            "document_id": document_id,
            "document_folder_id": str(document_folder_id) if document_folder_id is not None else None,
            "content": f"[{document_path}]:{chunk['chunked_text']}",
            "blob_path": blob_path,
            "file_name": basename,
            "file_extension": file_extension,
            "page_number": page_number,
            "created_at": iso_now,
            "updated_at": iso_now,
            "question": None,
            "is_vectorized": False,
            "external_id": external_id,
            "parent_external_id": parent_external_id,
        }

        documents.append(document)
    return documents


def upload_documents_to_index_from_batch(
    endpoint: str,
    index_name: str,
    sections: list[IndexDocument],
) -> None:
    """
    インデックス化するセクションのリストを検索インデックスにインデックス化します。

    :param index_name: インデックス名
    :type index_name: str
    :param sections: インデックス化するセクションのリスト
    :type sections: list
    :return: None
    :rtype: None
    """

    search_client = get_search_client(endpoint, index_name)
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 500 == 0:
            results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
            succeeded = sum([1 for r in results if r.succeeded])
            logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []
    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
        succeeded = sum([1 for r in results if r.succeeded])
        logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def upload_documents_to_tenant_index(
    endpoint: str,
    index_name: str,
    chunks: list[Chunk],
    bot_id: int,
    data_source_id: str,
    document_id: int,
    document_folder_id: UUID | None,
    basename: str,
    document_path: str,
    blob_path: str,
    file_extension: str,
    external_id: str | None,
    parent_external_id: str | None,
) -> None:
    """
    チャンクのリストをインデックスドキュメントのリストに変換し、検索インデックスにインデックス化します。

    :param index_name: インデックス名
    :type index_name: str
    :param search_method: 検索方法
    :type search_method: str
    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param basename: ファイルのベース名
    :type basename: str
    :param document_path: アプリケーション内のファイルのパス
    :type document_path: str
    :param blob_path: Blob内のファイルのパス
    :type blob_path: str
    :param file_extension: ファイルの拡張子
    :type file_extension: str
    :param generate_follow_up_questions: 更問生成を行うかどうか
    :type generate_follow_up_questions: bool
    :return: None
    :rtype: None
    """
    batch_documents = convert_chunks_to_index_documents(
        chunks=chunks,
        bot_id=bot_id,
        data_source_id=data_source_id,
        document_id=document_id,
        document_folder_id=document_folder_id,
        basename=basename,
        document_path=document_path,
        blob_path=blob_path,
        file_extension=file_extension,
        external_id=external_id,
        parent_external_id=parent_external_id,
    )
    logger.info(f"converted chunks to {len(batch_documents)} documents")
    upload_documents_to_index_from_batch(endpoint, index_name, batch_documents)
