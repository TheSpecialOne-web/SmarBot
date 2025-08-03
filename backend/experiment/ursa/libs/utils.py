from concurrent.futures import Future, ThreadPoolExecutor
import os
from typing import Any, Callable, Literal

import requests

MAC_PATH_PREFIX = "/Volumes/ursa-poc-data"
WINDOWS_PATH_PREFIX = "Z:"


def execute_parallel(func: Callable[..., Any], kwargs_list: list[dict[str, Any]], max_workers: int) -> list[Any]:
    """並行処理を行う

    Args:
        func (Callable): 並行処理したい関数
        kwargs_list (list[dict[str, Any]]): 関数の引数(dict型)のリスト
        max_workers (int): 並行処理数

    Returns:
        list[Any]: 関数の戻り値のリスト
    """
    response_list: list[Future] = []
    with ThreadPoolExecutor(max_workers=max_workers) as e:
        for kwargs in kwargs_list:
            response: Future = e.submit(func, **kwargs)
            response_list.append(response)
    return [r.result() for r in response_list]


def split_list(lst: list[Any], num: int) -> list[list[Any]]:
    """
    指定されたリストを、可能な限り均等な長さの `num` 個のサブリストに分割します。

    Args:
    lst (list[Any]): 分割する元のリスト。
    num (int): 生成するサブリストの数。

    Returns:
    List[List[Any]]: 分割されたサブリストのリスト。
    """
    quotient = len(lst) // num  # 分割後のリストの長さの商
    remainder = len(lst) % num  # 分割後のリストの長さの余り

    result = []
    start = 0

    for i in range(num):
        length = quotient + (1 if i < remainder else 0)  # 分割後のリストの長さ
        end = start + length  # 分割後のリストの終端インデックス
        result.append(lst[start:end])  # リストを分割して結果に追加
        start = end

    return result


def list_files_in_directory(directory: str, extensions: tuple[str, ...] = (".xlsx", ".pdf", ".docx", ".pptx", ".xls")):
    """
    指定されたディレクトリとそのサブディレクトリ内の特定の拡張子を持つファイル名を取ってきてリストで返す関数。

    Args:
        directory (str): ファイルを検索するディレクトリのパス。例: 'data/確定申告'
        extensions (Tuple[str, ...]): 検索するファイルの拡張子のタプル。

    Returns:
        List[str]: 特定の拡張子を持つファイルのフルパスのリスト。
    """
    file_list = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            if (
                file.endswith(extensions) and not file.startswith(".") and not file.startswith("$")
            ):  # .から始まる隠しファイルと$から始まる一時ファイルを除外
                file_list.append(os.path.join(root, file))
    return file_list


def list_files_in_directory_QA(
    directory: str,
    extensions: tuple[str, ...] = (".xlsx", ".pdf", ".docx", ".pptx"),
    keywords: tuple[str, ...] = ("請求", "仕様", "伺", "物品"),
):
    """
    指定されたディレクトリとそのサブディレクトリ内のファイルについて、以下の条件をどちらも満たすものをリストで返す関数。
    - 「"xlsx", "pdf", "docx", "pptx"」の拡張子を持つ
    - 「"請求", "仕様", "伺", "物品"」というワードがファイルネームに含まれる

    Args:
        directory (str): ファイルを検索するディレクトリのパス。例: 'data/確定申告'
        extensions (Tuple[str, ...]): 検索するファイルの拡張子のタプル。

    Returns:
        List[str]: 特定の拡張子を持つファイルのフルパスのリスト。
    """
    file_list = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            if (
                file.endswith(extensions) and not file.startswith(".") and not file.startswith("$")
            ):  # .から始まる隠しファイルと$から始まる一時ファイルを除外
                if any(
                    keyword in file for keyword in keywords
                ):  # ファイルパスに特定のキーワードが含まれる場合のみ追加
                    file_list.append(os.path.join(root, file))
    return file_list


def get_backend_uri(env: Literal["local", "dev", "stg", "prod"]) -> str:
    """
    指定された環境名に対応するバックエンドのURIを取得する。

    Args:
        env (str): 環境名。local, dev, stg, prod のいずれかを指定する。

    Returns:
        str: バックエンドのURI。

    Raises:
        Exception: env が local, dev, stg, prod のいずれかでない場合に例外を発生させる。
    """
    NEO_SMART_CHAT_DOMAIN = "chat.neoai.jp"

    if env == "local":
        return "http://localhost:8888"
    if env == "dev":
        return f"https://dev.{NEO_SMART_CHAT_DOMAIN}"
    if env == "stg":
        return f"https://stg.{NEO_SMART_CHAT_DOMAIN}"
    if env == "prod":
        return f"https://{NEO_SMART_CHAT_DOMAIN}"
    raise Exception("envはlocal, dev, stg, prodのいずれかを指定してください。")


def get_documents_all(
    tenant_id: str,
    id_token: str,
    bot_id: str,
    env: Literal["local", "dev", "stg", "prod"],
) -> dict | None:
    """
    指定されたテナントID、IDトークン、ボットID、環境を使用してドキュメントデータを取得し、jsonで返す。

    Args:
        tenant_id (str): テナントID。
        id_token (str): 認証用のIDトークン。
        bot_id (str): ボットID。
        env (str): 環境名。

    Returns:
        dict | None: ファイル情報。

    Raises:
        Exception: リクエストが失敗した場合やデータの解析に失敗した場合に例外を発生させる。
    """
    backend_uri = get_backend_uri(env)
    endpoint = f"{backend_uri}/backend-api/bots/{bot_id}/documents/all"

    try:
        res = requests.get(
            endpoint,
            headers={
                "Authorization": f"Bearer {id_token}",
                "X-Tenant-Id": tenant_id,
            },
        )
        res.raise_for_status()  # 直接HTTPエラーを例外として扱う
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch documents: {e}")

    return res.json()


def convert_to_mac_path(windows_path: str) -> str:
    """
    WindowsのファイルパスをMacのファイルパスに変換する。

    Args:
        windows_path (str): Windows形式のファイルパス。

    Returns:
        str: Mac形式に変換されたファイルパス。
    """
    mac_path = windows_path.replace("\\", "/")
    mac_path = mac_path.replace(WINDOWS_PATH_PREFIX, MAC_PATH_PREFIX)
    return mac_path


def convert_to_windows_path(mac_path: str) -> str:
    """
    MacのファイルパスをWindowsのファイルパスに変換する。

    Args:
        mac_path (str): Mac形式のファイルパス。

    Returns:
        str: Windows形式に変換されたファイルパス。
    """
    windows_path = mac_path.replace(MAC_PATH_PREFIX, WINDOWS_PATH_PREFIX)
    windows_path = windows_path.replace("/", "\\")
    return windows_path


def group_path_by_sequential_folder(base_path: str, file_paths: list[str]) -> dict[str, list]:
    """
    ベースパス直下のフォルダごとにファイルパスをグループ化する。
    結果はベースパス直下のフォルダをキーとし、ファイルパスを値とする辞書として返す。
    Args:
        base_path (str): フォルダの基準となるパス
        file_paths (list[str]): ファイルパスのリスト

    Returns:
        dict[str, list]: フォルダごとにグループ

    Examples:
        Inputs:
            base_path = "/home/user/"
            file_paths = [
                "/home/user/folder1/file1.txt",
                "/home/user/folder1/file2.txt",
                "/home/user/folder2/file3.txt",
                "/home/user/folder2/subfolder/file4.txt",
                "/home/user/folder3/file5.txt"
            ]

        Outputs:
            {
                "folder1": ["/home/user/folder1/file1.txt", "/home/user/folder1/file2.txt"],
                "folder2": ["/home/user/folder2/file3.txt", "/home/user/folder2/subfolder/file4.txt"],
                "folder3": ["/home/user/folder3/file5.txt"]
            }
    """

    sub_group_dict: dict[str, list] = {}

    for path in file_paths:
        if path.startswith(base_path):
            relative_path = path[len(base_path) :].strip(os.sep)
            sequential_folder = relative_path.split(os.sep)[0]
            if sequential_folder not in sub_group_dict:
                sub_group_dict[sequential_folder] = []
            sub_group_dict[sequential_folder].append(path)

    return sub_group_dict


def split_path_by_different_sequential_folder(
    base_path: str, file_paths: list[str], num_workers: int
) -> list[list[list[str]]]:
    """
    ベースパス直後のフォルダごとにファイルパスをグループ化し、それを指定された並列数に分割する。
    各分割はフォルダごとのファイルパスのリストのリストとして返される。

    Args:
        base_path (str): フォルダの基準となるパス
        file_paths (list[str]): ファイルパスのリスト
        num_workers (int): 並列数

    Returns:
        list[list[list[str]]]: フォルダごとにグループ化されたファイルパスのリストを、指定された並列数に分割したリスト

    Examples:
        Inputs:
            base_path = "/home/user/"
            file_paths = [
                "/home/user/folder1/file1.txt",
                "/home/user/folder1/file2.txt",
                "/home/user/folder2/file3.txt",
                "/home/user/folder2/subfolder/file4.txt",
                "/home/user/folder3/file5.txt"
            ]
            num_workers = 2

        Outputs:
            [
                [
                    ["/home/user/folder1/file1.txt", "/home/user/folder1/file2.txt"],
                    ["/home/user/folder2/file3.txt", "/home/user/folder2/subfolder/file4.txt"]
                ],
                [
                    ["/home/user/folder3/file5.txt"]
                ]
            ]
    """

    sub_group_dict = group_path_by_sequential_folder(base_path, file_paths)
    num_workers = min(num_workers, len(sub_group_dict))
    results = []
    count = 0
    cur_sublist = []
    for _, file_paths in sub_group_dict.items():
        cur_sublist.append(file_paths)
        count += 1
        if count >= num_workers:
            results.append(cur_sublist)
            cur_sublist = []
            count = 0
    if cur_sublist:
        results.append(cur_sublist)

    return results
