import os
import time
from typing import TypedDict

from auth0.v3.authentication import GetToken


class Auth0ClientSettings(TypedDict):
    domain: str
    token: str


class Auth0Client:
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str
    auth0_audience: str
    get_token: GetToken
    access_token_cache: str | None
    access_token_expiry: int

    def __init__(self):
        # Auth0のドメイン、クライアントID、クライアントシークレットを設定
        self.auth0_domain = os.environ.get("AUTH0_DOMAIN")
        self.auth0_client_id = os.environ.get("AUTH0_CLIENT_ID")
        self.auth0_client_secret = os.environ.get("AUTH0_CLIENT_SECRET")
        self.auth0_audience = os.environ.get("AUTH0_AUDIENCE")
        self.get_token = GetToken(self.auth0_domain)
        self.access_token_cache = None
        self.access_token_expiry = 0

    def get_auth0_client_settings(self) -> Auth0ClientSettings:
        if not self.auth0_domain:
            raise Exception("AUTH0_DOMAIN is not set")

        # キャッシュされたトークンを使用（有効期限内の場合）
        if self.access_token_cache and time.time() < self.access_token_expiry:
            return {"domain": self.auth0_domain, "token": self.access_token_cache}

        # キャッシュがない、または期限切れの場合、/oauth/tokenエンドポイントを呼び出してトークンを取得
        access_token_data = self.get_token.client_credentials(
            self.auth0_client_id,
            self.auth0_client_secret,
            f"https://{self.auth0_domain}/api/v2/",
        )
        access_token = access_token_data["access_token"]
        if not isinstance(access_token, str):
            raise Exception("access_token is not a string")
        self.access_token_cache = access_token
        self.access_token_expiry = time.time() + access_token_data["expires_in"]

        return {"domain": self.auth0_domain, "token": self.access_token_cache}
