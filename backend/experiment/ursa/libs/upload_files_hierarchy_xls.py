import base64
from datetime import datetime, timezone
import logging
import os
import re

# from concurrent.futures import Furture, ThreadPoolExecutor
import time
from typing import Literal, TypedDict
import unicodedata
import uuid

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd
import requests

from .utils import (
    convert_to_mac_path,
    convert_to_windows_path,
    execute_parallel,
    get_backend_uri,
    get_documents_all,
    split_list,
)

# 定数の設定
WINDOWS_PATH_PREFIX = "Z:"
MAC_PATH_PREFIX = "/Volumes/ursa-poc-data"
DRIVE_DIR = "共有ドライブ"
MAX_RETRIES = 5

# Azure OpenAIの設定
dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path)

# ログディレクトリのパス
log_dir = "logs"
log_file = "upload_xls_errors.log"
log_path = os.path.join(log_dir, log_file)

# ディレクトリが存在しない場合は作成
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # ERRORレベル以上のログを記録

# ファイルハンドラの設定
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.ERROR)

# フォーマッタの設定
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# ロガーにハンドラを追加
logger.addHandler(file_handler)


# 型チェックのために、アップロードするドキュメントの型を定義
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


def get_target_xls_files(
    tenant_id: str, id_token: str, bot_id: str, env: Literal["local", "dev", "stg", "prod"]
) -> list[dict]:
    """
    指定したbotにアップロードされているxlsファイルのうち、まだAI Searchにアップロードされていないものを取得する。

    Args:
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID
        env (Literal["local", "dev", "stg", "prod"]): アプリケーションの環境

    Returns:
        list[dict]: アップロード対象のxlsファイルのリスト
    """
    xls_files: list[dict] = []  # 全てのファイル
    files = get_documents_all(tenant_id, id_token, bot_id, env)
    if files:
        xls_files = [
            file for file in files["documents"] if file["file_extension"] == "xls" and file["status"] != "completed"
        ]
    return xls_files


def add_filepath_to_xlsfiles(
    xls_files: list[dict], os: Literal["mac", "windows"], data_source: Literal["drive", "safety"]
) -> list[dict]:
    """
    メモをファイルパスに変換して、file_pathとして追加する

    Args:
        xls_files (list[dict]): xlsファイルのリスト
        os (Literal["mac", "windows"]): OS
        data_source (Literal["drive", "safety"]): データソース

    Returns:
        list[dict]: 正しいファイルパスが格納されたxlsファイルのリスト
    """
    if os == "mac":
        for file in xls_files:
            file_path = convert_to_mac_path(file["memo"])
            if data_source == "drive":
                file_path = file_path.replace(MAC_PATH_PREFIX, f"{MAC_PATH_PREFIX}/{DRIVE_DIR}")
            file["file_path"] = file_path
    elif os == "windows":
        for file in xls_files:
            file_path = convert_to_windows_path(file["memo"])
            if data_source == "drive":
                file_path = file_path.replace(WINDOWS_PATH_PREFIX, f"{WINDOWS_PATH_PREFIX}\\{DRIVE_DIR}")
            file["file_path"] = file_path
    return xls_files


def read_html_file_and_extract_text(file_path: str) -> str:
    """
    xlsファイルのパスを受け取り、それの中身がHTMLファイルだった場合に読み込んでテキストを抽出する。
    ursaには元はhtmlファイルだったものが、間違ってのxlsファイルとして保存されていることがあるため、その対応。

    Args:
        file_path (str): ファイルパス
    Returns:
        str: 抽出されたテキスト
    """
    try:
        with open(file_path, "r", encoding="cp932") as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()
        clean_text = text.replace("\n", "")
        return clean_text
    except FileNotFoundError:
        raise Exception("指定されたファイルが見つかりませんでした。")
    except Exception as e:
        raise Exception(f"エラーが発生しました: {e!s}")


def extract_xls_txt(filepath: str) -> str:
    """
    Excelファイルからテキストを抽出する

    Args:
        filepath (str): ファイルパス
    Returns:
        str: 抽出されたテキスト
    Raises:
        ValueError: サポートされていないファイル形式の場合
    """
    ext = os.path.splitext(filepath)[-1].lower()
    if ext not in [".xls", ".xlsx", ".xlsm"]:
        raise ValueError("Unsupported file format")

    engine: Literal["xlrd", "openpyxl", "odf", "pyxlsb"] = "openpyxl" if ext in [".xlsx", ".xlsm"] else "xlrd"
    all_sheets_text = ""
    try:
        with pd.ExcelFile(filepath, engine=engine) as xls:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, engine=engine, dtype=str)

                column_text = " ".join(
                    str(col)
                    for col in df.columns
                    if not str(col).startswith("Unnamed") and str(col) not in ["NaT", "nan"]
                )

                df = df.dropna(axis=1, how="all").dropna(axis=0, how="all").fillna("").astype(str).replace("NaT", "")
                new_index = [idx if str(idx) not in ["NaT", "nan"] else "" for idx in df.index]
                df.index = pd.Index(new_index)
                joined_text = " ".join([" ".join(row[row != ""].values.tolist()) for _, row in df.iterrows()])

                sheet_text = column_text + joined_text
                sheet_text = " ".join(sheet_text.split())
                all_sheets_text += f"{sheet_name}:{sheet_text}\n\n"
    except Exception:
        try:
            all_sheets_text = read_html_file_and_extract_text(filepath)
        except Exception as e:
            logging.error(f"Error: {e}")
    return all_sheets_text


def encode_basename(basename: str) -> str:
    """
    ファイル名をエンコードする

    Args:
        basename (str): ファイル名
    Returns:
        str: エンコードされたファイル名
    """
    basename_NFC = unicodedata.normalize("NFC", basename)
    basename_encoded = base64.urlsafe_b64encode(basename_NFC.encode()).decode("utf-8")[:-2]
    return basename_encoded


def generate_setsubi_document(xls_file: dict, text_all: str) -> UrsaSemanticIndexDocument:
    """
    設備工事のドキュメントを生成する

    Args:
        xls_file (dict): xlsファイルの情報が含まれるJSONオブジェクト
        text_all (str): ファイル内の全テキスト

    Returns:
        IndexDocumentForUrsa: ドキュメント
    """
    encoded_id = str(uuid.uuid4())
    fullpath = xls_file["memo"]
    iso_now = datetime.now(timezone.utc).isoformat()

    try:
        branch = fullpath.split("\\")[1]
    except Exception:
        branch = ""
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    try:
        documenttype = fullpath.split("\\")[2]
    except Exception:
        documenttype = ""
    try:
        constructionname = fullpath.split("\\")[4]
    except Exception:
        constructionname = ""
    try:
        interpolation_path = "\\".join(fullpath.split("\\")[5:-1])
    except Exception:
        interpolation_path = ""
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    year = 0
    try:
        year_match = re.search(r"\d{4}.*", fullpath.split("\\")[3])
        if year_match:
            year = int(year_match.group(0)[:4])
    except Exception:
        pass

    author_match = re.findall(r"【(.*?)】", constructionname)
    try:
        author = author_match[0] if author_match else ""
    except Exception:
        author = ""
    return {
        "id": encoded_id,
        "content": text_all[:1000000] if len(text_all) > 1000000 else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": constructionname,
        "author": author,
        "full_path": fullpath,
        "interpolation_path": interpolation_path,
        "extension": xls_file["file_extension"],
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": documenttype,
        "branch": branch,  # TODO: memoをうまく使おう！
        "year": year if year is not None else 0,
        "sourceid": encode_basename(basename),
        "document_id": xls_file["id"],
        "document_folder_id": str(xls_file["document_folder_id"]),
    }


def generate_shuzen_document(xls_file: dict, text_all: str) -> UrsaSemanticIndexDocument:
    """
    修繕工事のドキュメントを生成する

    Args:
        xls_file (dict): xlsファイルの情報が含まれるJSONオブジェクト
        text_all (str): ファイル内の全テキスト

    Returns:
        IndexDocumentForUrsa: ドキュメント
    """
    encoded_id = str(uuid.uuid4())
    fullpath = xls_file["memo"]
    iso_now = datetime.now(timezone.utc).isoformat()

    try:
        branch = fullpath.split("\\")[1]
    except Exception:
        branch = ""
    try:
        basename = os.path.splitext(fullpath.split("\\")[-1])[0]
    except Exception:
        basename = ""
    try:
        documenttype = fullpath.split("\\")[2]
    except Exception:
        documenttype = ""
    try:
        interpolation_path = "\\".join(fullpath.split("\\")[4:-1])  # 修繕工事では年度以下の情報をパスに持たせる
    except Exception:
        interpolation_path = ""
    try:
        file_name = fullpath.split("\\")[-1]
    except Exception:
        file_name = ""

    year = 0
    try:
        year_match = re.search(r"\d{4}.*", fullpath.split("\\")[3])
        if year_match:
            year = int(year_match.group(0)[:4])
    except Exception:
        pass

    return {
        "id": encoded_id,
        "content": text_all[:1000000] if len(text_all) > 1000000 else text_all,  # ファイル内の全テキスト
        "file_name": file_name,
        "construction_name": "",
        "author": "",
        "full_path": fullpath,
        "interpolation_path": interpolation_path,
        "extension": xls_file["file_extension"],
        "created_at": iso_now,
        "updated_at": iso_now,
        "document_type": documenttype,
        "branch": branch,  # TODO: memoをうまく使おう！
        "year": year if year is not None else 0,
        "sourceid": encode_basename(basename),
        "document_id": xls_file["id"],
        "document_folder_id": str(xls_file["document_folder_id"]),
    }


def upload_document_xls(xls_file: dict, backend_uri: str, tenant_id: str, id_token: str, bot_id: str) -> None:
    """
    xlsファイルをアップロードする

    Args:
        xls_file (dict): xlsファイルの情報が含まれるJSONオブジェクト
        backend_uri (str): バックエンドのURI
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID

    Raises:
        Exception: アップロードに失敗した場合

    """
    memo = xls_file["memo"]
    postgres_document_id = xls_file["id"]
    text_all = extract_xls_txt(xls_file["file_path"])
    if memo.split("\\")[2] == "設備工事":
        document = generate_setsubi_document(xls_file, text_all)
    elif memo.split("\\")[2] == "修繕工事":
        document = generate_shuzen_document(xls_file, text_all)

    # ドキュメントのアップロード
    for i in range(MAX_RETRIES):
        try:
            res = requests.post(
                f"{backend_uri}/backend-api/bots/{bot_id}/documents/{postgres_document_id}/chunks/bulk",
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": str(tenant_id),
                },
                json={"chunks": [document]},
            )
            res.raise_for_status()
            print(f"アップロードに成功しました。ファイル名 : {xls_file['file_path']}、時刻 : {datetime.now()}")
            return
        except Exception as e:
            last_exception_request = e
            print(
                f"Failed to upload document. File name: {xls_file['file_path']}, Error: {e}, Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)
    logger.error(
        f"ドキュメントのアップロードをリトライしましたが、失敗しました。ファイル名 : {xls_file['file_path']}, エラー : {last_exception_request}"
    )


def upload_documents_xls(xls_files: list[dict], backend_uri: str, tenant_id: str, id_token: str, bot_id: str) -> None:
    """
    指定されたリスト内のxlsファイルを順次AI Searchのindexにアップロードする。

    Args:
        xls_files (list[dict]): アップロード対象のxlsファイルのリスト
        backend_uri (str): バックエンドのURI
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID

    Raises:
        Exception: アップロードに失敗した場合
    """
    for xls_file in xls_files:
        try:
            upload_document_xls(xls_file, backend_uri, tenant_id, id_token, bot_id)
            print(f"アップロードに成功しました。ファイル名 : {xls_file['file_path']}、時刻 : {datetime.now()}")
            time.sleep(3)
        except Exception as e:
            print(
                f"アップロードに失敗しました。ファイル名 : {xls_file['file_path']}、エラー : {e}、時刻 : {datetime.now()}"
            )
            logger.error(f"アップロードに失敗しました。ファイル名 : {xls_file['file_path']}、エラー : {e}")
            time.sleep(3)
    print("アップロードが完了しました。")


def upload_files_in_folders_parallel_xls(
    tenant_id: str,
    id_token: str,
    bot_id: str,
    env: Literal["local", "dev", "stg", "prod"],
    num_workers: int,
    os: Literal["mac", "windows"],
    data_source: Literal["drive", "safety"],
) -> None:
    """
    指定されたbot内のxlsファイルのうち、まだAI Searchにアップロードされていないものを取得し、並行処理でアップロードする。

    Args:
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID
        env (Literal["local", "dev", "stg", "prod"]): アプリケーションの環境
        num_workers (int): 並行処理数
        os (Literal["mac", "windows"]): OS
        data_source (Literal["drive", "safety"]): データソース
    """
    backend_uri = get_backend_uri(env)

    print("対象のファイルを取得中...")
    xls_files = get_target_xls_files(tenant_id, id_token, bot_id, env)
    xls_files = add_filepath_to_xlsfiles(xls_files, os, data_source)
    print(f"アップロード対象のファイル数: {len(xls_files)}")

    split_files = split_list(xls_files, num_workers)

    param_list = []
    for files in split_files:
        param_dict = {
            "xls_files": files,
            "backend_uri": backend_uri,
            "tenant_id": tenant_id,
            "id_token": id_token,
            "bot_id": bot_id,
        }
        param_list.append(param_dict)

    execute_parallel(
        upload_documents_xls,
        param_list,
        num_workers,
    )
