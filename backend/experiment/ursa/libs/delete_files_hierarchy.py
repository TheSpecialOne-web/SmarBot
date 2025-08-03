import logging
import os
import time
import unicodedata

import requests

MAX_RETRIES = 5
FOLDERS_TO_LEAVE = ["共有ドライブ"]

# ログディレクトリのパス
log_dir = "logs"
log_file = "delete_errors.log"
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
                f"Failed to get folder information. Folder ID: {parent_folder_id} Error: {e.response.text} Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)

    logger.error(f"フォルダの情報獲得をリトライしましたが、失敗しました。フォルダid : {parent_folder_id}")
    return None


def get_documents_by_folder_id(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, parent_folder_id: str | None
) -> dict | None:
    """
    指定したフォルダ内のドキュメント情報を取得する関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        parent_folder_id (str): 親フォルダのID。
    Returns:
        dict | None: 指定したフォルダ配下のドキュメント情報
    """
    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/documents"
    params = {"parent_document_folder_id": parent_folder_id} if parent_folder_id else {}

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
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(
                f"Failed to get document information. Folder ID: {parent_folder_id} Error: {e.response.text} Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)
    logger.error(f"ドキュメントの情報獲得をリトライしましたが、失敗しました。フォルダid : {parent_folder_id}")
    return None


def delete_document(backend_uri: str, tenant_id: str, id_token: str, bot_id: str, document_id: str) -> None:
    """
    指定したドキュメントを削除する関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        document_id (str): ドキュメントID。
    Returns:
        None
    """
    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/documents/{document_id}"
    params = {"document_id": document_id}

    for i in range(MAX_RETRIES):
        try:
            res = requests.delete(
                endpoint,
                params=params,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": tenant_id,
                },
            )
            res.raise_for_status()
            print(f"Document ID: {document_id} has been deleted.")
            return
        except requests.exceptions.RequestException as e:
            if r"\u51e6\u7406\u4e2d\u306e" in e.response.text:
                print(f"処理中のファイルは削除できません。ドキュメントID: {document_id}")
                return
            print(
                f"Failed to delete document. Document ID: {document_id} Error: {e.response.text} Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)
    logger.error(f"ドキュメントの削除をリトライしましたが、失敗しました。ドキュメントid : {document_id}")
    return


def delete_folder(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, document_folder_id: str | None
) -> None:
    """
    指定したフォルダを削除する関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        document_folder_id (str): フォルダID。
    Returns:
        None
    """
    if not document_folder_id:
        return

    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/document-folders/{document_folder_id}"
    params = {"document_folder_id": document_folder_id}

    for i in range(MAX_RETRIES):
        try:
            res = requests.delete(
                endpoint,
                params=params,
                headers={
                    "Authorization": f"Bearer {id_token}",
                    "X-Tenant-Id": tenant_id,
                },
            )
            res.raise_for_status()
            print(f"Folder ID: {document_folder_id} has been deleted.")
            return
        except requests.exceptions.RequestException as e:
            if r"\u30d5\u30a9\u30eb\u30c0\u306b" in e.response.text:
                print(f"フォルダにドキュメントが存在するため、削除できません。フォルダID: {document_folder_id}")
                return
            print(
                f"Failed to delete folder. Folder ID: {document_folder_id} Error: {e.response.text} Retrying{i + 1}/{MAX_RETRIES}"
            )
            time.sleep(3)
    logger.error(f"フォルダの削除をリトライしましたが、失敗しました。フォルダid : {document_folder_id}")
    return


def delete_files_by_folder_id(
    backend_uri: str, tenant_id: str, id_token: str, bot_id: str, folder_id: str | None
) -> None:
    """
    指定したfolder_id直下のFOLDERS_TO_LEAVE以外のファイル + フォルダを削除する関数
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        folder_id (str): フォルダID。
    Returns:
        None
    """
    # ファイルを削除
    documents = get_documents_by_folder_id(backend_uri, tenant_id, id_token, bot_id, folder_id)
    if not documents:
        return
    for document in documents["documents"]:
        document_id = document["id"]
        document_name = document["name"]
        print(f"Deleting document: {document_name}")
        delete_document(backend_uri, tenant_id, id_token, bot_id, document_id)

    # フォルダを削除
    folders = get_folder_detail(backend_uri, tenant_id, id_token, bot_id, folder_id)
    if not folders:
        return
    for folder in folders["document_folders"]:
        if unicodedata.normalize("NFC", folder["name"]) in FOLDERS_TO_LEAVE:
            continue
        folder_id = folder["id"]
        folder_name = folder["name"]
        # 再帰的に削除
        delete_files_by_folder_id(backend_uri, tenant_id, id_token, bot_id, folder_id)
        print(f"Deleting folder: {folder_name}")
        delete_folder(backend_uri, tenant_id, id_token, bot_id, folder_id)
