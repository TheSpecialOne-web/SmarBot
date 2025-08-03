from typing import TypedDict

from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

from ..blob_storage.blob_storage import BlobFile
from ..types import DEFAULT_TABLE_CHUNK_SIZE

DEFAULT_TEXT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_ENCODING_NAME = "o200k_base"


class Chunk(TypedDict):
    file_name: str  # 元のPDFのファイル名: {encoded_basename}_p{ページ番号}.pdf 例: sample_p1.pdf
    page_number: str  # ページ番号: p{ページ番号} 例: p1
    chunk_number: str  # チャンク番号: p{ページ番号}-{チャンク番号} 例: p1-1
    chunked_text: str  # チャンク化されたテキスト


def split_files_to_chunks(
    files: list[BlobFile], text_chunk_size: int | None, chunk_overlap: int | None
) -> list[Chunk]:
    """
    PDFファイルをチャンクに分割します。

    :param files: PDFファイルのリスト
    :type files: list[BlobFile]
    :return: チャンクのリスト
    :rtype: list[Chunk]
    """
    text_chunk_size = text_chunk_size or DEFAULT_TEXT_CHUNK_SIZE
    chunk_overlap = chunk_overlap or DEFAULT_CHUNK_OVERLAP

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=DEFAULT_ENCODING_NAME,
        chunk_size=text_chunk_size,
        chunk_overlap=chunk_overlap,
        disallowed_special=(),
    )
    chunks: list[Chunk] = []
    for file in files:
        chunk = text_splitter.split_text(file["text"])
        for i, chunked_text in enumerate(chunk):
            escaped_chunked_text = chunked_text.replace("\x00", "")
            chunks.append(
                {
                    "file_name": file["file_name"],
                    "page_number": str(file["page_number"]),
                    "chunk_number": f"{file['page_number']}-{i+1}",
                    "chunked_text": escaped_chunked_text,
                }
            )
    return chunks


def convert_files_to_chunks(files: list[BlobFile]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file in files:
        escaped_chunked_text = file["text"].replace("\x00", "")
        chunks.append(
            {
                "file_name": file["file_name"],
                "page_number": str(file["page_number"]),
                "chunk_number": f"{file['page_number']}",
                "chunked_text": escaped_chunked_text,
            }
        )
    return chunks


def convert_txt_files_to_chunks(files: list[BlobFile]):
    """
    txtファイルをチャンクに分割します。

    :param files: txtファイルのリスト
    :type files: list[BlobFile]
    :return: チャンクのリスト
    :rtype: list[Chunk]
    """
    chunks: list[Chunk] = []
    for chunked_text in files:
        escaped_chunked_text = chunked_text["text"].replace("\x00", "")
        chunks.append(
            {
                "file_name": chunked_text["file_name"],
                "page_number": f"chunk{chunked_text['page_number']}",
                "chunk_number": f"chunk{chunked_text['page_number']}-0",
                "chunked_text": escaped_chunked_text,
            }
        )
    return chunks


def convert_files_to_chunk_by_html_tags(
    files: list[BlobFile],
    text_chunk_size: int | None,
    chunk_overlap: int | None,
    table_chunk_size: int | None,
    file_extension: str,
) -> list[Chunk]:
    """
    PDFファイル、docxファイル、xlsxファイルをチャンクに分割します。

    :param files: PDFファイルのリスト
    :type files: list[BlobFile]
    :return: チャンクのリスト
    :rtype: list[Chunk]
    """
    chunks: list[Chunk] = []
    for file in files:
        # 通常のテキストとテーブルを分割
        chunk_list = split_text_by_html_tags(file["text"])

        # 指定したチャンクサイズ以下になるまで再帰的にチャンク分け
        chunk_list = split_and_optimize_chunk(chunk_list, text_chunk_size, chunk_overlap, table_chunk_size)

        for i, chunked_text in enumerate(chunk_list):
            escaped_chunked_text = chunked_text.replace("\x00", "")

            # docxの場合はchunkの通し番号をページ番号として扱う（参照元表示のため）
            if file_extension == "docx":
                chunks.append(
                    {
                        "file_name": file["file_name"],
                        "page_number": str(i + 1),
                        "chunk_number": f"{file['page_number']}-{i+1}",
                        "chunked_text": escaped_chunked_text,
                    }
                )
            else:
                chunks.append(
                    {
                        "file_name": file["file_name"],
                        "page_number": str(file["page_number"]),
                        "chunk_number": f"{file['page_number']}-{i+1}",
                        "chunked_text": escaped_chunked_text,
                    }
                )
    return chunks


def convert_files_to_chunks_for_ursa(files: list[BlobFile]) -> list[Chunk]:
    """
    PDFファイルの内容をそのままチャンクに格納します。

    :param files: PDFファイルのリスト
    :type files: list[BlobFile]
    :return: チャンクのリスト
    :rtype: list[Chunk]
    """
    chunks: list[Chunk] = []
    for file in files:
        escaped_chunked_text = file["text"].replace("\x00", "")
        chunks.append(
            {
                "file_name": file["file_name"],
                "page_number": "",
                "chunk_number": "",
                "chunked_text": escaped_chunked_text,
            }
        )
    return chunks


def split_text_by_html_tags(text: str) -> list[str]:
    """LLM Document Readerで読んだテキストを分割する関数。

    Args:
        text (str): 分割するテキスト

    Returns:
        list[str]: 分割されたテキストのリスト
    """
    # タグごとにテキストを分解（chunk_listには画像要素、表要素、それ以外の平文のいずれかが入る）
    try:
        soup = BeautifulSoup(text, "html.parser")
        chunk_list: list[str] = [str(tag) for tag in soup.contents if str(tag).strip()]
    finally:
        soup.decompose()

    chunk_overlaped_list: list[str] = []
    for i in range(len(chunk_list)):
        chunk_overlaped = chunk_list[i]

        # 前後に<table> または <img> が含まれていない場合（平文）のみOverwrapを付与（前後`DEFAULT_CHUNK_OVERLAP`）
        previous_chunk = chunk_list[i - 1] if i > 0 else ""
        try:
            previous_soup = BeautifulSoup(previous_chunk, "html.parser")
            if not previous_soup.find("table") and not previous_soup.find("img"):
                chunk_overlaped = previous_chunk[-DEFAULT_CHUNK_OVERLAP:] + chunk_list[i]
        finally:
            previous_soup.decompose()

        next_chunk = chunk_list[i + 1] if i < len(chunk_list) - 1 else ""
        try:
            next_soup = BeautifulSoup(next_chunk, "html.parser")
            if not next_soup.find("table") and not next_soup.find("img"):
                chunk_overlaped += next_chunk[:DEFAULT_CHUNK_OVERLAP]
        finally:
            next_soup.decompose()

        # Overwrapの関係で一つ前のチャンクと同じになってしまう場合、スキップ
        if i > 0 and len(chunk_overlaped_list) > i - 1 and chunk_overlaped_list[i - 1] == chunk_overlaped:
            continue

        chunk_overlaped_list.append(chunk_overlaped)
    return chunk_overlaped_list


def get_token_count(string: str) -> int:
    """文字列のトークン数を返す関数。

    Args:
        string (str): チャンク分けされたテキスト
        encoding_name (str): エンコーディング名

    Returns:
        int: トークン数
    """
    encoding = tiktoken.get_encoding(DEFAULT_ENCODING_NAME)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def split_and_optimize_chunk(
    chunk_list: list[str], text_chunk_size: int | None, chunk_overlap: int | None, table_chunk_size: int | None
) -> list[str]:
    """指定したチャンク数以下になるまで再帰的にチャンク分けする関数。

    Args:
        chunk_list (list[str]): チャンク分けされたテキストのリスト

    Returns:
        list[str]: CHUNK_SIZE以下になるように最適化された、チャンク分けされたテキストのリスト
    """
    text_chunk_size = text_chunk_size or DEFAULT_TEXT_CHUNK_SIZE
    table_chunk_size = table_chunk_size or DEFAULT_TABLE_CHUNK_SIZE
    chunk_overlap = chunk_overlap or DEFAULT_CHUNK_OVERLAP

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=text_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        disallowed_special=(),
    )
    table_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=table_chunk_size, chunk_overlap=0, separators=["\n\n", "\n", " ", ""], disallowed_special=()
    )

    revised_chunk_list = []
    for chunk in chunk_list:
        token_count = get_token_count(chunk)
        # テキストの許容チャンクサイズ以上の場合
        try:
            chunk_soup = BeautifulSoup(chunk, "html.parser")
            if token_count > DEFAULT_TEXT_CHUNK_SIZE and not chunk_soup.find("table") and not chunk_soup.find("img"):
                revised_chunk_list.extend(text_splitter.split_text(chunk))
            elif token_count > DEFAULT_TABLE_CHUNK_SIZE and chunk_soup.find("table"):
                revised_chunk_list.extend(table_splitter.split_text(chunk))
            else:
                revised_chunk_list.append(chunk)
        finally:
            chunk_soup.decompose()
    return revised_chunk_list
