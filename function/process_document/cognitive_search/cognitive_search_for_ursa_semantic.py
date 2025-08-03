import math
import os
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import TypedDict

import mojimoji

from libs.logging import get_logger

from ..libs.chunk import Chunk
from ..libs.document import encode_basename
from .client import get_search_client

logger = get_logger(__name__)

MAX_WORD_COUNT = 1000000


class UrsaSemanticIndexDocument(TypedDict):
    id: str
    content: str
    file_name: str
    construction_name: str
    author: str
    year: int
    branch: str
    full_path: str
    interpolation_path: str
    extension: str
    created_at: str
    updated_at: str
    sourceid: str
    document_id: int | None
    document_type: str
    document_folder_id: str | None
    external_id: str | None
    parent_external_id: str | None


def normalize_text(text: str) -> str:
    """
    textを正規化する関数。NFC正規化を行うことで、視覚的には同じ文字列でも異なる文字列として扱われることを防ぐ。
    Args:
        text (str): 正規化前のテキスト
    Returns:
        str: 正規化された名前
    """
    return unicodedata.normalize("NFC", text)


def convert_chunks_to_index_documents(
    chunks: list[Chunk],
    file_extension: str,
    memo: str,
    postgres_document_id: int,
    document_folder_id: uuid.UUID | None,
    external_id: str | None,
    parent_external_id: str | None,
) -> list[UrsaSemanticIndexDocument]:
    """
    チャンクのリストをインデックスドキュメントのリストに変換します。

    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param basename: 元のファイル名（拡張子無し）
    :type basename: str
    :param search_method: 検索方法
    :type search_method: str
    :return: ドキュメントのリスト
    :rtype: list
    """
    assert len(chunks) == 1
    documents: list[UrsaSemanticIndexDocument] = []
    for chunk in chunks:
        iso_now = datetime.now(timezone.utc).isoformat()
        text_all = chunk["chunked_text"]
        fullpath = memo
        encoded_id = str(uuid.uuid4())

        # 新しいフォルダパス = Z:\共有ドライブ\熊本支店_階層整理後\設備工事\2019年度\【岩田】次期ＮＭＳ構築に伴う伝送路整備（熊本支社）のうち単独除却\16　検討資料\02_工事\工事仕様書（ＮＭＳ）_xdw.pdf
        # Z:\熊本支店_階層整理後\設備工事\2019年度\【岩田】次期ＮＭＳ構築に伴う伝送路整備（熊本支社）のうち単独除却\16　検討資料\02_工事\工事仕様書（ＮＭＳ）_xdw.pdf
        # Z:\{datasource}\{branch}\設備工事\2019年度\{constructionname}\16　検討資料\{parentfolder}\{base_name}.pdf
        datasource = fullpath.split("\\")[1]
        kwargs = {
            "fullpath": fullpath,
            "file_extension": file_extension,
            "text_all": text_all,
            "iso_now": iso_now,
            "encoded_id": encoded_id,
            "postgres_document_id": postgres_document_id,
            "document_folder_id": document_folder_id,
            "external_id": external_id,
            "parent_external_id": parent_external_id,
        }

        if datasource in [normalize_text("共有ドライブ"), normalize_text("box")]:
            construction_type = fullpath.split("\\")[3]  # 設備工事 もしくは 修繕工事
            if construction_type == normalize_text("設備工事"):
                document = default_index_documents(**kwargs)
            elif construction_type == normalize_text("修繕工事"):
                document = shuzen_index_documents(**kwargs)
        elif datasource == normalize_text("Sharepoint"):
            document = sharepoint_index_documents(**kwargs)
        elif datasource == normalize_text("安全サイト"):
            document = safety_index_documents(**kwargs)
        else:
            raise ValueError(f"Unknown datasource: {datasource}, fullpath: {fullpath}")
        normalized_document = normalize_document(document)
        documents.append(normalized_document)
    return documents


def default_index_documents(
    fullpath,
    file_extension,
    text_all,
    iso_now,
    encoded_id,
    postgres_document_id,
    document_folder_id,
    external_id,
    parent_external_id,
) -> UrsaSemanticIndexDocument:
    """
    設備工事をindexに上げるときのdocumentを作成する関数
    """
    # fullpathの例）Z:\共有ドライブ\熊本支店_階層整理後\設備工事\2019年度\【岩田】次期ＮＭＳ構築に伴う伝送路整備（熊本支社）のうち単独除却\16　検討資料\02_工事\工事仕様書（ＮＭＳ）_xdw.pdf
    try:
        branch = fullpath.split("\\")[2]
    except Exception:
        branch = ""
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    try:
        documenttype = fullpath.split("\\")[3]
    except Exception:
        documenttype = ""
    try:
        constructionname = fullpath.split("\\")[5]
    except Exception:
        constructionname = ""
    try:
        interpolation_path = "\\".join(fullpath.split("\\")[6:-1])
    except Exception:
        interpolation_path = ""
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    year = 0
    try:
        year_match = re.search(r"\d{4}", fullpath.split("\\")[4])
        if year_match:
            year = int(year_match.group(0))
    except Exception:
        pass

    author = ""
    author_match = re.findall(r"【(.*?)】", constructionname)
    if author_match:
        author = author_match[0]

    return {
        "id": encoded_id,
        "content": text_all[:MAX_WORD_COUNT] if len(text_all) > MAX_WORD_COUNT else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": constructionname,
        "author": author,
        "full_path": fullpath,
        "interpolation_path": interpolation_path,
        "extension": file_extension,
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": documenttype,
        "branch": branch,
        "year": year if year is not None else 0,
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id),
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


def shuzen_index_documents(
    fullpath,
    file_extension,
    text_all,
    iso_now,
    encoded_id,
    postgres_document_id,
    document_folder_id,
    external_id,
    parent_external_id,
) -> UrsaSemanticIndexDocument:
    try:
        branch = fullpath.split("\\")[2]
    except Exception:
        branch = ""
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    try:
        documenttype = fullpath.split("\\")[3]
    except Exception:
        documenttype = ""
    try:
        interpolation_path = "\\".join(fullpath.split("\\")[5:-1])  # 修繕工事では年度以下の情報をパスに持たせる
    except Exception:
        interpolation_path = ""
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    year = 0
    try:
        year_match = re.search(r"\d{4}", fullpath.split("\\")[4])
        if year_match:
            year = int(year_match.group(0))
    except Exception:
        pass

    return {
        "id": encoded_id,
        "content": text_all[:MAX_WORD_COUNT] if len(text_all) > MAX_WORD_COUNT else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": "",
        "author": "",
        "full_path": fullpath,
        "interpolation_path": interpolation_path,
        "extension": file_extension,
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": documenttype,
        "branch": branch,
        "year": year if year is not None else 0,
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id),
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


# TODO: sharepoint_index_documentsの実装
def sharepoint_index_documents(
    fullpath,
    file_extension,
    text_all,
    iso_now,
    encoded_id,
    postgres_document_id,
    document_folder_id,
    external_id,
    parent_external_id,
) -> UrsaSemanticIndexDocument:
    return {
        "id": "",
        "content": "",  # ファイル内の全テキスト
        "file_name": "",
        "construction_name": "",
        "author": "",
        "full_path": "",
        "interpolation_path": "",
        "extension": "",
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": "",
        "branch": "",
        "year": 0,
        "sourceid": "",
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id),
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


# TODO: safety_index_documentsの実装。以下の実装はPoC段階のMockデータに対するもの
def safety_index_documents(
    fullpath,
    file_extension,
    text_all,
    iso_now,
    encoded_id,
    postgres_document_id,
    document_folder_id,
    external_id,
    parent_external_id,
) -> UrsaSemanticIndexDocument:
    """安全サイトの資料をindexに上げるときのdocumentを作成する関数"""
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    extension = file_extension
    try:
        branch = fullpath.split("\\")[3]
    except Exception:
        branch = ""
    year = 0
    try:
        year_match = re.search(r"\d{4}.*", fullpath.split("\\")[4])
        if year_match:
            year = int(year_match.group(0)[:4])
    except Exception:
        pass
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    return {
        "id": encoded_id,
        "content": text_all[:MAX_WORD_COUNT] if len(text_all) > MAX_WORD_COUNT else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": "",
        "author": "",
        "full_path": fullpath,
        "interpolation_path": "",
        "extension": extension,
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": "",  # 先方のbox環境によってdocument_typeに入ってくる値は変わる可能性あり。現状は空で問題なし。
        "branch": branch,
        "year": year if year is not None else 0,
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id),
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


def normalize_document(
    document: UrsaSemanticIndexDocument,
) -> UrsaSemanticIndexDocument:
    """
    documentの各フィールドの値を正規化する関数．

    :param document: 正規化するドキュメント
    :type document: UrsaSemanticIndexDocument
    :return: 正規化されたドキュメント
    :rtype: UrsaSemanticIndexDocument
    """
    for key, value in document.items():
        if value is None:
            document[key] = ""  # type: ignore[literal-required]
        elif isinstance(value, str):
            document[key] = mojimoji.zen_to_han(value, kana=False)  # type: ignore[literal-required]
    return document


def upload_documents_to_index_from_batch(
    endpoint: str,
    index_name: str,
    sections: list[UrsaSemanticIndexDocument],
) -> None:
    """
    ドキュメントのリストをAI Searchにアップロードする。

    :param index_name: AI Searchのインデックス名
    :type index_name: str
    :param sections: アップロードするドキュメント（json）のリスト
    :type sections: list
    :return: None
    :rtype: None
    """

    search_client = get_search_client(endpoint, index_name)
    BATCH_SIZE = 1000
    num_iterations = math.ceil(len(sections) / BATCH_SIZE)
    for i in range(num_iterations):
        start = i * BATCH_SIZE
        end = (i + 1) * BATCH_SIZE
        batch_documents = sections[start:end]
        results = search_client.upload_documents(documents=batch_documents)  # type: ignore[arg-type]
        succeeded_count = len([result for result in results if result.succeeded])
        logger.info(f"\tIndexed {len(results)} sections, {succeeded_count} succeeded")


def upload_hybrid_documents_to_index(
    endpoint: str,
    index_name: str,
    search_method: str,
    chunks: list[Chunk],
    basename: str,
    file_extension: str,
    memo: str,
    document_id: int,
    document_folder_id: uuid.UUID | None,
    external_id: str | None,
    parent_external_id: str | None,
) -> None:
    """
    チャンクのリストをインデックスドキュメントのリストに変換し、検索インデックスにインデックス化します。

    :param endpoint: 検索サービスのエンドポイント
    :type endpoint: str
    :param index_name: インデックス名
    :type index_name: str
    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param basename: 元のファイル名（拡張子無し）
    :type basename: str
    :param file_extension: ファイルの拡張子
    :type file_extension: str
    :param memo: ファイルのフルパス
    :type memo: str
    :param document_id: ドキュメントID
    :type document_id: int
    :param document_folder_id: ドキュメントフォルダID
    :type document_folder_id: UUID
    :return: None
    :rtype
    """
    batch_documents = convert_chunks_to_index_documents(
        chunks=chunks,
        file_extension=file_extension,
        memo=memo,
        postgres_document_id=document_id,
        document_folder_id=document_folder_id,
        external_id=external_id,
        parent_external_id=parent_external_id,
    )

    upload_documents_to_index_from_batch(endpoint, index_name, batch_documents)
