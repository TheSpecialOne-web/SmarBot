from fastapi import Request

from api.libs.app_env import app_env


def get_client_ip(request: Request) -> str:
    """X-Azure-ClientIP ヘッダーからクライアントのIPアドレスを取得する関数"""
    if app_env.is_localhost():
        return request.client.host if request.client else ""

    x_azure_client_ip = request.headers.get("X-Azure-ClientIP")
    if not x_azure_client_ip:
        raise Exception("X-Azure-ClientIP not found")

    try:
        client_ip = x_azure_client_ip.split(",")[0]
    except Exception:
        client_ip = x_azure_client_ip
    return client_ip
