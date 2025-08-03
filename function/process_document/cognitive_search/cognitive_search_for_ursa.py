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


class IndexDocumentForUrsa(TypedDict):
    id: bytes
    content: str
    file_name: str
    construction_name: str
    author: str
    path: str
    extention: str
    source_file: str
    target_facilities: str
    construction_start_date: str
    construction_end_date: str
    location: str
    year: int
    summary: str
    branch: str
    document_type: str
    parent_folder: str
    cost: int
    sourceid: str
    document_id: int
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
) -> list[IndexDocumentForUrsa]:
    """
    チャンクのリストをインデックスドキュメントのリストに変換します。

    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param basename: 元のファイル名（拡張子無し）
    :type basename: str
    :return: ドキュメントのリスト
    :rtype: list
    """
    assert len(chunks) == 1
    documents: list[IndexDocumentForUrsa] = []
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
        elif datasource == normalize_text("安全サイト"):
            document = safety_index_documents(**kwargs)
        else:
            raise ValueError(f"Unknown datasource: {datasource}")
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
) -> IndexDocumentForUrsa:
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
        parentfolder = fullpath.split("\\")[-2]
    except Exception:
        parentfolder = ""
    try:
        file_path = "\\".join(fullpath.split("\\")[6:-1])
    except Exception:
        file_path = ""
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
        "content": text_all[:1000000] if len(text_all) > 1000000 else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": constructionname,
        "author": author,
        "path": f"{file_path}\\{basename}.{file_extension}",
        "extention": file_extension,
        "source_file": "",
        "target_facilities": "",
        "construction_start_date": iso_now,
        "construction_end_date": iso_now,
        "location": "",
        "summary": "",
        "document_type": documenttype,
        "cost": 0,
        "branch": branch,  # TODO: memoをうまく使おう！
        "year": year if year is not None else 0,
        "parent_folder": parentfolder,
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id) if document_folder_id is not None else None,
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
) -> IndexDocumentForUrsa:
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
        file_path = "\\".join(fullpath.split("\\")[5:-1])  # 修繕工事では年度以下の情報をパスに持たせる
    except Exception:
        file_path = ""
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
        "content": text_all[:1000000] if len(text_all) > 1000000 else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": "",  # 修繕工事は特定工事に紐づかない
        "author": "",
        "path": f"{file_path}\\{basename}.{file_extension}",  # 修繕工事は特定工事に紐づかない
        "extention": file_extension,
        "source_file": "",
        "target_facilities": "",
        "construction_start_date": iso_now,
        "construction_end_date": iso_now,
        "location": "",
        "summary": "",
        "document_type": documenttype,  # 修繕工事のフラグ
        "cost": 0,
        "branch": branch,  # TODO: memoをうまく使おう！
        "year": year if year is not None else 0,
        "parent_folder": "",
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id) if document_folder_id is not None else None,
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


def safety_index_documents(
    fullpath,
    file_extension,
    text_all,
    chunk,
    iso_now,
    encoded_id,
    postgres_document_id,
    document_folder_id,
    external_id,
    parent_external_id,
) -> IndexDocumentForUrsa:
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    try:
        documenttype = fullpath.split("\\")[2]
    except Exception:
        documenttype = ""
    extention = file_extension
    try:
        branch = fullpath.split("\\")[3]
    except Exception:
        branch = ""
    match = re.search(r"\d{4}年度", fullpath)
    if match:
        year = int(match.group(0)[:4])
    else:
        year = None
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    return {
        "id": encoded_id,
        "content": text_all[:1000000] if len(text_all) > 1000000 else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": basename,  # 工事名に件名を紐づける
        "author": "",
        "path": f"{basename}.{extention}",  # 安全関連は階層構造を持たない
        "extention": extention,
        "source_file": "",
        "target_facilities": "",
        "construction_start_date": iso_now,
        "construction_end_date": iso_now,
        "location": "",
        "summary": "",
        "document_type": documenttype,  # 安全関連のフラグ
        "cost": 0,
        "branch": branch,  # TODO: memoをうまく使おう！
        "year": year if year is not None else 0,
        "parent_folder": "",
        "sourceid": encode_basename(basename),
        "document_id": postgres_document_id,
        "document_folder_id": str(document_folder_id) if document_folder_id is not None else None,
        "external_id": external_id,
        "parent_external_id": parent_external_id,
    }


def normalize_document(
    document: IndexDocumentForUrsa,
) -> IndexDocumentForUrsa:
    """
    documentの各フィールドの値を正規化する関数．

    :param document: 正規化するドキュメント
    :type document: IndexDocumentForUrsa
    :return: 正規化されたドキュメント
    :rtype: IndexDocumentForUrsa
    """
    for key, value in document.items():
        if value is None:
            document[key] = ""  # type: ignore[literal-required]
        elif isinstance(value, str):
            document[key] = mojimoji.zen_to_han(value, kana=False)  # type: ignore[literal-required]
    return document


# 以下のコードは基本的に変更しなくてよいはず
def upload_documents_to_index_from_batch(
    endpoint: str,
    index_name: str,
    sections: list[IndexDocumentForUrsa],
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
        if i % 1000 == 0:
            results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
            succeeded = sum([1 for r in results if r.succeeded])
            logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []
    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)  # type: ignore[arg-type]
        succeeded = sum([1 for r in results if r.succeeded])
        logger.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def upload_documents_to_index(
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

    :param index_name: インデックス名
    :type index_name: str
    :param search_method: 検索方法
    :type search_method: str
    :param chunks: チャンクのリスト
    :type chunks: list[Chunk]
    :param basename: ファイルのベース名
    :type basename: str
    :return: None
    :rtype: None
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
