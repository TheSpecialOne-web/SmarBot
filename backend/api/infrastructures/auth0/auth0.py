from datetime import datetime
from time import sleep
from typing import Callable, TypeVar

from auth0.v3.exceptions import RateLimitError
from auth0.v3.management import Users, UsersByEmail
import jwt
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api.domain.models import user as user_domain
from api.domain.services.auth0 import IAuth0Service
from api.infrastructures.auth0.client import Auth0Client
from api.libs.exceptions import Unauthorized

T = TypeVar("T")


class Auth0Service(IAuth0Service):
    def __init__(self):
        self.client = Auth0Client()
        self.jwks_client = jwt.PyJWKClient(f"https://{self.client.auth0_domain}/.well-known/jwks.json")

    def _handle_rate_limit_error(self, func: Callable[..., T], *args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            reset_at = int(e.reset_at)
            now = datetime.now().timestamp()
            sleep(reset_at - now)
            return func(*args, **kwargs)

    def validate_token(self, token: str) -> user_domain.ExternalUserId:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
        except jwt.exceptions.PyJWKClientError as e:
            raise Exception(f"failed to get signing key: {e}")
        except jwt.exceptions.DecodeError:
            raise Unauthorized("不正なトークンです")

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client.auth0_audience,
                issuer=f"https://{self.client.auth0_domain}/",
            )
            return user_domain.ExternalUserId.from_string(payload["sub"])
        except jwt.exceptions.ExpiredSignatureError:
            raise Unauthorized("トークンの有効期限が切れています")
        except jwt.exceptions.DecodeError:
            raise Unauthorized("不正なトークンです")

    def find_by_id(self, id: user_domain.ExternalUserId) -> user_domain.IdpUser:
        client_settings = self.client.get_auth0_client_settings()

        user = self._handle_rate_limit_error(Users(**client_settings).get, id.root)

        return user_domain.IdpUser.from_id_and_email(
            id=user["user_id"],
            email=user["email"],
        )

    def find_by_emails(self, emails: list[user_domain.Email]) -> list[user_domain.IdpUser]:
        client_settings = self.client.get_auth0_client_settings()

        all_users = []
        per_page = 25
        for i in range(0, len(emails), per_page):
            query = " OR ".join([f'email:"{email.value}"' for email in emails[i : i + per_page]])
            params = {
                "q": query,
                "fields": ["user_id,email"],
                "sort": "created_at:1",
            }
            users = self._handle_rate_limit_error(Users(**client_settings).list, **params)
            all_users.extend(users["users"])

        return [user_domain.IdpUser.from_id_and_email(id=user["user_id"], email=user["email"]) for user in all_users]

    @retry(
        retry=retry_if_exception_type((RateLimitError)),
        wait=wait_exponential(multiplier=2, min=2),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def create_user(self, email: user_domain.Email) -> str:
        client_settings = self.client.get_auth0_client_settings()

        create_user_params = {
            "email": email.value,
            "email_verified": True,
            "connection": "email",
            "verify_email": False,
        }
        auth0_user = self._handle_rate_limit_error(Users(**client_settings).create, create_user_params)

        return auth0_user["user_id"]

    def delete_user(self, email: user_domain.Email) -> None:
        client_settings = self.client.get_auth0_client_settings()

        # ユーザーの存在確認
        auth0_users = UsersByEmail(**client_settings).search_users_by_email(email.value)

        if len(auth0_users) == 0:
            raise Exception("user not found")

        for user in auth0_users:
            self._handle_rate_limit_error(Users(**client_settings).delete, user["user_id"])

    def delete_users(self, emails: list[user_domain.Email]) -> None:
        client_settings = self.client.get_auth0_client_settings()

        delete_users = self.find_by_emails(emails)

        for user in delete_users:
            self._handle_rate_limit_error(Users(**client_settings).delete, user.id.root)

    def bulk_create_auth0_users(self, emails: list[user_domain.Email]) -> list[user_domain.IdpUser]:
        auth0_users = []
        for email in emails:
            id = self.create_user(email)
            auth0_users.append(user_domain.IdpUser.from_id_and_email(id=id, email=email.value))

        return auth0_users
