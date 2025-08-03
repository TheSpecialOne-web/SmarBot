import argparse
import os
import time

import requests

NEO_SMART_CHAT_DOMAIN = "chat.neoai.jp"


def main():
    args = parse_args()
    tenant_id = args.tenant_id
    id_token = args.id_token
    bot_id = args.bot_id
    files = args.files
    memo = args.memo
    app_env = args.app_env
    # APIの環境を切り替える
    backend_uri = f"https://dev.{NEO_SMART_CHAT_DOMAIN}"
    if app_env == "stg":
        backend_uri = f"https://stg.{NEO_SMART_CHAT_DOMAIN}"
    if app_env == "prod":
        backend_uri = f"https://app.{NEO_SMART_CHAT_DOMAIN}"
    # まとめてアップロードする場合の分岐
    if "/*.pdf" in files:
        files = list_files(files.replace("/*.pdf", ""))
    else:
        files = [files]
    for file in files:
        file_name = file.split("/")[-1]
        try:
            upload_document(backend_uri, tenant_id, id_token, bot_id, file_name, file, memo)
            print(f"アップロードに成功しました。ファイル名 : {file_name}")
            time.sleep(2)
        except Exception as e:
            print(f"アップロードに失敗しました。ファイル名 : {file_name}、エラー : {e}")
            return
    print("アップロードが完了しました。")


def list_files(directory):
    """*.pdfが指定された場合、すべてのファイル名を取ってきてリストで返す関数

    Args:
        directory (str): 例 : data/確定申告

    Returns:
        list: 例 : ["data/確定申告/ファイル1.pdf", "data/確定申告/ファイル2.pdf"]
    """
    with os.scandir(directory) as entries:
        return [os.path.join(directory, entry.name) for entry in entries if entry.is_file()]


def upload_document(backend_uri, tenant_id, id_token, bot_id, file_name, file_path, memo):
    payload = {
        "memo": (None, memo),
        "files": (file_name, open(file_path, "rb"), "application/pdf"),
    }
    try:
        res = requests.post(
            f"{backend_uri}/backend-api/bots/{bot_id}/documents",
            headers={
                "Authorization": f"Bearer {id_token}",
                "X-Tenant-Id": str(tenant_id),
            },
            files=payload,
        )
        if res.status_code != 200:
            try:
                res_json = res.json()
                error_message = res_json["error"]
            except Exception:
                error_message = ""
            raise Exception(f"Status Code: {res.status_code}, Message: {error_message}")
    except Exception as e:
        raise e


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", type=str, help="テナントID")
    parser.add_argument("--id-token", type=str, help="IDトークン")
    parser.add_argument("--bot-id", type=str, help="ボットID")
    parser.add_argument("--files", type=str, help="アップロードしたいファイルのパス")
    parser.add_argument("--memo", type=str, help="アップロードの際に残したいメモ")
    parser.add_argument("--app-env", type=str, help="アプリケーションの環境")
    return parser.parse_args()


if __name__ == "__main__":
    main()
