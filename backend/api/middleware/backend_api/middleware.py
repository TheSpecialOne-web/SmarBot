import ipaddress

from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from api.database import get_db_session_from_request
from api.domain.models import (
    tenant as tenant_domain,
)
from api.domain.models.user.external_user_id import ExternalUserId
from api.infrastructures.auth0.auth0 import Auth0Service
from api.infrastructures.postgres.user import UserRepository
from api.libs.api_log import log_api_access
from api.libs.ctx import ContextUser, set_user_to_request
from api.libs.error_handlers import ErrorHandlers
from api.libs.exceptions import BadRequest, Forbidden, NotFound, Unauthorized
from api.libs.ip_address import get_client_ip
from api.libs.logging import get_logger

logger = get_logger()
auth0_service = Auth0Service()

security = HTTPBearer()


class ValidateTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            if request.url.path == "/backend-api/userinfo":
                return await call_next(request)

            token = await security(request)
            if token is None:
                raise Unauthorized("認証情報がありません")

            external_user_id = auth0_service.validate_token(token.credentials)

            user = extract_role_and_policy_from_user(request, external_user_id)
            # userinfo のログはコントローラーで取っている
            log_api_access(request, logger=logger, user_id=user.id, tenant_id=user.tenant.id)
            set_user_to_request(request, user)

            return await call_next(request)
        except Exception as e:
            return ErrorHandlers().handle_error(request, e)


# 既存の関数はそのまま使用
def extract_role_and_policy_from_user(request: Request, external_user_id: ExternalUserId) -> ContextUser:
    tenant_id = request.headers.get("X-Tenant-Id")
    if not tenant_id:
        raise BadRequest("組織のIDが指定されていません。")
    try:
        tid = tenant_domain.Id(value=int(tenant_id))
    except Exception:
        raise BadRequest("組織のIDが不正です。")

    session = get_db_session_from_request(request)
    user_repo = UserRepository(session)
    user = None
    if external_user_id.is_email_connection():
        user = user_repo.get_user_info_by_external_id(external_user_id)
    elif external_user_id.is_entra_id():
        idp_user = auth0_service.find_by_id(external_user_id)
        user = user_repo.get_user_info_by_email(idp_user.email)
    if user is None:
        raise NotFound("ユーザーが見つかりませんでした")

    tenant = user.tenant
    tenant_name = tenant.name
    tenant_alias = tenant.alias
    roles = user.roles

    if tenant is None:
        raise BadRequest("tenant is not found")
    if tenant.id != tid:
        raise NotFound("指定されたテナントが見つかりませんでした")
    if tenant_name is None:
        raise BadRequest("tenant is not found")
    if tenant_alias is None:
        raise BadRequest("テナントのエイリアスが見つかりませんでした")
    if len(roles) == 0:
        raise BadRequest("役割が設定されていません")

    # IPアドレスのチェック
    allowed_ips = tenant.allowed_ips
    if len(allowed_ips.root) > 0:
        client_ip = get_client_ip(request)
        ip_addr = ipaddress.ip_address(client_ip)
        if ip_addr not in allowed_ips:
            raise Forbidden("クライアントIPが許可されていません")

    if tenant.status == tenant_domain.Status.SUSPENDED:
        raise Forbidden("テナントの利用期間が終了しています")

    return ContextUser(
        id=user.id,
        name=user.name,
        email=user.email,
        tenant=tenant,
        roles=roles,
        is_administrator=user.is_administrator,
    )
