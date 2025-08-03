import logging
import os
import time
from typing import Literal
import unicodedata

import requests

from .utils import (
    convert_to_mac_path,
    convert_to_windows_path,
    execute_parallel,
    get_backend_uri,
    list_files_in_directory,
    list_files_in_directory_QA,
    split_path_by_different_sequential_folder,
)

# 定数の設定
WINDOWS_PATH_PREFIX = "Z:"
MAC_PATH_PREFIX = "/Volumes/ursa-poc-data"
MAX_RETRIES = 5

# ログディレクトリのパス
log_dir = "logs"
log_file = "upload_errors.log"
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


def split_path(file: str) -> list[str]:
    """
    ファイルパスを分割する関数
    Args:
    file (str): ファイルパス
    Returns:
    list[str]: ファイルパスを分割したリスト
    Examples:
    >>> split_path("/Volumes/ursa-poc-data/共有ドライブ/test1/test2/test3")
    ["共有ドライブ", "test1", "test2", "test3"]
    """
    parts: list[str] = []

    if file.startswith(WINDOWS_PATH_PREFIX):
        file = convert_to_mac_path(file)

    file = file.replace(MAC_PATH_PREFIX, "")

    if file.startswith("/"):
        parts = file.split("/")[1:]
    elif file.startswith("\\"):
        parts = file.split("\\")[1:]

    return parts


def normalize_name(name: str) -> str:
    """
    名前を正規化する関数。NFC正規化を行うことで、視覚的には同じ文字列でも異なる文字列として扱われることを防ぐ。
    Args:
        name (str): 名前
    Returns:
        str: 正規化された名前
    """
    return unicodedata.normalize("NFC", name)


def get_folder_detail(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, parent_folder_id: str | None
) -> dict | None:
    """
    フォルダの詳細を取得する関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        parent_folder_id (str): 親フォルダのID。
    Returns:
        dict | None: フォルダ情報
    """
    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/document-folders"
    params = {"parent_document_folder_id": parent_folder_id} if parent_folder_id else {}

    # リトライ処理を行う
    for i in range(MAX_RETRIES):
        try:
            res = requests.get(
                endpoint,
                params=params,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": tenant_id,
                },
            )
            res.raise_for_status()  # ステータスコードが200以外の場合は例外を発生させる
            return res.json()
        except requests.exceptions.RequestException as e:
            print(
                f"Failed to get folder information. Folder ID: {parent_folder_id} Error: {e} Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)

    logger.error(f"フォルダの情報獲得をリトライしましたが、失敗しました。フォルダid : {parent_folder_id}")
    return None


def search_folder(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, parent_folder_id: str | None, folder_name: str
) -> dict | None:
    """
    特定のフォルダが、指定したフォルダIDの直下に存在するかどうかを、名前の一致で調べている関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        parent_folder_id (str): 親フォルダのID。
        folder_name (str): フォルダ名。
    Returns:
        dict | None: フォルダ情報
    """
    response = get_folder_detail(backend_uri, tenant_id, id_token, bot_id, parent_folder_id)

    if not response:
        return None
    folders = response.get("document_folders", [])
    for folder in folders:
        if normalize_name(folder["name"]) == normalize_name(folder_name):
            return folder
    return None


def create_folder(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, parent_folder_id: str | None, folder_name: str
) -> str | None:
    """
    フォルダを指定した親フォルダの直下にアップロードする関数
    Args:
        backend_uri (str): バックエンドのURI
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID
        parent_folder_id (str): 親フォルダのID
        folder_name (str): フォルダ名
    Returns:
        str | None: フォルダID
    """
    folder_name = normalize_name(folder_name)
    response = search_folder(backend_uri, tenant_id, id_token, bot_id, parent_folder_id, folder_name)

    if response:
        existing_folder_id = response.get("id")
        print(f'Folder "{folder_name}" already exists. Folder ID: {existing_folder_id}')
        return existing_folder_id

    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/document-folders"
    data = {"name": folder_name, "parent_document_folder_id": parent_folder_id}

    last_exception: Exception | None = None
    for i in range(MAX_RETRIES):
        try:
            res = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": tenant_id,
                    "Content-Type": "application/json",
                },
                json=data,
            )

            res.raise_for_status()
            folder_id = res.json().get("id")
            print(f'Folder "{folder_name}" created successfully. Folder ID:', folder_id)
            return folder_id

        except requests.exceptions.RequestException as e:
            last_exception = e
            print(
                f"Failed to create folder. Folder name: {folder_name}, Error: {last_exception}, Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)
        except Exception as e:
            last_exception = e
            print(
                f"Failed to create folder due to client issues. Folder name: {folder_name}, Error: {e}, Retrying{i + 1}/{MAX_RETRIES}"
            )
    logger.error(
        f"フォルダの作成をリトライしましたが、失敗しました。フォルダ名 : {folder_name}, エラー : {last_exception}"
    )
    return None


def upload_document_to_folder(
    backend_uri: str,
    tenant_id: str,
    id_token: str,
    bot_id: str,
    fullpath: str,  # must be full path
    parent_folder_id: str | None,
) -> None:
    """
    ドキュメントをフォルダにアップロードする関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        fullpath (str): ファイルのフルパス。
        parent_folder_id (str): 親フォルダのID。
    """
    fullpath = normalize_name(fullpath)
    memo = convert_to_windows_path(fullpath) if not fullpath.startswith(WINDOWS_PATH_PREFIX) else fullpath
    file_name = fullpath.split("/")[-1]

    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/documents"
    params = {"parent_document_folder_id": parent_folder_id} if parent_folder_id else {}

    last_exception: Exception | None = None
    for i in range(MAX_RETRIES):
        try:
            print("Uploading document. File name:", fullpath)
            res = requests.post(  # type: ignore
                endpoint,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": tenant_id,
                },
                params=params,
                files={  # type: ignore
                    "memo": (None, memo),
                    "files": (file_name, open(fullpath, "rb"), "application/pdf"),
                },
            )
            if r"\u3044\u307e\u3059\u3002" in res.text:  # 既に同じファイルが存在する場合, エラーを発生させない
                print(f"File name: {fullpath} Already exists.")
                return
            res.raise_for_status()  # ステータスコードが200以外の場合は例外を発生させる
            print(f"Uploaded successfully. File name: {fullpath}")
            return

        except Exception as e:
            last_exception = e
            print(f"Failed to upload document. File name: {fullpath}, Error: {e}, Retrying{i + 1}/{MAX_RETRIES}")
            time.sleep(3)
    logger.error(
        f"ドキュメントのアップロードをリトライしましたが、失敗しました。ファイル名 : {fullpath}, エラー : {last_exception}"
    )
    return


def upload_document_hierarchy(
    backend_uri: str,
    tenant_id: str,
    id_token: str,
    bot_id: str,
    fullpath: str,
    parent_folder_id: str | None,
    subpath: str | None = None,
) -> None:
    """
    ドキュメントを階層化によってアップロードする関数
    特定のフォルダを直接上げたいときは、subpath、parent_folder_idはNoneにする。
    Args:
        backend_uri (str): バックエンドのURI
        tenant_id (str): テナントID
        id_token (str): 認証用のIDトークン
        bot_id (str): ボットID
        fullpath (str): ファイルのフルパス
        parent_folder_id (str): 親フォルダのID
        subpath (str): ファイルのメインパスの中に含まれる、部分的な経路（base_pathを除いた部分）
    """
    if subpath:
        path = convert_to_mac_path(subpath) if not subpath.startswith(MAC_PATH_PREFIX) else subpath
    else:
        path = convert_to_mac_path(fullpath) if not fullpath.startswith(MAC_PATH_PREFIX) else fullpath
    path_parts = split_path(path)

    for part in path_parts[:-1]:
        parent_folder_id = create_folder(backend_uri, tenant_id, id_token, bot_id, parent_folder_id, part)
        if not parent_folder_id:
            logger.error(f"親フォルダの作成に失敗しました。フォルダ名 : {part}、フルパス：{fullpath}")
            return

    upload_document_to_folder(backend_uri, tenant_id, id_token, bot_id, fullpath, parent_folder_id)


def upload_documents_hierarchy(
    backend_uri: str,
    tenant_id: str,
    id_token: str,
    bot_id: str,
    fullpaths: list[str],
    parent_folder_id: str | None,
    base_path: str | None = None,
) -> None:
    """
    複数のファイルを階層化によってアップロードする関数。
    full_pathsに直接アップロードしたいファイル群をリストとして指定したい場合、parent_folder_idとbase_pathはNoneにする。
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        fullpaths list[str]: ファイルのフルパス。
        parent_folder_id (str): 親フォルダのID。
        base_path (str): ファイルが存在するベースディレクトリのパス。
    """
    if base_path:
        subpaths = [path.replace(base_path, "") for path in fullpaths]
        for subpath, fullpath in zip(subpaths, fullpaths):
            try:
                upload_document_hierarchy(
                    backend_uri, tenant_id, id_token, bot_id, fullpath, parent_folder_id, subpath
                )
                time.sleep(1)
            except Exception as e:
                print(f"アップロードに失敗しました。ファイル名 : {fullpath}、エラー : {e}")
                logger.error(f"アップロードに失敗しました。ファイル名 : {fullpath}、エラー : {e}")
                time.sleep(1)

    else:  # full_pathsにアップロードしたいファイルを直接リストとして渡す場合
        for fullpath in fullpaths:
            try:
                upload_document_hierarchy(backend_uri, tenant_id, id_token, bot_id, fullpath, parent_folder_id)
                time.sleep(1)
            except Exception as e:
                print(f"アップロードに失敗しました。ファイル名 : {fullpath}、エラー : {e}")
                logger.error(f"アップロードに失敗しました。ファイル名 : {fullpath}、エラー : {e}")
                time.sleep(1)

    print("アップロードが完了しました。")


def upload_files_in_folders_parallel_hierarchy(
    base_path: str,
    tenant_id: str,
    id_token: str,
    bot_id: str,
    env: Literal["local", "dev", "stg", "prod"],
    extensions: tuple[str],  # ここを修正
    num_workers: int,
    QA_flag: bool = False,
) -> None:
    """
    フォルダ内のファイルを階層化によってアップロードする関数
    Args:
        base_path (str): ファイルが存在するベースディレクトリのパス。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        env (str): 環境名。
        extensions (tuple[str]): アップロードするファイルの拡張子。
        num_workers (int): 並列処理の数。
        QA_flag (bool): Q&Aデータベースかどうか。
    """
    if not os.path.isdir(base_path):
        raise Exception("ディレクトリを指定してください")
    backend_uri = get_backend_uri(env)

    # ルートフォルダからbase_pathまでのフォルダ作成する
    base_path_parts = split_path(base_path)
    parent_folder_id = None
    for part in base_path_parts:
        parent_folder_id = create_folder(backend_uri, tenant_id, id_token, bot_id, parent_folder_id, part)
        if not parent_folder_id:
            logger.error(f"ベースフォルダの作成が失敗しました。フォルダ名 : {part}")
            return

    # Q&Aの場合は、特定の文字がファイル名に含まれる場合のみアップロード対象となる
    if QA_flag:
        target_fullpath_list = list_files_in_directory_QA(base_path, extensions)
    else:
        target_fullpath_list = list_files_in_directory(base_path, extensions)

    # ファイルのリストをnum_workersの数、もしくはベースフォルダ直下に存在するフォルダの数だけ分割する
    split_fullpath_list = split_path_by_different_sequential_folder(base_path, target_fullpath_list, num_workers)
    # 並列処理をfor文で回す
    for chunk in split_fullpath_list:
        num_workers = len(chunk)
        param_list = []
        for files in chunk:
            print(files)
            param_dict = {
                "backend_uri": backend_uri,
                "tenant_id": tenant_id,
                "id_token": id_token,
                "bot_id": bot_id,
                "fullpaths": files,
                "parent_folder_id": parent_folder_id,  # base_pathのフォルダID
                "base_path": base_path,
            }
            param_list.append(param_dict)

        execute_parallel(
            upload_documents_hierarchy,
            param_list,
            num_workers,
        )
