import os

import pandas as pd
import requests

from .utils import convert_to_mac_path

MAC_PATH_PREFIX = "/Volumes/ursa-poc-data"
WINDOWS_PATH_PREFIX = "Z:"

# 安全とTIOSのファイルは今回対象外となっている
PREFIXES_TO_REMOVE = ["/Volumes/ursa-poc-data/安全", "/Volumes/ursa-poc-data/TIOSサンプル"]

# 安全とTIOSのファイルを除外した全てのファイルパスを取得
current_dir = os.path.dirname(__file__)
all_documents_path = os.path.join(current_dir, "../data/filepath_id.csv")
all_documents_series = pd.read_csv(all_documents_path)["file_path"]
all_documents = {
    document
    for document in all_documents_series
    if not any(document.startswith(prefix) for prefix in PREFIXES_TO_REMOVE)
}


def get_all_documents_from_bot(backend_uri: str, tenant_id: str, id_token: str, bot_id: str) -> dict | None:
    """
    指定したbot_idのbot直下にある全てのdocumentを取得する
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
    Returns:
        dict | None: ボット直下にある全てのdocument
    """
    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/documents/all"
    try:
        res = requests.get(
            endpoint,
            headers={
                "Authorization": f"Bearer {id_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to get all documents from bot: {e}")
        return None


def get_failed_uploaded_documents(backend_uri: str, tenant_id: str, id_token: str, bot_id: str) -> set | None:
    """
    指定したbot_idのbot直下にアップロードされていないファイルを取得する
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
    Returns:
        set | None: botにアップロードされていないファイル
    """
    all_documents_from_bot = get_all_documents_from_bot(backend_uri, tenant_id, id_token, bot_id)

    if not all_documents_from_bot:
        return None

    uploaded_documents = set()
    for document in all_documents_from_bot["documents"]:
        uploaded_documents.add(convert_to_mac_path(document["memo"]))

    failed_uploaded_documents = all_documents - uploaded_documents
    return failed_uploaded_documents


def get_pending_documents(backend_uri: str, tenant_id: str, id_token: str, bot_id: str) -> set | None:
    """
    指定したbot_idのbot直下にアップロードしたが、AI Searchに反映されていないファイルを取得する
    Args:
        backend_uri (str): バックエンドのURI。
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
    Returns:
        set | None: AI Searchに反映されていないファイル
    """
    all_documents_from_bot = get_all_documents_from_bot(backend_uri, tenant_id, id_token, bot_id)

    if not all_documents_from_bot:
        return None

    pending_documents = set()
    for document in all_documents_from_bot["documents"]:
        if document["status"] == "pending":
            pending_documents.add(convert_to_mac_path(document["memo"]))

    return pending_documents
